#pragma once
#include "CommandBase.hpp"
#define APA_EXTENDED_COMMAND(name) class name##Command : public CommandBase { public: name##Command(); GS::String GetName() const override; GS::Optional<GS::UniString> GetInputParametersSchema() const override; GS::Optional<GS::UniString> GetRawResponseSchema() const override; GS::ObjectState Execute(const GS::ObjectState&,GS::ProcessControl&) const override; };
APA_EXTENDED_COMMAND(GetNativeEnvelopeMemoV1)
APA_EXTENDED_COMMAND(GetNativeDrawingAssociationsV1)
APA_EXTENDED_COMMAND(GetNativeElementHotspotsV1)
APA_EXTENDED_COMMAND(GetNativeElementQuantitiesV1)
APA_EXTENDED_COMMAND(GetNativeComponentBindingsV1)
APA_EXTENDED_COMMAND(GetNativeOpeningConnectionsV1)
APA_EXTENDED_COMMAND(GetNativeQuantityPreflightV1)
APA_EXTENDED_COMMAND(GetNativeLibraryPartDefaultsV1)
APA_EXTENDED_COMMAND(GetNativeNavigatorBindingsV1)
APA_EXTENDED_COMMAND(CreateNativeAssemblyV1)
#undef APA_EXTENDED_COMMAND
