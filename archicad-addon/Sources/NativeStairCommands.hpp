#pragma once
#include "ExtendedElementCommands.hpp"

class CreateExactStairsV1Command : public CreateStairsCommand {
public:
    CreateExactStairsV1Command ();
    GS::Optional<GS::UniString> GetInputParametersSchema () const override;
    GS::Optional<GS::ObjectState> SetTypeSpecificParameters (API_Element&, API_ElementMemo&, const Stories&, const GS::ObjectState&) const override;
};

#define APA_STAIR_COMMAND(CLASS) \
class CLASS : public CommandBase { \
public: CLASS (); GS::String GetName () const override; \
GS::Optional<GS::UniString> GetInputParametersSchema () const override; \
GS::Optional<GS::UniString> GetRawResponseSchema () const override; \
GS::ObjectState Execute (const GS::ObjectState&, GS::ProcessControl&) const override; };
APA_STAIR_COMMAND(GetNativeStairGeometryV1Command)
APA_STAIR_COMMAND(EvaluateNativeStairGeometryV1Command)
APA_STAIR_COMMAND(ModifyNativeStairGeometryV1Command)
#undef APA_STAIR_COMMAND
