#pragma once
#include "APIEnvir.h"
#include "ACAPinc.h"
#include "DGModule.hpp"
#include "DGBrowser.hpp"

constexpr short SafeBIMPaletteResId = 32610;
constexpr short SafeBIMMenuResId = 32610;

class SafeBIMPalette final : public DG::Palette, public DG::PanelObserver {
private:
    static GS::Ref<SafeBIMPalette> instance;
    static const GS::Guid paletteGuid;
    DG::Browser browser;
    SafeBIMPalette();
    void SetMenuChecked(bool checked);
    void PanelResized(const DG::PanelResizeEvent& event) override;
    void PanelCloseRequested(const DG::PanelCloseRequestEvent&, bool* accepted) override;
    static GSErrCode PaletteControl(Int32, API_PaletteMessageID, GS::IntPtr);
public:
    ~SafeBIMPalette() override;
    static bool HasInstance();
    static void CreateInstance();
    static SafeBIMPalette& GetInstance();
    static void DestroyInstance();
    static GSErrCode RegisterPaletteControl();
    void Show();
    void Hide();
};

