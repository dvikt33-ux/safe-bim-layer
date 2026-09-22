import json, sys, urllib.request, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from safe_bim_layer import TapirClient, SafeBIMLayer, SafeBIMError

MODEL_URL='http://127.0.0.1:8080/v1/chat/completions'
MODEL=r'C:\LocalAI\models\Qwen3.8-27B-UD-Q4_K_XL.gguf'
BRIDGE='http://127.0.0.1:19723'
PROJECT=r'C:\LocalAI\SafeBIM_v01_Integration.pln'
SCHEMA=str(Path(__file__).parent/'tapir-1.5.8.json')
OUT=Path(__file__).parent/'safe-bim-v01-integration-result.json'

def post(url,obj,timeout=120):
    req=urllib.request.Request(url,data=json.dumps(obj).encode(),headers={'Content-Type':'application/json'},method='POST')
    try:
        with urllib.request.urlopen(req,timeout=timeout) as r:return json.loads(r.read().decode())
    except Exception as e:return {'_transport_error':str(e)}

HIGH_SCHEMA={'type':'object','additionalProperties':False,'properties':{
 'contour':{'type':'array','minItems':4,'items':{'type':'object','additionalProperties':False,'properties':{'x':{'type':'number'},'y':{'type':'number'}},'required':['x','y']}},
 'wallHeight':{'type':'number','exclusiveMinimum':0},'wallThickness':{'type':'number','exclusiveMinimum':0},
 'slab':{'type':'object','additionalProperties':False,'properties':{'thickness':{'type':'number','exclusiveMinimum':0}},'required':['thickness']},
 'door':{'type':'object','additionalProperties':False,'properties':{'centerOffset':{'type':'number','minimum':0},'sillHeight':{'type':'number'},'width':{'type':'number','exclusiveMinimum':0},'height':{'type':'number','exclusiveMinimum':0}},'required':['centerOffset','width','height']},
 'windows':{'type':'array','minItems':2,'maxItems':2,'items':{'type':'object','additionalProperties':False,'properties':{'centerOffset':{'type':'number','minimum':0},'sillHeight':{'type':'number'},'width':{'type':'number','exclusiveMinimum':0},'height':{'type':'number','exclusiveMinimum':0}},'required':['centerOffset','width','height']}}},
 'required':['contour','wallHeight','wallThickness','slab','door','windows']}

def call_qwen():
    prompt='Return exactly one high-level create_room tool call and no prose. Do not use Tapir commands or low-level GUIDs. Create a 6x4 room with contour [[0,0],[6,0],[6,4],[0,4],[0,0]], wallHeight 3.0, wallThickness 0.20, slab thickness 0.20, one door at centerOffset 3.0 width 1.0 height 2.0, and two windows on the host wall at centerOffset 1.5 and 4.5, each width 1.0 height 1.0 sillHeight 1.0.'
    req={'model':MODEL,'messages':[{'role':'system','content':'You are a high-level BIM planner. Return exactly one tool call. Never emit Tapir_CreateWalls, Tapir_CreateSlabs, Tapir_CreateDoors, or Tapir_CreateWindows.'},{'role':'user','content':prompt}], 'tools':[{'type':'function','function':{'name':'create_room','parameters':HIGH_SCHEMA}}], 'tool_choice':'required','temperature':0,'max_tokens':420}
    # llama-server accepts string tool_choice; object-valued tool_choice is
    # rejected by the current runtime. Bound the integration probe. A model timeout must not leave a partially
    # started room transaction or cause retries that could duplicate writes.
    resp=post(MODEL_URL,req,65)
    try:
        call=resp['choices'][0]['message']['tool_calls'][0]
        args=json.loads(call['function']['arguments'])
        return {'request':req,'response':resp,'toolName':call['function']['name'],'args':args,'error':None}
    except Exception as e:
        return {'request':req,'response':resp,'toolName':None,'args':None,'error':str(e)}

def cleanup_copy(client):
    client.call('OpenProject',{'projectFilePath':PROJECT})
    allr=client.call('GetAllElements',{}); gs=[x['elementId']['guid'] for x in allr.get('result',{}).get('addOnCommandResponse',{}).get('elements',[])]
    if gs:
        rr=client.call('GetDetailsOfElements',{'elements':[{'elementId':{'guid':g}} for g in gs]}); ds=rr.get('result',{}).get('addOnCommandResponse',{}).get('detailsOfElements',[])
        walls=[g for g,d in zip(gs,ds) if d.get('type')=='Wall']
        if walls: client.call('DeleteElements',{'elements':[{'elementId':{'guid':g}} for g in walls]})
    return {'projectInfo':client.call('GetProjectInfo',{}),'remaining':client.call('GetAllElements',{})}

def main():
    c=TapirClient(BRIDGE,SCHEMA); layer=SafeBIMLayer(c)
    result={'version':'0.1','project':PROJECT,'safeBimLayer':'v0.1','preflight':cleanup_copy(c)}
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    q=call_qwen(); result['qwen']=q
    if q['error'] or q['toolName']!='create_room':
        result['status']='FAIL'; result['failureStage']='QWEN_HIGH_LEVEL_TOOL_CALL'; OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps({'status':result['status'],'error':q['error']},ensure_ascii=False)); return
    try:
        # Validate the high-level contract before any BIM write.
        c._validate_node(HIGH_SCHEMA,q['args'],'create_room')
        result['safeBimResult']=layer.create_room(q['args']['contour'],q['args']['wallHeight'],q['args']['wallThickness'],q['args']['slab'],q['args']['door'],q['args']['windows'])
        result['status']=result['safeBimResult']['status']
    except Exception as e:
        result['status']='FAIL'; result['failureStage']='SAFE_BIM_PREWRITE'; result['error']=repr(e)
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'status':result['status'],'failureStage':result.get('failureStage'),'safeBimStatus':result.get('safeBimResult',{}).get('status')},ensure_ascii=False))

if __name__=='__main__': main()
