// Included after the existing Tapir GDL serializers. Reuse them with bounded
// SDK-owned handles, without OpenParameters/global default changes or placement.
#include "NativeExtendedModules.hpp"
#include <algorithm>
#include <iterator>
static bool APABoundedStrings(GSHandle handle,UInt64 count){
 if(handle==nullptr||*handle==nullptr)return false;const auto n=BMGetHandleSize(handle)/sizeof(GS::uchar_t);const auto* data=reinterpret_cast<const GS::uchar_t*>(*handle);GSSize pos=0;
 for(UInt64 i=0;i<count;++i){while(pos<n&&data[pos]!=0)++pos;if(pos>=n)return false;++pos;}return true;
}
GS::ObjectState GetNativeLibraryPartDefaultsV1Command::Execute(const GS::ObjectState& p,GS::ProcessControl&) const {
 GS::Array<Int32> indices;p.Get("libraryPartIndices",indices);bool scripts=false;p.Get("includeParameterScripts",scripts);GS::ObjectState out("nativeModelWrites",0,"authority","LIBRARY_PART_STORED_DEFAULTS_NOT_PLACED_INSTANCE");const auto& rows=out.AddList<GS::ObjectState>("parts");if(scripts&&indices.GetSize()!=1){rows(CreateErrorResponse(APIERR_BADPARS,"Script query requires exactly one explicitly selected library part"));return out;}
 for(Int32 index:indices){double a=0,b=0;Int32 count=0;API_AddParType** parameters=nullptr;const GS::OnExit cleanup([&](){if(parameters)ACAPI_DisposeAddParHdl(&parameters);});const auto err=ACAPI_LibraryPart_GetParams(index,&a,&b,&count,&parameters);
 if(err!=NoError){rows(CreateErrorResponse(err,"Library part default parameters"));continue;}const auto allocated=parameters?BMGetHandleSize(reinterpret_cast<GSHandle>(parameters))/sizeof(API_AddParType):0;if(count<0||static_cast<GSSize>(count)>allocated||count>4096){rows(CreateErrorResponse(APIERR_BADPARS,"Parameter count exceeds allocated handle or bounded query"));continue;}
 GS::ObjectState row("libraryPartIndex",index,"defaultA",a,"defaultB",b,"parameterCount",count);const auto& list=row.AddList<GS::ObjectState>("parameters");
 for(Int32 i=0;i<count;++i){const auto& original=(*parameters)[i];API_AddParType param=original;
 if(std::find(std::begin(param.name),std::end(param.name),'\0')==std::end(param.name)||std::find(std::begin(param.uDescname),std::end(param.uDescname),0)==std::end(param.uDescname)){rows(CreateErrorResponse(APIERR_BADPARS,"Unterminated parameter identity"));return out;}
 GS::ObjectState entry("name",param.name,"displayName",GS::UniString(param.uDescname),"index",static_cast<Int32>(param.index),"type",ConvertAddParIDToString(param.typeID),"nativeTypeId",static_cast<Int32>(param.typeID),"typeModifier",static_cast<Int32>(param.typeMod),"dimension1",param.dim1,"dimension2",param.dim2,"flags",static_cast<Int32>(param.flags));
 bool supported=param.typeID!=APIParT_Dictionary&&param.typeID!=APIParT_Separator;bool bounds=true;const bool text=param.typeID==APIParT_CString||param.typeID==APIParT_Title;
 if(supported&&param.typeMod==API_ParArray){const auto second=std::max<Int32>(1,param.dim2);const UInt64 cells=param.dim1>0?static_cast<UInt64>(param.dim1)*static_cast<UInt64>(second):0;bounds=cells>0&&cells<=4096&&param.value.array!=nullptr;if(bounds){if(text)bounds=APABoundedStrings(param.value.array,cells);else bounds=cells<=BMGetHandleSize(param.value.array)/sizeof(double);}param.dim2=second;
 }else if(supported&&param.typeMod!=API_ParSimple)bounds=false;else if(supported&&text)bounds=std::find(std::begin(param.value.uStr),std::end(param.value.uStr),0)!=std::end(param.value.uStr);
 if(supported&&bounds){switch(param.typeID){
 case APIParT_Integer:case APIParT_PenCol:case APIParT_LineTyp:case APIParT_Mater:case APIParT_FillPat:case APIParT_BuildingMaterial:case APIParT_Profile:AddValueInteger(entry,param);break;
 case APIParT_ColRGB:case APIParT_Intens:case APIParT_Length:case APIParT_RealNum:case APIParT_Angle:AddValueDouble(entry,param);break;
 case APIParT_LightSw:AddValueOnOff(entry,param);break;case APIParT_Boolean:AddValueBool(entry,param);break;case APIParT_CString:case APIParT_Title:AddValueString(entry,param);break;
 default:supported=false;break;}}
 entry.Add("valueStatus",!supported?"UNSUPPORTED_NATIVE_PARAMETER_TYPE":(bounds?"SERIALIZED_REUSING_TAPIR":"OMITTED_ALLOCATION_OR_SIZE_BOUNDARY"));list(entry);
 }
 if(scripts){const auto& sections=row.AddList<GS::ObjectState>("parameterScripts");for(Int32 slot=0;slot<2;++slot){API_LibPartSection section={};section.sectType=slot==0?API_Sect1DScript:API_SectVLScript;GS::UniString text;const auto se=ACAPI_LibraryPart_GetSection(index,&section,nullptr,&text);GS::ObjectState item("section",slot==0?"MASTER":"PARAMETER","nativeError",static_cast<Int32>(se),"authority","PRIVATE_LIBRARY_SOURCE_NOT_EXECUTED_OR_INTERPRETED");if(se==NoError&&text.GetLength()<=65536){item.Add("status","READABLE");item.Add("text",text);}else item.Add("status",se==NoError?"OMITTED_SIZE_BOUNDARY":"NATIVE_UNAVAILABLE_OR_PROTECTED_NO_BYPASS");sections(item);}}
 rows(row);
 }return out;
}
