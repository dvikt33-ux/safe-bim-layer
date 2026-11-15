"""Open a visual check of an existing authored BIM candidate in a browser."""
from html import escape
import json

from apa_project_design import _review_design


STYLE = """
:root {
  font-family: Inter, Arial, sans-serif;
  color: #17272b;
  background: #eef1ef;
  line-height: 1.45;
}
body { max-width: 1220px; margin: 0 auto; padding: 36px 24px 64px; }
h1 { font-size: clamp(24px, 4vw, 40px); margin: 0 0 6px; }
h2 { font-size: 21px; margin: 26px 0 12px; }
h3 { font-size: 16px; margin: 0 0 6px; }
p { max-width: 80ch; margin: 8px 0; }
.muted { color: #526668; }
.plots {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(350px, 100%), 1fr));
  gap: 14px;
}
.plot, table { background: #fff; border: 1px solid #d9dfdc; border-radius: 10px; }
.plot { padding: 16px 16px 8px; }
canvas { width: 100%; height: auto; display: block; }
table { width: 100%; border-collapse: collapse; }
td, th { padding: 10px 12px; border-bottom: 1px solid #e4e9e5; text-align: left; vertical-align: top; }
td:first-child { width: 40%; }
th { color: #384e50; font-size: 13px; }
small { font-size: 12px; }
.status { font-weight: 600; color: #166858; }
.open { color: #9a480d; }
@media print {
  :root { background: #fff; }
  body { padding: 0; }
  .plot, table { break-inside: avoid; }
}
"""


def plot_data(brief, candidate, layout):
    from shapely import get_parts
    from shapely.geometry import LineString, Polygon

    operations = {step["id"]: (step["command"], next(iter(step["params"].values()))[0])
                  for step in candidate["graph"]["operations"]}
    names = {room["id"]: room["name"] for room in brief["rooms"]}
    stories = [dict(story, walls=[], openings=[], slabs=[], rooms=[]) for story in brief["stories"]]
    story_by_id = {story["id"]: story for story in stories}
    for room in layout["rooms"]:
        story_by_id[room["storyId"]]["rooms"].append(dict(name=names[room["roomId"]], **room["rectangle"]))
    for command, data in operations.values():
        if command in {"CreateWalls", "CreateSlabs"}:
            stories[data["floorIndex"]]["walls" if command == "CreateWalls" else "slabs"].append(data)
        if command in {"CreateDoors", "CreateWindows"}:
            host = operations[data["ownerWallId"]["guid"]["$createdGuid"]][1]
            a, b = host["begCoordinate"], host["endCoordinate"]
            length = ((b["x"] - a["x"]) ** 2 + (b["y"] - a["y"]) ** 2) ** 0.5
            offsets = [data["centerOffset"] + sign * data["width"] / 2 for sign in (-1, 1)]
            ends = [{axis: a[axis] + (b[axis] - a[axis]) * offset / length for axis in ("x", "y")}
                    for offset in offsets]
            stories[host["floorIndex"]]["openings"].append(dict(ends=ends, thickness=host["thickness"],
                                                               window=command == "CreateWindows"))
    bounds = candidate["authoredOutline"]
    stairs = []
    for stair in candidate.get("stairConnections", []):
        flight = operations[stair["stairOperationId"]][1]
        xmin, _, xmax, _ = stair["flightBounds"]
        x = (xmin + xmax) / 2
        cut = LineString([(x, bounds["yMin"] - 1), (x, bounds["yMax"] + 1)])
        cuts = []
        for sid in (stair["lowerSlabOperationId"], stair["upperSlabOperationId"]):
            slab = operations[sid][1]
            outline = [(p["x"], p["y"]) for p in slab["polygonCoordinates"]]
            holes = [[(p["x"], p["y"]) for p in h["polygonCoordinates"]] for h in slab.get("holes", [])]
            for part in get_parts(Polygon(outline, holes).intersection(cut)):
                if part.geom_type == "LineString" and not part.is_empty:
                    cuts.append(dict(yMin=part.bounds[1], yMax=part.bounds[3], top=slab["level"], depth=slab["thickness"]))
        stairs.append(dict(stair, flight=flight, slabs=cuts))
    return dict(bounds=bounds, stories=stories, stairs=stairs)


SCRIPT = """
const data = JSON.parse(document.getElementById('plan-data').textContent);
const {xMin,xMax,yMin,yMax}=data.bounds;
const plots=document.getElementById('plots');
function graphic(title, sub, height){
  const article=document.createElement('article'); article.className='plot';
  const h=document.createElement('h3'); h.textContent=title;
  const info=document.createElement('small'); info.className='muted'; info.textContent=sub;
  const canvas=document.createElement('canvas'); canvas.width=720; canvas.height=height;
  canvas.setAttribute('aria-label',title); article.append(h,info,canvas); plots.append(article);
  return canvas.getContext('2d');
}
function line(ctx,a,b,color,width,dash=[]){
  ctx.beginPath(); ctx.setLineDash(dash); ctx.strokeStyle=color; ctx.lineWidth=width;
  ctx.moveTo(...a); ctx.lineTo(...b); ctx.stroke(); ctx.setLineDash([]);
}
function shape(ctx,points,fill,stroke,dash=[]){
  ctx.beginPath(); ctx.moveTo(...points[0]); points.slice(1).forEach(p=>ctx.lineTo(...p)); ctx.closePath();
  if(fill){ctx.fillStyle=fill;ctx.fill();} ctx.setLineDash(dash);ctx.strokeStyle=stroke;ctx.lineWidth=1.4;
  ctx.stroke();ctx.setLineDash([]);
}
function label(ctx,text,x,y,max){ctx.fillStyle='#263b3b';ctx.textAlign='center';ctx.font='18px Inter, Arial';ctx.fillText(text,x,y,max);}
for(const story of data.stories){
  const ctx=graphic(story.label,`Отметка ${story.level.toFixed(3)} м`,550);
  const k=Math.min(620/(xMax-xMin),450/(yMax-yMin));
  const x0=(720-k*(xMax-xMin))/2,y0=41;
  const point=(x,y)=>[x0+(x-xMin)*k,y0+(yMax-y)*k];
  const xy=p=>point(p.x,p.y);
  const rect=(a,b,c,d)=>[point(a,b),point(c,b),point(c,d),point(a,d)];
  for(const slab of story.slabs){shape(ctx,slab.polygonCoordinates.map(xy),'#eef2ef','#b4c2bc');}
  for(const room of story.rooms){
    shape(ctx,rect(room.xMin,room.yMin,room.xMax,room.yMax),'#e0eeee','#adc4bf');
    const [x,y]=point((room.xMin+room.xMax)/2,(room.yMin+room.yMax)/2);
    label(ctx,room.name,x,y,(room.xMax-room.xMin)*k-10);
  }
  for(const slab of story.slabs)for(const hole of (slab.holes||[])){
    shape(ctx,hole.polygonCoordinates.map(xy),'#ffffff','#a95d22',[8,5]);
  }
  for(const stair of data.stairs.filter(s=>s.lowerStoryId===story.id||s.upperStoryId===story.id)){
    shape(ctx,rect(...stair.flightBounds),story.id===stair.lowerStoryId?'#f2dbb7':null,'#a95d22',[8,4]);
    if(story.id===stair.lowerStoryId){
      const [a,b,c]=stair.flightBounds;
      for(let i=1;i<stair.flight.stepNum;i++){
        const y=b+i*stair.flight.treadDepth;line(ctx,point(a,y),point(c,y),'#b07133',1);
      }
    }
  }
  for(const wall of story.walls)line(ctx,xy(wall.begCoordinate),xy(wall.endCoordinate),'#27363b',wall.thickness*k);
  for(const op of story.openings){
    const [a,b]=op.ends.map(xy);line(ctx,a,b,'#fff',op.thickness*k+1);
    line(ctx,a,b,op.window?'#486d8d':'#328079',3);
  }
  const length=Math.min(2,(xMax-xMin)/3);line(ctx,[x0,518],[x0+length*k,518],'#27363b',3);
  label(ctx,`${length.toFixed(1)} м`,x0+length*k/2,542,100);
}
for(const stair of data.stairs){
  const ctx=graphic('Разрез по лестнице','Плиты и марш из эскиза',360);
  const f=stair.flight, z=f.zCoordinate;
  const k=Math.min(600/(yMax-yMin),250/(f.totalHeight+.45));
  const point=(y,h)=>[60+(y-yMin)*k,300-(h-z)*k];
  for(const slab of stair.slabs)shape(ctx,[point(slab.yMin,slab.top),point(slab.yMax,slab.top),
    point(slab.yMax,slab.top-slab.depth),point(slab.yMin,slab.top-slab.depth)],'#849b98','#476565');
  let y=stair.flightBounds[1], h=z;
  for(let i=0;i<f.stepNum;i++){
    line(ctx,point(y,h),point(y,h+f.riserHeight),'#a85a22',2);h+=f.riserHeight;
    line(ctx,point(y,h),point(y+f.treadDepth,h),'#a85a22',2);y+=f.treadDepth;
  }
  label(ctx,`${f.stepNum} подъёмов × ${f.riserHeight.toFixed(2)} м`,360,343,600);
}
"""


def finding_detail(row):
    measurement = row.get("measurement", {})
    if "valueM2" in measurement and measurement["valueM2"] is not None:
        return f'{measurement["valueM2"]:.2f} м²'
    if "requiredWidthM" in measurement:
        count = len(row["route"])
        return f'Проход при ширине {measurement["requiredWidthM"]:.2f} м, переходов {count}' if count else "Маршрут не найден"
    if row.get("criterion", {}).get("kind") == "STAIR_LINK" and measurement:
        labels = {"minimumWidthM": "ширина", "minimumGoingM": "проступь",
                  "maximumRiserM": "подъём", "minimumLandingDepthM": "площадки"}
        return ", ".join(f'{labels[key]} {fact["measuredM"]:.2f} м' for key, fact in measurement.items())
    return row["reason"].replace("_", " ")


def write_design_review(intent, variant_id, output):
    report, sources = _review_design(intent)
    variant = next((row for row in report["variants"] if row["id"] == variant_id), None)
    if variant is None or "candidate" not in variant:
        raise ValueError("Для эскиза нужен вариант с проверяемой геометрией")
    candidate = variant["candidate"]
    brief = report["brief"]
    data = json.dumps(plot_data(brief, candidate, sources[variant_id]["layout"]),
                      ensure_ascii=False, allow_nan=False).replace("<", "\\u003c")
    statuses = {"DESIGN_CHECKED": "Подтверждено в эскизе", "PARTIAL": "Ожидает сверки", "CONFLICT": "Расхождение",
                "MISSING": "Отсутствует", "UNVERIFIED": "Недостаточно данных"}
    rows = []
    for row in candidate["requirements"]:
        css = "status" if row["status"] == "DESIGN_CHECKED" else "status open"
        detail = escape(finding_detail(row))
        rows.append(f'<tr><td>{escape(row["text"])}<br><small>{escape(row["sourceRef"])}</small></td>'
                    f'<td class="{css}">{statuses.get(row["status"], row["status"])}</td><td>{detail}</td></tr>')
    html = f'''<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>Проверка планировки · APA</title><style>{STYLE}</style>
<body><h1>Проверка планировки</h1><p class="muted">{escape(brief["projectId"])} · {escape(variant_id)}</p>
<div class="plots" id="plots"></div>
<p class="muted">Эскиз из авторской геометрии. Цветные отрезки показывают двери и окна.
Высота прохода, ограждения и нормативная применимость требуют отдельных данных.</p>
<h2>Требования проекта</h2><table><thead><tr><th>Требование</th><th>Результат</th><th>Измерение</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table>
<script type="application/json" id="plan-data">{data}</script><script>{SCRIPT}</script></body></html>'''
    with output.open("x", encoding="utf-8") as handle:
        handle.write(html)
    return dict(status="DESIGN_REVIEW_WRITTEN", variant=variant_id, output=str(output),
                inputHash=report["inputHash"], graphHash=candidate["sourcePlanHash"],
                requiredOpenIds=candidate["requiredOpenIds"], nativeWriteCalls=0)
