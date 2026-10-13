#pragma once
#include "CommandBase.hpp"

// Source-only overlay until a separately approved APX deployment.
class GetNativeGridDefaultsV1Command : public CommandBase {
public:
    GetNativeGridDefaultsV1Command ();
    GS::String GetName () const override;
    GS::Optional<GS::UniString> GetInputParametersSchema () const override;
    GS::Optional<GS::UniString> GetRawResponseSchema () const override;
    GS::ObjectState Execute (const GS::ObjectState&, GS::ProcessControl&) const override;
};
