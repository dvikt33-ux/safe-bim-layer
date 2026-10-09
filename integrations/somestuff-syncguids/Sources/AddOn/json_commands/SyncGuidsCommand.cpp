#include <chrono>
#include <string>
#include <unordered_set>

#include "ACAPinc.h"
#include "json_commands/SyncGuidsCommand.hpp"

#include "Propertycache.hpp"
#include "Sync.hpp"
#include "dialogs/SyncSettings.hpp"

#if defined(ServerMainVers_2500)

namespace {

// Validate the text BEFORE invoking APIGuidFromString. Braces are deliberately
// rejected: the JSON contract uses the 36-character canonical UUID form.
bool IsCanonicalGuidText (const std::string& value)
{
    if (value.size () != 36)
        return false;

    for (std::size_t i = 0; i < value.size (); ++i) {
        const bool dash = i == 8 || i == 13 || i == 18 || i == 23;
        const char ch = value[i];
        if (dash) {
            if (ch != '-')
                return false;
        } else {
            const bool hex = (ch >= '0' && ch <= '9') ||
                             (ch >= 'a' && ch <= 'f') ||
                             (ch >= 'A' && ch <= 'F');
            if (!hex)
                return false;
        }
    }

    return true;
}

} // namespace

SyncGuidsCommand::SyncGuidsCommand () : CommandBase (CommonSchema::NotUsed) {}

GS::String SyncGuidsCommand::GetName () const
{
    return "SyncGuids";
}

GS::Optional<GS::UniString> SyncGuidsCommand::GetInputParametersSchema () const
{
    return R"({
        "type": "object",
        "properties": {
            "elementGuids": {
                "type": "array",
                "minItems": 1,
                "maxItems": 5000,
                "uniqueItems": true,
                "items": {
                    "type": "string",
                    "pattern": "^[0-9a-fA-F]{8}(-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}$"
                }
            }
        },
        "required": ["elementGuids"],
        "additionalProperties": false
    })";
}

GS::Optional<GS::UniString> SyncGuidsCommand::GetResponseSchema () const
{
    return GS::NoValue;
}

GS::ObjectState SyncGuidsCommand::Execute (const GS::ObjectState& parameters,
                                           GS::ProcessControl& /*processControl*/) const
{
    // Read and validate the entire request before the first possible BIM write.
    GS::Array<GS::UniString> requested;
    if (!parameters.Get ("elementGuids", requested) ||
        requested.IsEmpty () || requested.GetSize () > 5000) {
        return CreateErrorResponse (APIERR_BADPARS, "Expected 1..5000 elementGuids");
    }

    SyncSettings settings;
    LoadSyncSettingsFromPreferences (settings, true);
    if (settings.GetSyncMon ()) {
        // APA controls synchronization explicitly. With monitoring ON,
        // measurements conflate observer-triggered work and this command.
        return CreateErrorResponse (APIERR_BADPARS, "Disable SomeStuff tracking before SyncGuids");
    }

    GS::Array<API_Guid> guids;
    std::unordered_set<std::string> seen;

    for (const GS::UniString& item : requested) {
        const std::string text (item.ToCStr ().Get ());
        if (!IsCanonicalGuidText (text))
            return CreateErrorResponse (APIERR_BADPARS, "Invalid GUID format");

        const API_Guid guid = APIGuidFromString (text.c_str ());
        if (guid == APINULLGuid)
            return CreateErrorResponse (APIERR_BADPARS, "Null GUID is not allowed");

        const std::string canonical (APIGuidToString (guid).ToCStr ().Get ());
        if (!seen.insert (canonical).second)
            return CreateErrorResponse (APIERR_BADPARS, "Duplicate GUID");

        API_Elem_Head head = {};
        head.guid = guid;
        if (ACAPI_Element_GetHeader (&head) != NoError) {
            // Existence alone does not establish edit permission; the caller
            // must verify actual property values after the operation.
            return CreateErrorResponse (APIERR_BADPARS, "Element not found or header inaccessible");
        }

        guids.Push (guid);
    }

    const auto started = std::chrono::steady_clock::now ();
    PROPERTYCACHE ().Update ();

    const auto engineStart = std::chrono::steady_clock::now ();
    GS::Array<API_Guid> secondPass = SyncArray (settings, guids);
    const GS::UInt32 secondPassCandidates = static_cast<GS::UInt32> (secondPass.GetSize ());

    // Mirrors SyncSelected: one extra pass for recursively affected elements.
    if (!secondPass.IsEmpty ())
        SyncArray (settings, secondPass);

    const auto finished = std::chrono::steady_clock::now ();
    const double seconds = std::chrono::duration<double> (finished - started).count ();
    const double engineSeconds = std::chrono::duration<double> (finished - engineStart).count ();

    GS::ObjectState response;
    response.Add ("status", "returned_unverified");
    response.Add ("requestedCount", static_cast<GS::Int32> (guids.GetSize ()));
    response.Add ("secondPassCandidateCount", static_cast<GS::Int32> (secondPassCandidates));
    response.Add ("elapsedSeconds", seconds);
    response.Add ("engineSeconds", engineSeconds);
    response.Add ("trackingEnabled", false);
    response.Add ("requiresReadback", true);

    // WARNING: SyncArray returns a re-sync candidate array, not a success
    // report. It may return early on user cancellation, and its internal
    // ACAPI_CallUndoableCommand result is not propagated. Only caller-side
    // GUID/property readback can confirm correctness for a known test rule.
    return response;
}

#endif // defined(ServerMainVers_2500)
