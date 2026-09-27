#include "SafeBIMPalette.hpp"

GS::Ref<SafeBIMPalette> SafeBIMPalette::instance;
const GS::Guid SafeBIMPalette::paletteGuid("{FA2DBA6D-6589-4E1B-AB61-730A7997C907}");

static GS::UniString LoadHtml()
{
    GS::UniString data;
    GSHandle handle = RSLoadResource('DATA', ACAPI_GetOwnResModule(), 100);
    if (handle != nullptr) {
        data.Append(*handle, BMhGetSize(handle));
        BMhKill(&handle);
    }
    return data;
}

SafeBIMPalette::SafeBIMPalette() :
    DG::Palette(ACAPI_GetOwnResModule(), SafeBIMPaletteResId,
                ACAPI_GetOwnResModule(), paletteGuid),
    browser(GetReference(), 1)
{
    Attach(*this);
    BeginEventProcessing();
    browser.LoadHTML(LoadHtml());
}

SafeBIMPalette::~SafeBIMPalette() { EndEventProcessing(); }
bool SafeBIMPalette::HasInstance() { return instance != nullptr; }
void SafeBIMPalette::CreateInstance() { if (!HasInstance()) instance = new SafeBIMPalette(); }
SafeBIMPalette& SafeBIMPalette::GetInstance() { return *instance; }
void SafeBIMPalette::DestroyInstance() { instance = nullptr; }

void SafeBIMPalette::SetMenuChecked(bool checked)
{
    API_MenuItemRef ref{}; ref.menuResID = SafeBIMMenuResId; ref.itemIndex = 1;
    GSFlags flags{};
    ACAPI_MenuItem_GetMenuItemFlags(&ref, &flags);
    flags = checked ? (flags | API_MenuItemChecked) : (flags & ~API_MenuItemChecked);
    ACAPI_MenuItem_SetMenuItemFlags(&ref, &flags);
}

void SafeBIMPalette::Show() { DG::Palette::Show(); SetMenuChecked(true); }
void SafeBIMPalette::Hide() { DG::Palette::Hide(); SetMenuChecked(false); }
void SafeBIMPalette::PanelResized(const DG::PanelResizeEvent& event)
{
    BeginMoveResizeItems();
    browser.Resize(event.GetHorizontalChange(), event.GetVerticalChange());
    EndMoveResizeItems();
}
void SafeBIMPalette::PanelCloseRequested(const DG::PanelCloseRequestEvent&, bool* accepted)
{
    Hide(); *accepted = true;
}

GSErrCode SafeBIMPalette::PaletteControl(Int32, API_PaletteMessageID message, GS::IntPtr param)
{
    switch (message) {
        case APIPalMsg_OpenPalette: if (!HasInstance()) CreateInstance(); GetInstance().Show(); break;
        case APIPalMsg_ClosePalette: DestroyInstance(); break;
        case APIPalMsg_HidePalette_Begin: if (HasInstance()) GetInstance().Hide(); break;
        case APIPalMsg_IsPaletteVisible:
            *reinterpret_cast<bool*>(param) = HasInstance() && GetInstance().IsVisible(); break;
        default: break;
    }
    return NoError;
}

GSErrCode SafeBIMPalette::RegisterPaletteControl()
{
    return ACAPI_RegisterModelessWindow(SafeBIMPaletteResId, PaletteControl,
        API_PalEnabled_FloorPlan | API_PalEnabled_Section | API_PalEnabled_3D,
        GSGuid2APIGuid(paletteGuid));
}

