#pragma once

#if defined(ServerMainVers_2500)

#include "json_commands/CommandBase.hpp"

// Experimental GUID-scoped JSON endpoint for Archicad 25-29.
// This command is NOT a drop-in replacement for SyncAll:
// its result never certifies that every property was written.
class SyncGuidsCommand final : public CommandBase {
public:
    SyncGuidsCommand ();

    GS::String GetName () const override;
    GS::Optional<GS::UniString> GetInputParametersSchema () const override;
    GS::Optional<GS::UniString> GetResponseSchema () const override;

    GS::ObjectState Execute (const GS::ObjectState& parameters,
                             GS::ProcessControl& processControl) const override;
};

#endif // defined(ServerMainVers_2500)
