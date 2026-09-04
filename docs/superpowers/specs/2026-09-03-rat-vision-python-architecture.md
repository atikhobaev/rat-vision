# RAT VISION — Python Architecture Revision

Date: 2026-09-03
Status: Approved
Companion product spec: `2026-09-03-rat-vision-design.md`
UI authority: `2026-09-03-rat-vision-ui-blueprint.md`

## 1. Decision

RAT VISION v1 will be implemented in **Python 3.13 x64** instead of .NET/WPF.

The approved product behavior and UI blueprint do not change. The stack changes so that the application UI, profile logic, persistence, theme system, process matching, diagnostics, and most platform behavior can be developed and tested directly in the current chat environment.

Target stack:

- Python 3.13 x64;
- Tkinter/ttk from the Python standard library for the windowing/event-loop foundation;
- custom Tkinter `Canvas`-based RAT VISION controls for the approved TerraGroup-inspired visual language;
- Pillow for embedded PNG/3D-emoji assets and image scaling;
- `psutil` for friendly running-process discovery where it improves reliability;
- `ctypes` for Windows APIs (`user32`, `gdi32`, `shell32`, `kernel32`) and NVIDIA NVAPI loading;
- standard-library `json`, `dataclasses`, `pathlib`, `logging`, and `threading` for core application services;
- pytest for automated tests.

No Qt, Electron, browser runtime, .NET runtime, or external UI framework is required by the application.

## 2. Why This Stack

The UI and core logic can run under Linux in a virtual display, which allows automated tests and real screenshot-based review in this environment. Windows-only operations are isolated behind adapters and replaced by fakes during Linux development.

This keeps the Windows-specific surface deliberately small:

- foreground-window hook;
- monitor enumeration and display metadata;
- gamma-ramp read/apply/restore;
- NVIDIA Digital Vibrance control;
- Windows tray icon/menu;
- launch-at-login registration;
- final Windows packaging and hardware verification.

The user should not perceive a cross-platform toolkit. RAT VISION remains a Windows product; Linux support exists only as an engineering/test mode.

## 3. Application Boundaries

Use focused Python packages rather than a single large GUI script.

```text
ratvision/
  app.py
  domain/
    models.py
    defaults.py
    profile_service.py
    activation_coordinator.py
  persistence/
    settings_store.py
    migration.py
  platform/
    base.py
    simulation.py
    windows/
      foreground.py
      displays.py
      gamma.py
      nvapi.py
      tray.py
      startup.py
      processes.py
  ui/
    main_window.py
    profile_workspace.py
    sidebar.py
    settings_view.py
    add_game_dialog.py
    controls/
      button.py
      toggle.py
      slider.py
      checkbox.py
      card.py
      led.py
      modal.py
      toast.py
    theme.py
    assets.py
  diagnostics/
    collector.py
  updates/
    service.py
```

Tests mirror these packages under `tests/`.

## 4. Platform Interfaces

`ratvision.platform.base` defines Python `Protocol` interfaces so policy code never imports Win32 APIs directly.

### ForegroundWindowProvider

- exposes the current foreground process identity;
- starts/stops observation;
- emits process changes through a callback/event abstraction;
- callbacks are marshalled onto the Tk UI thread before they mutate UI state.

### DisplayProvider

Returns stable `DisplayInfo` records containing at minimum:

- device ID such as `\\.\DISPLAY1`;
- friendly display name when available;
- bounds/resolution;
- refresh rate when available;
- primary flag;
- online/offline state.

### ColorBackend

Supports per-display operations:

- capture desktop baseline;
- apply `VisualParameters`;
- restore one display;
- restore all touched displays;
- report capability details and nonfatal failures.

Gamma/brightness/contrast and NVIDIA Digital Vibrance remain separate internal mechanisms but are coordinated behind this boundary.

### TrayBackend

- creates/removes tray icon;
- switches between approved OFF and ON/waiting icon states;
- exposes Open, global toggle, Settings, Buy me a coffee, and Exit actions;
- does not own profile policy.

### StartupBackend

Reads/writes RAT VISION launch-at-login state on Windows. The simulation implementation keeps this state in memory for tests.

## 5. Foreground Hook

On Windows use `SetWinEventHook(EVENT_SYSTEM_FOREGROUND, ...)` through `ctypes.WinDLL("user32", use_last_error=True)` and a retained `ctypes.WINFUNCTYPE` callback.

The callback object must be held strongly for the lifetime of the native hook; otherwise Python garbage collection could invalidate a callback still referenced by Windows.

The native callback does the minimum work required to resolve/process the event and posts the result to application state. It must not mutate Tk widgets directly from the native callback thread.

Linux/simulation mode uses an injectable fake foreground provider so focus transitions can be exercised deterministically in tests.

## 6. Multi-Monitor Gamma Control

Use `CreateDCW`/`DeleteDC`, `GetDeviceGammaRamp`, and `SetDeviceGammaRamp` from `gdi32` for each selected Windows display device.

Before RAT VISION changes a display for the first time in a session, capture that display's original 256-entry RGB gamma ramp. Store independent baselines keyed by display ID.

When a profile stops applying, global XRAT is disabled, a selected display is removed from the active profile, or the application exits, restore each touched display from its own captured baseline.

The LUT calculation preserves the upstream brightness/contrast/gamma behavior and is implemented as pure Python so it is fully unit-testable on Linux.

A repeated background reapply mechanism may be retained if Windows/driver testing confirms that some systems revert gamma ramps. It must be cancellable per display and must never outlive the profile/application state that created it.

## 7. NVIDIA Digital Vibrance

Do not depend on `NvAPIWrapper.Net` in the Python product.

The Windows NVIDIA adapter dynamically loads `nvapi64.dll`, obtains `nvapi_QueryInterface`, and resolves only the NVAPI functions RAT VISION needs. The upstream wrapper is used as a behavioral/reference source, not shipped as a .NET dependency.

v1 requires:

- NVAPI initialization/unload;
- mapping a Windows display name to the associated NVIDIA display handle;
- reading the current DVC/Digital Vibrance range/value;
- setting DVC level;
- restoring the captured original value.

The adapter is capability-driven: if NVAPI is unavailable or a specific display is not NVIDIA-controlled, saturation is reported unsupported for that display while gamma/brightness/contrast continue to work.

Exact native structures/function signatures must be verified against NVIDIA/NvAPIWrapper references before the Windows hardware adapter is considered complete. Unit tests use a fake query-interface/function table and never require an NVIDIA GPU.

## 8. Process Discovery and Matching

Core matching remains case-insensitive and uses normalized executable identity, not mutable window titles.

`psutil` may be used to enumerate running processes and retrieve executable/name metadata for the Add Game dialog. Windows foreground resolution itself continues to use the foreground HWND → PID → executable/process identity path so profile activation does not depend on a periodic process scan.

If `psutil` cannot access a process, the UI skips or degrades that item rather than failing discovery.

## 9. Tkinter UI Strategy

Tkinter supplies the window, focus, event loop, geometry, clipboard, file dialogs, and accessibility-compatible native basics. The approved RAT VISION presentation is rendered with focused custom controls instead of default gray Tk widgets.

Custom controls use Canvas drawing for:

- thin instrument sliders;
- compact ON/OFF toggles with separate LED state;
- monitor checkboxes;
- restrained lab cards/panels;
- RAT buttons and tertiary actions;
- modals and toast surfaces where native widgets would visibly break the design.

Standard Tk/ttk controls may remain inside custom shells for text entry, scrolling, list behavior, or accessibility when their native behavior is more valuable than custom drawing.

All sizing derives from centralized theme/spacing tokens. The master/detail layout, sticky Buy me a coffee button, Add Game flow, profile workspace, Updates placeholder, and Settings content remain exactly as approved in the UI blueprint.

## 10. Themes

`ThemeManager` owns semantic tokens rather than widget-specific hard-coded colors.

Required modes:

- `Night // Level Black`;
- `Day // Clean Lab`;
- `Follow Windows` on Windows, mapped to one of the two RAT VISION themes.

Theme changes redraw custom controls and update ordinary Tk/ttk styles at runtime without restarting the application.

XRAT green remains a functional status color. Day/Clean Lab keeps its separate cyan/blue corporate accent.

## 11. Assets and Emoji

Brand images and curated polished 3D emoji-style PNG assets are stored as application resources. Apple emoji artwork is not redistributed.

Pillow loads/scales PNG assets once per required display size and the asset manager keeps Tk `PhotoImage` references alive while widgets use them.

The program must have a monochrome fallback glyph/icon set when 3D emoji are disabled in Settings or an asset cannot be loaded.

Tray artwork is purpose-built at small sizes; it is not produced by naively shrinking the full logo at runtime.

## 12. Threading and UI Safety

Tk widgets are mutated only on the Tk event-loop thread.

Native hooks, background gamma reapply loops, log workers, or future update workers communicate back through a thread-safe queue. `root.after(...)` drains/dispatches queued state changes on the UI thread.

Shutdown order is explicit:

1. disable new profile activations;
2. cancel reapply/background workers;
3. restore all displays/DVC values;
4. stop foreground hook;
5. remove tray icon;
6. persist final settings;
7. destroy Tk root.

Every cleanup stage is attempted even if an earlier one reports an error.

## 13. Settings and Paths

Use a versioned JSON schema with `schema_version` and atomic replace-on-save.

Normal Windows user data lives under `%LOCALAPPDATA%\RatVision\`:

- `settings.json`;
- `logs/`;
- diagnostics exports when explicitly saved there.

Development/simulation mode may redirect the data directory to a temporary test path.

The upstream `settings.json` migration remains deterministic and creates an imported profile rather than silently overwriting the three RAT VISION defaults.

## 14. Simulation Mode

When the application runs outside Windows or when `RATVISION_SIMULATION=1` is set, `app.py` selects simulation platform adapters.

Simulation mode provides:

- synthetic monitor list;
- fake foreground-process transitions;
- in-memory color apply/restore history;
- simulated tray state represented in diagnostics/UI rather than an OS tray icon;
- no registry/startup writes;
- no native gamma/NVAPI calls.

This mode is an engineering feature, not an end-user product mode. It is the basis for screenshot-driven UI review and integration tests in the chat environment.

## 15. Testing

### Pure/core tests

Use pytest for:

- default profiles;
- model validation;
- case-insensitive multi-executable matching;
- copy/reset semantics;
- settings migration and atomic persistence behavior;
- gamma LUT calculation;
- activation coordinator state transitions;
- global OFF and restore behavior;
- multi-monitor selection and independent restore decisions.

### Platform adapter tests

Use fake `ctypes` function objects/tables to verify:

- Win32 handle/lifecycle cleanup;
- hook callback retention and stop behavior;
- gamma capture/apply/restore sequencing;
- NVAPI capability and error mapping;
- tray state mapping and command dispatch.

These tests do not require Windows hardware.

### UI tests

Run Tk under a virtual X display in development:

- construct main window in simulation mode;
- drive selected state/view-model methods;
- verify geometry/state bindings;
- capture screenshots for human visual review;
- verify both Day and Night themes;
- verify resizing and scrolling at representative dimensions.

Final Windows manual verification covers native tray integration, high-DPI rendering, monitor metadata, gamma ramps, and NVIDIA DVC.

## 16. Delivery and Packaging

Development deliverable is a runnable Python source application with tests and a Windows launcher script.

The release build is a **Windows x64 packaged app** created in a Windows environment using a packaging tool such as PyInstaller or Nuitka after the Python application is feature-complete. Packaging is intentionally a release-stage concern and must not block normal development in this chat environment.

The packaged build must include Python runtime/dependencies/assets so the end user does not need to install Python manually.

Final packaging acceptance requires one real Windows build/run. That requirement is much smaller than requiring Windows for all development.

## 17. Preserved Product Decisions

The stack revision does not reopen approved product/UI decisions. RAT VISION still includes:

- three default profiles: Escape from Tarkov, Escape from Tarkov: Arena, Hunt: Showdown;
- independent visual parameters per profile;
- multiple executables per profile;
- checkbox-based multi-monitor targeting;
- global persistent XRAT ON/OFF;
- approved RAT VISION / XRAT branding;
- first-concept monochrome rat mark;
- separate green tray lamp for ON/waiting;
- Night // Level Black and Day // Clean Lab;
- semantic polished 3D emoji-style assets;
- Add Game from running application or `.exe`;
- sticky `☕ Buy me a coffee`;
- Updates UI placeholder without a fake update backend;
- version visibility in title/About/diagnostics;
- reliable restore on focus loss, global OFF, and exit.
