#pragma once
#include "CommandBase.hpp"

class GetAPARuntimeInfoV1Command : public CommandBase {
public:
    GetAPARuntimeInfoV1Command ();
    GS::String GetName () const override;
    GS::Optional<GS::UniString> GetInputParametersSchema () const override;
    GS::Optional<GS::UniString> GetRawResponseSchema () const override;
    GS::ObjectState Execute (const GS::ObjectState&, GS::ProcessControl&) const override;
};

// Source-only overlay until a separately approved APX deployment.
class GetNativeGridDefaultsV1Command : public CommandBase {
public:
    GetNativeGridDefaultsV1Command ();
    GS::String GetName () const override;
    GS::Optional<GS::UniString> GetInputParametersSchema () const override;
    GS::Optional<GS::UniString> GetRawResponseSchema () const override;
    GS::ObjectState Execute (const GS::ObjectState&, GS::ProcessControl&) const override;
};

class GetNativeGridElementsV1Command : public CommandBase {
public:
    GetNativeGridElementsV1Command ();
    GS::String GetName () const override;
    GS::Optional<GS::UniString> GetInputParametersSchema () const override;
    GS::Optional<GS::UniString> GetRawResponseSchema () const override;
    GS::ObjectState Execute (const GS::ObjectState&, GS::ProcessControl&) const override;
};
class CreateNativeGridElementsV1Command : public CommandBase {
public:
    CreateNativeGridElementsV1Command ();
    GS::String GetName () const override;
    GS::Optional<GS::UniString> GetInputParametersSchema () const override;
    GS::Optional<GS::UniString> GetRawResponseSchema () const override;
    GS::ObjectState Execute (const GS::ObjectState&, GS::ProcessControl&) const override;
};
class ModifyNativeGridElementsV1Command : public CommandBase {
public:
    ModifyNativeGridElementsV1Command ();
    GS::String GetName () const override;
    GS::Optional<GS::UniString> GetInputParametersSchema () const override;
    GS::Optional<GS::UniString> GetRawResponseSchema () const override;
    GS::ObjectState Execute (const GS::ObjectState&, GS::ProcessControl&) const override;
};
