#include "APIEnvir.h"
#include "ACAPinc.h"
#include "SafeBIMPalette.hpp"

static void TogglePalette()
{
    if (SafeBIMPalette::HasInstance() && SafeBIMPalette::GetInstance().IsVisible())
        SafeBIMPalette::GetInstance().Hide();
    else {
        if (!SafeBIMPalette::HasInstance()) SafeBIMPalette::CreateInstance();
        SafeBIMPalette::GetInstance().Show();
    }
}

static GSErrCode MenuHandler(const API_MenuParams* params)
{
    if (params->menuItemRef.menuResID == SafeBIMMenuResId &&
        params->menuItemRef.itemIndex == 1) TogglePalette();
    return NoError;
}

API_AddonType CheckEnvironment(API_EnvirParams* env)
{
    RSGetIndString(&env->addOnInfo.name, 32000, 1, ACAPI_GetOwnResModule());
    RSGetIndString(&env->addOnInfo.description, 32000, 2, ACAPI_GetOwnResModule());
    return APIAddon_Preload;
}

GSErrCode RegisterInterface()
{
    return ACAPI_MenuItem_RegisterMenu(SafeBIMMenuResId, 0, MenuCode_Palettes, MenuFlag_Default);
}

GSErrCode Initialize()
{
    GSErrCode error = ACAPI_MenuItem_InstallMenuHandler(SafeBIMMenuResId, MenuHandler);
    if (error != NoError) return error;
    return SafeBIMPalette::RegisterPaletteControl();
}

GSErrCode FreeData()
{
    SafeBIMPalette::DestroyInstance();
    return NoError;
}

