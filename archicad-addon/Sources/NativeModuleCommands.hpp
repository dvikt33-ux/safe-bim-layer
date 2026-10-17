#pragma once
#include "CommandBase.hpp"

#define APA_MODULE_COMMAND(name) class name##Command : public CommandBase { public: name##Command(); GS::String GetName() const override; GS::Optional<GS::UniString> GetInputParametersSchema() const override; GS::Optional<GS::UniString> GetRawResponseSchema() const override; GS::ObjectState Execute(const GS::ObjectState&,GS::ProcessControl&) const override; };
APA_MODULE_COMMAND(GetNativeElementDefaultsV1)
APA_MODULE_COMMAND(GetNativePolygonMemoV1)
APA_MODULE_COMMAND(GetNativeWorkingUnitsV1)
APA_MODULE_COMMAND(GetNativeGroupRootsV1)
APA_MODULE_COMMAND(CreateNativeGroupV1)
APA_MODULE_COMMAND(CloneNativeGroupV1)
APA_MODULE_COMMAND(GetNativeLibraryPartOriginV1)
#undef APA_MODULE_COMMAND

// Preserve the original DevKit namespace/name; no duplicate column factory.
class APAProtectionInfoCommand : public API_AddOnCommand {
public:
 GS::String GetName() const override { return "ProtectionInfoCommand"; }
 GS::String GetNamespace() const override { return "AddOnCommandTest"; }
 GS::Optional<GS::UniString> GetSchemaDefinitions() const override { return GS::NoValue; }
 GS::Optional<GS::UniString> GetInputParametersSchema() const override { return R"({"type":"object","maxProperties":0})"; }
 GS::Optional<GS::UniString> GetResponseSchema() const override;
 API_AddOnCommandExecutionPolicy GetExecutionPolicy() const override { return API_AddOnCommandExecutionPolicy::InstantExecutionOnParallelThread; }
 bool IsProcessWindowVisible() const override { return false; }
 void OnResponseValidationFailed(const GS::ObjectState&) const override {}
 GS::ObjectState Execute(const GS::ObjectState&,GS::ProcessControl&) const override;
};
