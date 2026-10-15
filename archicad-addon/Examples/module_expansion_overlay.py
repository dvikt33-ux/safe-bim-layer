"""Add thin SDK groups to the existing Tapir registration; no second add-on."""
from pathlib import Path
def apply(addon):
    addon=Path(addon);path=addon/'Sources/AddOnMain.cpp';text=path.read_text(encoding='utf8')
    if '#include "NativeModuleCommands.hpp"' not in text:text=text.replace('#include "ElementCommands.hpp"','#include "ElementCommands.hpp"\n#include "NativeModuleCommands.hpp"',1)
    if '#include "NativeExtendedModules.hpp"' not in text:text=text.replace('#include "NativeModuleCommands.hpp"','#include "NativeModuleCommands.hpp"\n#include "NativeExtendedModules.hpp"',1)
    for name in ['GetNativeElementDefaultsV1','GetNativePolygonMemoV1','GetNativeWorkingUnitsV1','GetNativeGroupRootsV1','GetNativeLibraryPartOriginV1','GetNativeEnvelopeMemoV1','GetNativeDrawingAssociationsV1','GetNativeElementHotspotsV1','GetNativeElementQuantitiesV1','GetNativeComponentBindingsV1','GetNativeOpeningConnectionsV1','GetNativeQuantityPreflightV1']:
        line=f'        err |= RegisterCommand<{name}Command> (elementCommands, "apa-sdk-module", "SDK29 typed read adapter; source/build only until runtime registration.");'
        if line not in text:
            anchor='        AddCommandGroup (elementCommands);'
            if text.count(anchor)!=1:raise ValueError('ELEMENT_REGISTRATION_ANCHOR_CHANGED')
            text=text.replace(anchor,line+'\n'+anchor,1)
    # DevKit namespace is deliberately independent of Tapir GetNamespace final.
    line='    err |= ACAPI_AddOnAddOnCommunication_InstallAddOnCommandHandler (GS::NewOwned<APAProtectionInfoCommand> ());'
    if line not in text:
        anchor='        AddCommandGroup (elementCommands);';text=text.replace(anchor,anchor+'\n'+line,1)
    path.write_text(text,encoding='utf8')
