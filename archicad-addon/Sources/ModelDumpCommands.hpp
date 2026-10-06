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


class GetAutoTextsV1Command : public CommandBase {
public:
    GetAutoTextsV1Command ();
    GS::String GetName () const override;
    GS::Optional<GS::UniString> GetInputParametersSchema () const override;
    GS::Optional<GS::UniString> GetRawResponseSchema () const override;
    GS::ObjectState Execute (const GS::ObjectState&, GS::ProcessControl&) const override;
};


class GetCurrent2DDocumentV1Command : public CommandBase {
public:
    GetCurrent2DDocumentV1Command ();
    GS::String GetName () const override;
    GS::Optional<GS::UniString> GetInputParametersSchema () const override;
    GS::Optional<GS::UniString> GetRawResponseSchema () const override;
    GS::ObjectState Execute (const GS::ObjectState&, GS::ProcessControl&) const override;
};
