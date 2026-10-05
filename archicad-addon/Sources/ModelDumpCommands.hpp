#pragma once
#include "CommandBase.hpp"

class GetModelDumpV1Command : public CommandBase {
public:
    GetModelDumpV1Command ();
    GS::String GetName () const override;
    GS::Optional<GS::UniString> GetInputParametersSchema () const override;
    GS::Optional<GS::UniString> GetRawResponseSchema () const override;
    GS::ObjectState Execute (const GS::ObjectState&, GS::ProcessControl&) const override;
};
