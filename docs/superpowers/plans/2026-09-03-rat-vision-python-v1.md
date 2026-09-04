# RAT VISION Python v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Build RAT VISION v1 as a testable Python 3.13 Windows desktop utility with the approved master/detail UI, game-specific display profiles, multi-monitor targeting, global XRAT toggle, tray state, themes, diagnostics, and isolated Win32/NVIDIA adapters.

**Architecture:** Policy and persistence live in pure Python packages that are fully testable on Linux. Tkinter/Canvas renders the approved RAT VISION interface, while all Windows-only work is isolated behind `Protocol` interfaces with simulation implementations for development and tests. Windows adapters use `ctypes` and never mutate Tk widgets from native callback threads.

**Tech Stack:** Python 3.13 x64, Tkinter/ttk, Pillow, psutil, ctypes, dataclasses, pathlib, json, logging, threading, pytest.

**Spec:** `docs/superpowers/specs/2026-09-03-rat-vision-design.md`, `docs/superpowers/specs/2026-09-03-rat-vision-ui-blueprint.md`, `docs/superpowers/specs/2026-09-03-rat-vision-python-architecture.md`

## Global Constraints

- Product name is **RAT VISION**; `XRAT TRACING` is secondary fictional technology/protocol copy only.
- Python runtime target is **Python 3.13 x64**.
- RAT VISION is a Windows product; Linux behavior exists only as simulation/test mode.
- Default profiles: Escape from Tarkov, Escape from Tarkov: Arena, Hunt: Showdown.
- Each profile owns brightness, contrast, gamma, saturation, one or more executable identities, and one or more displays.
- Global OFF immediately restores all touched displays and prevents profile application without closing the app.
- UI uses approved master/detail layout with fixed top bar/sidebar and scrollable workspace.
- Themes: `Night // Level Black` default, `Day // Clean Lab`, and `Follow Windows`.
- XRAT green is functional state color; Clean Lab cyan/blue is separate corporate accent.
- Semantic 3D emoji/image assets reinforce text; essential actions never depend on emoji alone.
- Tray has exactly two global states in v1: OFF hollow lamp and ON/waiting green lamp.
- Update section is an honest placeholder and performs no network update check in v1.
- Version is visible in window title/header, About, diagnostics, and exported diagnostics.
- All settings changes save automatically.
- Original `tarkov-settings` attribution and license notices are preserved in About/README/license materials.

---

### Task 1: Python package scaffold, version, domain models, and defaults

**Files:**
- Create: `pyproject.toml`
- Create: `ratvision/__init__.py`
- Create: `ratvision/version.py`
- Create: `ratvision/domain/__init__.py`
- Create: `ratvision/domain/models.py`
- Create: `ratvision/domain/defaults.py`
- Create: `tests/domain/test_models.py`
- Create: `tests/domain/test_defaults.py`

**Interfaces:**
- Produces `VisualParameters`, `GameProfile`, `DisplayInfo`, `ForegroundProcess`, `AppSettings`, `ThemeMode`.
- Produces `create_default_profiles(displays: Sequence[DisplayInfo]) -> list[GameProfile]`.
- `VisualParameters.normalized()` clamps brightness/contrast to `0..1`, gamma to `0.4..2.8`, saturation to integer `0..100`.

- [x] **Step 1: Write failing model/default tests**

```python
from ratvision.domain.models import VisualParameters


def test_visual_parameters_normalize_to_supported_ranges():
    value = VisualParameters(-1, 2, 9, 140).normalized()
    assert value == VisualParameters(0.0, 1.0, 2.8, 100)
```

```python
from ratvision.domain.defaults import create_default_profiles
from ratvision.domain.models import DisplayInfo


def test_default_profiles_include_three_games_and_primary_display():
    displays = [DisplayInfo("DISPLAY1", "Main", 2560, 1440, 165.0, True, True)]
    profiles = create_default_profiles(displays)
    assert [p.name for p in profiles] == [
        "Escape from Tarkov",
        "Escape from Tarkov: Arena",
        "Hunt: Showdown",
    ]
    assert profiles[0].processes == ["escapefromtarkov.exe"]
    assert set(profiles[2].processes) == {"hunt.exe", "huntgame.exe"}
    assert all(p.display_ids == ["DISPLAY1"] for p in profiles)
```

- [x] **Step 2: Run tests and verify import failures**

Run: `pytest tests/domain/test_models.py tests/domain/test_defaults.py -q`
Expected: collection/import failure because `ratvision.domain` does not exist.

- [x] **Step 3: Implement dataclasses and defaults**

Use immutable `VisualParameters`, normalized lowercase executable identities, UUID string profile IDs, and `ThemeMode` enum values `night`, `day`, `system`.

- [x] **Step 4: Run tests**

Run: `pytest tests/domain/test_models.py tests/domain/test_defaults.py -q`
Expected: PASS.

- [x] **Step 5: Commit**

```bash
git add pyproject.toml ratvision tests/domain
git commit -m "feat: add RAT VISION domain model"
```

### Task 2: Settings persistence, migration, autosave-safe serialization, import/export

**Files:**
- Create: `ratvision/persistence/__init__.py`
- Create: `ratvision/persistence/settings_store.py`
- Create: `ratvision/persistence/migration.py`
- Create: `tests/persistence/test_settings_store.py`
- Create: `tests/persistence/test_migration.py`

**Interfaces:**
- Produces `SettingsStore(path: Path)` with `load(displays) -> AppSettings`, `save(settings) -> None`, `export_to(settings, destination)`, `import_from(source, displays) -> AppSettings`.
- Writes atomically via sibling temporary file then `Path.replace()`.
- Invalid JSON is renamed to `settings.invalid-YYYYMMDD-HHMMSS.json` and safe defaults are returned.
- Migration understands the upstream flat keys `brightness`, `contrast`, `gamma`, `saturation`, `pTargets`, `display`, `minimizeOnStart` and converts them to one imported profile while retaining the three new defaults only when no user profile data exists.

- [x] **Step 1: Write failing round-trip and invalid-file tests**

```python
def test_settings_round_trip_preserves_profiles(tmp_path, sample_settings):
    store = SettingsStore(tmp_path / "settings.json")
    store.save(sample_settings)
    assert store.load([]) == sample_settings
```

```python
def test_invalid_json_is_backed_up_and_defaults_loaded(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text("{broken", encoding="utf-8")
    loaded = SettingsStore(path).load([])
    assert loaded.profiles
    assert list(tmp_path.glob("settings.invalid-*.json"))
```

- [x] **Step 2: Verify failure**

Run: `pytest tests/persistence -q`
Expected: FAIL because persistence modules are absent.

- [x] **Step 3: Implement explicit dict serializers and migration**

Do not serialize dataclasses with pickle. JSON schema includes `schema_version`, `app`, and `profiles`; unknown keys are ignored on read.

- [x] **Step 4: Run tests**

Run: `pytest tests/persistence -q`
Expected: PASS.

- [x] **Step 5: Commit**

```bash
git add ratvision/persistence tests/persistence
git commit -m "feat: persist and migrate RAT VISION settings"
```

### Task 3: Platform protocols and deterministic simulation backend

**Files:**
- Create: `ratvision/platform/__init__.py`
- Create: `ratvision/platform/base.py`
- Create: `ratvision/platform/simulation.py`
- Create: `tests/platform/test_simulation.py`

**Interfaces:**
- `ForegroundWindowProvider.start(callback)`, `.stop()`, `.current()`.
- `DisplayProvider.list_displays() -> list[DisplayInfo]`.
- `ColorBackend.capture(display_id)`, `.apply(display_id, params)`, `.restore(display_id)`, `.restore_all()`, `.capabilities(display_id)`.
- `TrayBackend.start(actions)`, `.set_enabled(enabled)`, `.stop()`.
- `StartupBackend.is_enabled()`, `.set_enabled(value)`.
- Simulation exposes test helpers `focus(executable)`, `set_displays(...)` and records color calls.

- [x] **Step 1: Write simulation behavior tests**

```python
def test_simulated_foreground_emits_normalized_executable():
    provider = SimulationForegroundProvider()
    seen = []
    provider.start(seen.append)
    provider.focus("HuntGame.EXE")
    assert seen[-1].executable == "huntgame.exe"
```

- [x] **Step 2: Verify failure**

Run: `pytest tests/platform/test_simulation.py -q`
Expected: FAIL because platform abstractions do not exist.

- [x] **Step 3: Implement protocols and fakes**

Use `typing.Protocol`; no Windows imports are allowed in `base.py` or `simulation.py`.

- [x] **Step 4: Run tests**

Run: `pytest tests/platform/test_simulation.py -q`
Expected: PASS.

- [x] **Step 5: Commit**

```bash
git add ratvision/platform tests/platform
git commit -m "feat: add platform abstraction and simulation mode"
```

### Task 4: Profile service and XRAT activation coordinator

**Files:**
- Create: `ratvision/domain/profile_service.py`
- Create: `ratvision/domain/activation_coordinator.py`
- Create: `tests/domain/test_profile_service.py`
- Create: `tests/domain/test_activation_coordinator.py`

**Interfaces:**
- `ProfileService.match(executable) -> GameProfile | None`, `.copy_visuals(source_id, target_id)`, `.add_process`, `.remove_process`, `.set_displays`.
- `ActivationCoordinator.on_foreground(process)` applies/restores profiles through `ColorBackend`.
- `ActivationCoordinator.set_global_enabled(value)` restores immediately when false.
- `ActivationCoordinator.refresh_profile(profile_id)` reapplies live profile after slider/display changes.

- [x] **Step 1: Write failing policy tests**

```python
def test_global_off_restores_all_and_blocks_matching(sample_settings, fake_color):
    coordinator = build_coordinator(sample_settings, fake_color)
    coordinator.set_global_enabled(False)
    coordinator.on_foreground(ForegroundProcess(1, "escapefromtarkov.exe", ""))
    assert fake_color.applied == []
    assert fake_color.restore_all_count == 1
```

```python
def test_copy_visuals_does_not_copy_processes_or_displays(profile_service):
    source, target = profile_service.profiles[:2]
    target_processes = list(target.processes)
    target_displays = list(target.display_ids)
    profile_service.copy_visuals(source.id, target.id)
    assert target.processes == target_processes
    assert target.display_ids == target_displays
    assert target.visual == source.visual
```

- [x] **Step 2: Verify failure**

Run: `pytest tests/domain/test_profile_service.py tests/domain/test_activation_coordinator.py -q`
Expected: FAIL.

- [x] **Step 3: Implement policy layer**

Profile matching is case-insensitive, enabled-only, and executable-based. Applying a profile captures and updates every selected online display; leaving the profile restores all displays touched by the previous active profile.

- [x] **Step 4: Run tests**

Run: `pytest tests/domain/test_profile_service.py tests/domain/test_activation_coordinator.py -q`
Expected: PASS.

- [x] **Step 5: Commit**

```bash
git add ratvision/domain tests/domain
git commit -m "feat: coordinate XRAT profile activation"
```

### Task 5: Theme tokens, asset manager, and custom RAT controls

**Files:**
- Create: `ratvision/ui/__init__.py`
- Create: `ratvision/ui/theme.py`
- Create: `ratvision/ui/assets.py`
- Create: `ratvision/ui/controls/__init__.py`
- Create: `ratvision/ui/controls/button.py`
- Create: `ratvision/ui/controls/toggle.py`
- Create: `ratvision/ui/controls/slider.py`
- Create: `ratvision/ui/controls/checkbox.py`
- Create: `ratvision/ui/controls/led.py`
- Create: `ratvision/ui/controls/card.py`
- Create: `tests/ui/test_theme.py`
- Create: `tests/ui/test_controls_smoke.py`

**Interfaces:**
- `ThemeManager.tokens(mode) -> ThemeTokens`, `.apply(root, mode)`.
- `AssetManager.get(name, size) -> ImageTk.PhotoImage | None` with strong cache references.
- Controls accept semantic theme tokens, expose ordinary Tk variables/callbacks, and redraw on theme change.

- [x] **Step 1: Write failing token and GUI smoke tests**

```python
def test_clean_lab_uses_blue_for_selection_not_xrat_green():
    tokens = ThemeManager().tokens(ThemeMode.DAY)
    assert tokens.accent != tokens.status_on
    assert tokens.accent.lower() == "#39aeea"
```

GUI smoke test creates a hidden `Tk`, mounts each custom control, calls `update_idletasks()`, then destroys the root.

- [x] **Step 2: Verify failure**

Run: `xvfb-run -a pytest tests/ui/test_theme.py tests/ui/test_controls_smoke.py -q`
Expected: FAIL.

- [x] **Step 3: Implement centralized semantic tokens and Canvas controls**

Use the 8 px spacing system and 4–6 px panel radii. Slider progress is neutral in Night and blue in Day; ordinary controls never use XRAT green as progress/selection color.

- [x] **Step 4: Run tests under Xvfb**

Run: `xvfb-run -a pytest tests/ui/test_theme.py tests/ui/test_controls_smoke.py -q`
Expected: PASS.

- [x] **Step 5: Commit**

```bash
git add ratvision/ui tests/ui
git commit -m "feat: add RAT VISION theme and control kit"
```

### Task 6: Main shell, profile sidebar, workspace, autosave bindings

**Files:**
- Create: `ratvision/ui/main_window.py`
- Create: `ratvision/ui/sidebar.py`
- Create: `ratvision/ui/profile_workspace.py`
- Create: `tests/ui/test_main_window.py`

**Interfaces:**
- `MainWindow(root, app_controller)` renders fixed top bar, fixed sidebar, scrollable right workspace.
- Sidebar emits `select_profile`, `add_game`, `open_settings`, `donate` actions.
- Workspace edits selected profile and calls controller autosave methods immediately.
- Top bar exposes theme shortcut and global XRAT toggle.

- [x] **Step 1: Write failing structure tests**

Test widgets by stable semantic attributes rather than pixel positions: header version text, three default profile rows, sticky donation/settings actions, four parameter sliders, monitor section, process section.

- [x] **Step 2: Verify failure**

Run: `xvfb-run -a pytest tests/ui/test_main_window.py -q`
Expected: FAIL.

- [x] **Step 3: Implement approved master/detail shell**

Default geometry `1180x760`, minimum `980x640`. Right workspace is a Canvas+scrollbar interior frame; top and sidebar never scroll.

- [x] **Step 4: Run tests**

Run: `xvfb-run -a pytest tests/ui/test_main_window.py -q`
Expected: PASS.

- [x] **Step 5: Commit**

```bash
git add ratvision/ui tests/ui/test_main_window.py
git commit -m "feat: build RAT VISION main profile workspace"
```

### Task 7: Add Game, process discovery, profile emoji selection, copy/reset tools

**Files:**
- Create: `ratvision/platform/processes.py`
- Create: `ratvision/ui/add_game_dialog.py`
- Create: `ratvision/ui/profile_tools.py`
- Create: `tests/platform/test_processes.py`
- Create: `tests/ui/test_add_game_dialog.py`

**Interfaces:**
- `ProcessDiscovery.list_running() -> list[RunningProcess]` skips inaccessible processes.
- Add Game supports running-process source and `.exe` file source, then name/mark/process/display/starting-parameters step.
- User-created profile defaults to primary display and `VisualParameters()` unless copying from another profile.

- [x] **Step 1: Write discovery and dialog state tests**

Mock `psutil.process_iter` to include an `AccessDenied` process and assert valid items remain. Test that creation with `copy_from_id` clones visuals only.

- [x] **Step 2: Verify failure**

Run: `xvfb-run -a pytest tests/platform/test_processes.py tests/ui/test_add_game_dialog.py -q`
Expected: FAIL.

- [x] **Step 3: Implement discovery and two-step modal**

Manual `.exe` selection extracts filename as normalized process identity and uses stem/product label as editable profile name.

- [x] **Step 4: Run tests**

Run: `xvfb-run -a pytest tests/platform/test_processes.py tests/ui/test_add_game_dialog.py -q`
Expected: PASS.

- [x] **Step 5: Commit**

```bash
git add ratvision/platform/processes.py ratvision/ui tests/platform tests/ui
git commit -m "feat: add game profile creation flow"
```

### Task 8: Settings, theme switching, diagnostics, donation, update placeholder

**Files:**
- Create: `ratvision/ui/settings_view.py`
- Create: `ratvision/diagnostics/__init__.py`
- Create: `ratvision/diagnostics/collector.py`
- Create: `ratvision/updates/__init__.py`
- Create: `ratvision/updates/service.py`
- Create: `tests/diagnostics/test_collector.py`
- Create: `tests/ui/test_settings_view.py`

**Interfaces:**
- `DiagnosticsCollector.collect() -> dict[str, object]`, `.format_text() -> str` includes version, XRAT state, foreground executable, displays, backend capabilities.
- `UpdateService.check()` returns `UpdateStatus.NOT_CONNECTED` in v1.
- Donation action opens the configured URL through injected `open_url(url)` callable.
- Settings changes autosave.

- [x] **Step 1: Write failing diagnostics/settings tests**

Assert About shows version/upstream attribution, Update button surfaces exact copy `UPDATE PROTOCOL NOT CONNECTED`, and Day/Night switch updates theme manager state.

- [x] **Step 2: Verify failure**

Run: `xvfb-run -a pytest tests/diagnostics tests/ui/test_settings_view.py -q`
Expected: FAIL.

- [x] **Step 3: Implement Settings workspace**

Include Startup, Window Behavior, Notifications, Profile Data import/export/restore defaults, Appearance, Diagnostics, Updates, and About sections. Donation URL is supplied from application config; no green permanent donation styling.

- [x] **Step 4: Run tests**

Run: `xvfb-run -a pytest tests/diagnostics tests/ui/test_settings_view.py -q`
Expected: PASS.

- [x] **Step 5: Commit**

```bash
git add ratvision/ui/settings_view.py ratvision/diagnostics ratvision/updates tests
git commit -m "feat: add settings diagnostics and update placeholder"
```

### Task 9: Windows foreground, display metadata, and startup adapters

**Files:**
- Create: `ratvision/platform/windows/__init__.py`
- Create: `ratvision/platform/windows/foreground.py`
- Create: `ratvision/platform/windows/displays.py`
- Create: `ratvision/platform/windows/startup.py`
- Create: `tests/platform/windows/test_foreground.py`
- Create: `tests/platform/windows/test_displays.py`
- Create: `tests/platform/windows/test_startup.py`

**Interfaces:**
- Native modules import safely on non-Windows and raise `PlatformUnavailableError` only when instantiated.
- Foreground uses `SetWinEventHook(EVENT_SYSTEM_FOREGROUND)` and retains the `WINFUNCTYPE` callback strongly until `.stop()`.
- Display provider enumerates Windows display devices and produces `DisplayInfo`.
- Startup backend uses current-user `HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run` through `winreg`.

- [x] **Step 1: Write fake-library unit tests**

Inject fake `user32` functions and verify hook/unhook call order and callback retention. Mock Windows display enumeration data and registry calls.

- [x] **Step 2: Verify failure**

Run: `pytest tests/platform/windows/test_foreground.py tests/platform/windows/test_displays.py tests/platform/windows/test_startup.py -q`
Expected: FAIL.

- [x] **Step 3: Implement ctypes adapters with dependency injection seams**

Native callbacks only emit `ForegroundProcess`; Tk scheduling is owned by application controller.

- [x] **Step 4: Run tests on Linux using fakes**

Run: `pytest tests/platform/windows/test_foreground.py tests/platform/windows/test_displays.py tests/platform/windows/test_startup.py -q`
Expected: PASS.

- [x] **Step 5: Commit**

```bash
git add ratvision/platform/windows tests/platform/windows
git commit -m "feat: add Windows foreground display and startup adapters"
```

### Task 10: Gamma LUT/backend and NVIDIA DVC adapter

**Files:**
- Create: `ratvision/platform/windows/gamma.py`
- Create: `ratvision/platform/windows/nvapi.py`
- Create: `ratvision/platform/windows/color_backend.py`
- Create: `tests/platform/windows/test_gamma.py`
- Create: `tests/platform/windows/test_nvapi.py`
- Create: `tests/platform/windows/test_color_backend.py`

**Interfaces:**
- `calculate_lut(params: VisualParameters) -> tuple[int, ...]` preserves upstream curve formula exactly.
- `GammaController` captures/restores an independent 256-entry RGB baseline per display ID.
- `NvApiDvcController` resolves only initialize/unload/display-handle/get-DVC/set-DVC functions and captures original DVC per supported display.
- `WindowsColorBackend` combines gamma and DVC and degrades saturation capability independently.

- [x] **Step 1: Write golden LUT and restore tests**

Use known inputs `VisualParameters(0.5, 0.5, 1.0, 0)` to assert first/last values `0`/`65535` and monotonicity; add exact sampled values derived from the upstream formula. Verify two displays restore distinct baselines.

- [x] **Step 2: Verify failure**

Run: `pytest tests/platform/windows/test_gamma.py tests/platform/windows/test_nvapi.py tests/platform/windows/test_color_backend.py -q`
Expected: FAIL.

- [x] **Step 3: Implement pure LUT then injected native wrappers**

Use `CreateDCW`, `GetDeviceGammaRamp`, `SetDeviceGammaRamp`, `DeleteDC`. NVAPI loads through `ctypes.WinDLL("nvapi64.dll")`, obtains query-interface, and uses verified function IDs/signatures isolated in constants/structures.

- [x] **Step 4: Run unit tests without hardware**

Run: `pytest tests/platform/windows/test_gamma.py tests/platform/windows/test_nvapi.py tests/platform/windows/test_color_backend.py -q`
Expected: PASS.

- [x] **Step 5: Commit**

```bash
git add ratvision/platform/windows tests/platform/windows
git commit -m "feat: port gamma and NVIDIA vibrance backends"
```

### Task 11: Tray icon state and Windows tray backend

**Files:**
- Create: `ratvision/platform/windows/tray.py`
- Create: `ratvision/ui/tray_assets.py`
- Create: `tests/platform/windows/test_tray.py`

**Interfaces:**
- `TrayActions(open_app, toggle_enabled, open_settings, donate, exit_app)`.
- Tray artwork exposes two image states only: `off` and `on`.
- Windows backend uses `Shell_NotifyIconW`; context menu includes RAT VISION/version, XRAT toggle, Open, Settings, Buy me a coffee, Exit.

- [x] **Step 1: Write menu/state tests against injected shell API**

Assert `.set_enabled(False)` selects hollow-lamp icon resource and `.set_enabled(True)` selects green-lamp icon resource; no profile-active state exists.

- [x] **Step 2: Verify failure**

Run: `pytest tests/platform/windows/test_tray.py -q`
Expected: FAIL.

- [x] **Step 3: Implement small-purpose tray renderer and shell adapter**

Tray icon rendering uses a purpose-built monochrome rat glyph and separate lower-right lamp; green bloom is restrained and only in ON state.

- [x] **Step 4: Run tests**

Run: `pytest tests/platform/windows/test_tray.py -q`
Expected: PASS.

- [x] **Step 5: Commit**

```bash
git add ratvision/platform/windows/tray.py ratvision/ui/tray_assets.py tests/platform/windows/test_tray.py
git commit -m "feat: add RAT VISION tray states and menu"
```

### Task 12: Application controller, simulation launch, Windows composition, safe shutdown

**Files:**
- Create: `ratvision/controller.py`
- Create: `ratvision/app.py`
- Create: `ratvision/__main__.py`
- Create: `tests/test_controller.py`
- Create: `tests/test_app_smoke.py`

**Interfaces:**
- `AppController` owns settings store, profile service, activation coordinator, theme manager, backends, and UI-thread scheduling.
- `python -m ratvision --simulate` uses simulation platform and starts a fully interactive GUI on Linux/Windows.
- Normal Windows launch composes Windows adapters.
- Shutdown order: stop foreground hook → restore color backend → stop tray → persist settings → destroy Tk root.

- [x] **Step 1: Write controller/shutdown tests**

Verify global toggle updates tray and settings, foreground callbacks are scheduled with `root.after`, and shutdown restores before the root is destroyed.

- [x] **Step 2: Verify failure**

Run: `xvfb-run -a pytest tests/test_controller.py tests/test_app_smoke.py -q`
Expected: FAIL.

- [x] **Step 3: Implement composition and CLI arguments**

CLI supports `--simulate`, `--settings PATH`, `--theme night|day|system` for deterministic testing.

- [x] **Step 4: Run complete suite**

Run: `xvfb-run -a pytest -q`
Expected: PASS.

- [x] **Step 5: Commit**

```bash
git add ratvision tests
git commit -m "feat: compose RAT VISION application"
```

### Task 13: Brand assets, emoji fallback, screenshot review harness

**Files:**
- Create: `ratvision/resources/README.md`
- Create: `ratvision/resources/brand/rat_mark.png`
- Create: `ratvision/resources/brand/rat_mark_small.png`
- Create: `ratvision/resources/emoji/` curated embedded assets or original substitutes with license notice
- Create: `tools/capture_ui.py`
- Create: `tests/ui/test_assets.py`

**Interfaces:**
- Every asset requested by the approved UI has a packaged image or deterministic monochrome fallback.
- `tools/capture_ui.py --theme night|day --output PATH` starts simulation mode at `1180x760`, selects the Tarkov profile, renders, captures, exits.

- [x] **Step 1: Write asset-presence/fallback tests**

Assert missing 3D emoji never raises and returns a fallback semantic glyph; brand/tray images have small-size variants.

- [x] **Step 2: Verify failure**

Run: `xvfb-run -a pytest tests/ui/test_assets.py -q`
Expected: FAIL.

- [x] **Step 3: Add approved original brand artwork and curated/legal emoji assets**

Store license/source notes in `ratvision/resources/README.md`. Do not include Apple emoji artwork.

- [x] **Step 4: Capture both themes and run visual sanity checks**

Run:
`xvfb-run -a python tools/capture_ui.py --theme night --output /tmp/ratvision-night.png`
`xvfb-run -a python tools/capture_ui.py --theme day --output /tmp/ratvision-day.png`
Expected: both files exist at 1180×760 and show complete main screen without clipped sections at initial scroll position.

- [x] **Step 5: Commit**

```bash
git add ratvision/resources tools/capture_ui.py tests/ui/test_assets.py
git commit -m "feat: add RAT VISION visual assets and screenshot harness"
```

### Task 14: Documentation, portable Windows launcher/build recipe, final verification

**Files:**
- Create: `README.md`
- Create: `LICENSES.md`
- Create: `scripts/start-rat-vision.bat`
- Create: `scripts/build-windows.bat`
- Create: `scripts/verify.bat`
- Modify: `.gitignore`

**Interfaces:**
- `start-rat-vision.bat` launches `python -m ratvision` from an installed Python 3.13 environment with clear errors.
- `build-windows.bat` creates an isolated venv, installs declared runtime/build dependencies, and invokes PyInstaller only on Windows if available/installed by the build step.
- `verify.bat` runs pytest before packaging.
- README explains normal use, simulation mode, supported GPUs, attribution, settings location, and the exact Windows hardware verification checklist.

- [x] **Step 1: Add documentation assertions to test suite**

Test that version string appears in README and that scripts reference `python -m ratvision`/`pytest` rather than obsolete WPF commands.

- [x] **Step 2: Verify failure**

Run: `pytest tests/test_docs.py -q`
Expected: FAIL until docs/scripts exist.

- [x] **Step 3: Write docs and Windows scripts**

Hardware verification checklist must explicitly test: global OFF restore, Alt-Tab restore/reapply, two-monitor independent restore, Tarkov/Arena/Hunt process matching, NVIDIA saturation support/degradation, tray OFF/ON lamp, exit restore.

- [x] **Step 4: Run final Linux verification**

Run:
`xvfb-run -a pytest -q`
`python -m compileall -q ratvision`
`git status --short`
Expected: all tests PASS, compileall succeeds, status clean after commit.

- [x] **Step 5: Commit**

```bash
git add README.md LICENSES.md scripts .gitignore tests/test_docs.py
git commit -m "docs: add RAT VISION run build and verification workflow"
```

## Plan Self-Review

- Spec coverage: domain profiles, defaults, autosave persistence/migration, global XRAT policy, multi-monitor, process matching, master/detail UI, sliders/reset/copy tools, Add Game, Settings, diagnostics, donation, update placeholder, themes, tray, Windows adapters, attribution, version display, and screenshot review all have explicit tasks.
- Platform boundary: Tasks 1–8 and 12–13 are executable/testable in this Linux environment; Tasks 9–11 use injected native fakes so their Python behavior is testable here while final hardware behavior is verified on Windows.
- No placeholder implementation steps remain; the intentionally disconnected update service has a specified deterministic v1 behavior.
- Type/signature consistency: `AppSettings`, `GameProfile`, `VisualParameters`, `DisplayInfo`, platform protocols, `ProfileService`, `ActivationCoordinator`, and `AppController` are introduced before consumers.
