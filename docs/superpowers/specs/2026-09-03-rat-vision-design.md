# RAT VISION — Design Specification

Date: 2026-09-03
Status: Approved product/UI/Python architecture
Upstream reference: `incheon-kim/tarkov-settings`
UI authority: `2026-09-03-rat-vision-ui-blueprint.md` supersedes UI-specific details in this document where the two differ.

## 1. Product Definition

RAT VISION is a new Windows desktop product derived from the behavior of `tarkov-settings`, not a cosmetic reskin of the original application. It automatically applies a per-game display profile when one of the profile's target processes owns the foreground window, and restores the normal desktop display state when no enabled profile matches.

Primary brand name: **RAT VISION**.
Internal joke/technology name: **XRAT TRACING**.
Primary secondary line: **See what the rat sees.**
Optional About/README line: **Powered by questionable research.**

The application title must include the running version, e.g. `RAT VISION v1.0.0`.

## 2. Goals

1. Preserve the proven low-level display-control behavior from the upstream project where practical.
2. Replace the old WinForms UI with a maintainable custom RAT VISION desktop UI that can be developed/tested in simulation mode.
3. Support separate visual settings per game/application profile.
4. Allow multiple executable process names to activate one profile.
5. Provide a global enable/disable switch that does not close the program.
6. Make adding applications easy without requiring the user to know a process name.
7. Keep tray behavior clear and immediately understandable.
8. Establish a distinct RAT VISION brand and a coherent dark laboratory UI system.

## 3. Non-Goals for v1

- No per-scene or per-map profiles.
- No automatic profile optimization from screenshots.
- No hotkey system beyond ordinary application/tray interaction.
- No HDR calibration workflow.
- No game-file modification.
- No attempt to imitate or reproduce copyrighted game UI assets or official corporate logos exactly.

## 4. Technical Platform

### 4.1 Target stack

- **Python 3.13 x64**
- **Tkinter/ttk** for the window/event-loop foundation
- **custom Canvas-based RAT VISION controls** for the approved lab visual language
- **Pillow** for embedded image/emoji assets
- **psutil** for friendly running-process discovery where useful
- **ctypes** for Win32, GDI, Shell tray integration, and NVIDIA NVAPI
- **pytest** for automated tests

The product remains Windows-targeted. A simulation adapter set allows the UI and policy layers to run under Linux for development, automated tests, and screenshot review.

The detailed architecture is authoritative in `2026-09-03-rat-vision-python-architecture.md`.

### 4.2 Migration strategy

The upstream project is WinForms on .NET Framework 4.7.2. RAT VISION ports useful behavior rather than carrying forward the original form architecture or .NET runtime dependency.

Existing behavior worth preserving:

- foreground-window awareness through Win32 APIs;
- gamma-ramp display adjustment;
- NVIDIA Digital Vibrance behavior, reimplemented directly through NVAPI/`ctypes`;
- monitor targeting;
- tray lifecycle behavior;
- restoration of normal display state when the target is no longer active.

The original `MainForm` does not remain a coordinator in the new architecture.

## 5. Architecture

### 5.1 Services

**ForegroundWindowService**
Owns Win32 foreground-window event handling. Publishes the current foreground process identity. It must not know about Tk widgets or profiles.

**ProfileService**
Owns profile matching, profile CRUD, duplication, enabled state, and `Copy settings from...` behavior.

**ColorService**
Applies and restores brightness, contrast, gamma, saturation/Digital Vibrance and target-display state. It wraps the native/NVIDIA implementations behind a testable interface.

**SettingsService**
Loads, validates, migrates, and persists application settings and profiles.

**TrayService**
Owns tray icon state, tray menu commands, show/hide main window, global toggle, and exit behavior.

**StartupService**
Owns launch-at-login behavior if enabled.

**ThemeService**
Owns Night / Level Black, Day / Clean Lab, and Follow Windows theme selection and persistence.

**UpdateService / IUpdateService**
Reserved abstraction for update checks. v1 exposes the UI placeholder but does not perform network update checks yet.

### 5.2 Data flow

1. `ForegroundWindowService` reports the current process.
2. If the global RAT VISION switch is OFF, `ColorService` must remain/restored to desktop defaults.
3. If global state is ON, `ProfileService` searches enabled profiles for a matching process.
4. If a profile matches, `ColorService` applies that profile to its configured monitor.
5. If the foreground process changes to a non-matching process, the normal desktop display state is restored immediately.
6. Re-focusing the same game must reapply its profile safely without accumulating transforms.

### 5.3 Failure behavior

- A missing or renamed executable must not crash the app; the profile simply remains idle.
- Failure to change NVIDIA saturation must not block brightness/contrast/gamma where supported.
- Unsupported GPU capabilities must be represented as disabled controls with a clear reason.
- Invalid settings files must be recoverable: preserve a backup when possible and load safe defaults.
- Exiting RAT VISION must always attempt to restore the desktop display state.

## 6. Profile Model

Each game profile contains:

- stable profile ID;
- display name;
- enabled flag;
- one or more target executable/process names;
- one or more target monitors/displays;
- brightness;
- contrast;
- gamma;
- saturation / Digital Vibrance;
- optional built-in profile identifier for defaults/migration.

Process matching is case-insensitive and uses executable/process identity rather than window title text.

### 6.1 Copying settings

`Copy settings from...` copies only visual/display values:

- brightness;
- contrast;
- gamma;
- saturation;

It must not copy profile name, enabled state, target executable list, or profile ID.

### 6.2 Default profiles

Create these on first run unless an existing settings file already contains user profiles:

1. **Escape from Tarkov** — includes `EscapeFromTarkov.exe`.
2. **Escape from Tarkov: Arena** — includes `EscapeFromTarkovArena.exe`.
3. **Hunt: Showdown** — include modern known executable identities such as `hunt.exe` and `HuntGame.exe` so either launcher/runtime path can match.

Defaults are editable and removable by the user.

## 7. Global Enable / Disable

The main window always exposes a prominent global RAT VISION switch.

### OFF

- application remains running;
- tray icon remains present;
- foreground monitoring may continue internally;
- all display changes are restored immediately;
- no game profile is applied while OFF;
- state persists across restarts.

### ON

- RAT VISION waits for a configured target process;
- matching foreground processes activate their enabled profile;
- leaving the game restores the desktop state.

Primary branded action/status copy may use:

- `TURN ON XRAT TRACING`
- `XRAT TRACING // ENABLED`
- `XRAT TRACING // DISABLED`

The joke must never obscure the actual ON/OFF state.

## 8. Application Discovery and Profile Creation

`Add profile` offers two convenient discovery paths:

1. **Choose a running app/window** — enumerate suitable user-visible processes/windows and select one.
2. **Choose an .exe** — standard file picker.

Manual process-name entry may exist under an advanced disclosure, but is not the primary workflow.

One profile may contain multiple executables. The user can add or remove process entries after profile creation.

## 9. Main UX Structure

### 9.1 Main window

The final main-window structure is the master/detail layout defined in `2026-09-03-rat-vision-ui-blueprint.md`: fixed top global bar, fixed left profile sidebar, and scrollable right profile workspace. Profile editing occurs directly in the right workspace rather than on a separate editor page.

### 9.2 Displays

Profiles support multi-monitor selection through a checkbox list. Each selected display is independently restored to its captured desktop state when the profile stops applying.

### 9.3 Settings

Settings includes startup, window behavior, notifications, profile import/export, appearance/theme selection, diagnostics, About, and a visible update-check placeholder. `Buy me a coffee` remains sticky in the main sidebar and is also available from the tray menu.

## 10. Tray Experience

The tray icon is a simplified, small-size-safe version of the RAT VISION rat-head mark.

The rat itself remains monochrome. **Only the separate indicator lamp communicates global state.**

### OFF

- monochrome rat head;
- small lower-right **dark-gray hollow indicator** `○`;
- no green eye or green body coloration.

### ON / waiting

- same monochrome rat head;
- small lower-right **bright green filled lamp** `●`;
- lamp receives a restrained soft glow reminiscent of powered night-vision equipment.

There is no third tray state for “profile active” in v1. The user is likely inside the game at that moment and extra state complexity does not improve the tray experience.

Tray menu must include at minimum:

- Show RAT VISION;
- Enable/Disable RAT VISION;
- current global status;
- Exit.

## 11. Brand and Visual Design

### 11.1 Brand hierarchy

Primary product: **RAT VISION**
Secondary fictional technology/protocol: **XRAT TRACING**

`XRAT` must remain a joke/experimental protocol layer, not replace the product name.

### 11.2 Rat mark

The rat head follows the approved first-concept character:

- black-and-white;
- sharp, slightly wild/stencil-like silhouette;
- clearly a rat, not a fox/cat;
- asymmetrical enough to feel alive rather than purely geometric;
- simplified derivative for 16–24 px sizes.

The larger brand mark may incorporate an optic/lens motif in the eye or the `O` of `VISION`, but the tray ON/OFF state is communicated by the separate lamp, not by changing the rat.

### 11.3 UI style

The rest of the application follows an **original black covert-biotech corporate laboratory language inspired by the feel of TerraGroup Labs Black**, without reproducing official assets.

Design formula:

- 70% sterile corporate laboratory;
- 20% black-ops tactical;
- 10% Tarkov/extraction-shooter humor.

Characteristics:

- almost-black matte background;
- graphite panels;
- off-white primary text;
- steel-gray secondary text;
- thin precise rules and panel borders;
- condensed uppercase display typography;
- neutral grotesk for ordinary UI text;
- monospaced font for technical annotations/process/version data;
- sparse classification labels, brackets, section IDs, and laboratory annotations;
- light texture/distress only on branding/decorative surfaces, not across normal controls.

### 11.4 Green accent rule

Green is functional, not decorative.

Use bright powered-optics green only for:

- enabled lamps/statuses;
- selected/active critical state;
- success/authorized state where appropriate;
- very small XRAT protocol accents.

Do not wash the UI in green and do not use gamer RGB effects.

### 11.5 Three white stripes Easter egg

Three vertical white stripes reminiscent of sports-track-pant stripes may appear as a small visual Easter egg somewhere in the application chrome or About area.

They are not part of the logo, not a primary navigation motif, and must not dominate the design.

## 12. Emoji / Friendly Accent System

The program uses polished 3D emoji-style illustrations as a semantic navigation layer wherever they materially improve visual differentiation, while technical rows remain restrained.

The desired visual feel is Apple-like: rounded, dimensional, expressive and premium. Do **not** redistribute Apple emoji artwork. Prefer a legally usable embedded set with a comparable polished 3D character, such as Microsoft Fluent Emoji assets, subject to license verification during implementation.

Use embedded image resources rather than relying on the user's Windows emoji font so appearance remains consistent. The Python asset manager loads and scales packaged PNG resources through Pillow while retaining Tk image references.

Emoji reinforce text labels and may be used for profiles, processes, visual parameters, displays, tools, settings, import/export, diagnostics, updates, success/warning states, and similar semantic sections. They never replace essential text. Core XRAT ON/OFF status remains primarily lamp + text, so operational state is not dependent on emoji.

Example empty-state copy:

`NO TEST SUBJECTS REGISTERED`
`Add a game to begin XRAT testing.`

## 12.1 Theme System

RAT VISION provides three appearance modes:

- `Night // Level Black` (default): near-black/graphite/off-white with sparse functional XRAT green;
- `Day // Clean Lab`: cold white/gray with TerraGroup-like cyan/blue accents and the same separate XRAT green state color;
- `Follow Windows`: follows the system light/dark preference while mapping into the corresponding RAT VISION theme.

The top bar includes a one-click Day/Night shortcut. Theme-dependent colors/geometry must come from centralized semantic theme tokens so custom Canvas controls and ttk styles update together at runtime.

## 13. Typography System

Use three roles rather than one decorative font everywhere:

1. **Display / brand** — tall condensed uppercase sans/grotesk, used sparingly for RAT VISION, section headers, and major states.
2. **Interface** — highly readable neutral sans/grotesk for controls and descriptions.
3. **Technical** — monospace for process names, diagnostic values, IDs, versions, and pseudo-laboratory annotations.

Fonts must be redistributable with the application or safely rely on a standard Windows family. Exact typefaces are selected during implementation after license verification.

## 14. Versioning and Diagnostics

Version must be visible in:

- window title;
- About page;
- diagnostic export/log metadata.

Diagnostic output should include application version, OS, GPU vendor/capability summary, configured profile names/processes, selected monitor IDs, and global enabled state. It must not expose unrelated personal information.

## 15. Settings Persistence and Migration

The new settings schema must be versioned.

Migration should recognize the upstream-style single global profile where feasible:

- import brightness;
- contrast;
- gamma;
- saturation;
- monitor;
- existing target processes.

Imported old settings may become a user profile rather than silently overwriting the three new defaults. Migration behavior must be deterministic and covered by tests.

Writes should be atomic where practical to reduce settings corruption risk.

## 16. Testing Strategy

### Unit tests

- case-insensitive process matching;
- multiple processes per profile;
- global OFF always suppresses application;
- correct profile selection;
- duplicate/copy semantics;
- settings migration and validation;
- capability handling;
- state restoration decisions.

### Service/integration tests

- foreground-event handling abstraction;
- color service receives apply/restore calls in the correct sequence;
- rapid Alt-Tab does not leave stale display settings;
- application exit requests restore;
- switching directly from Game A to Game B applies B rather than briefly retaining A.

### UI tests / manual verification

- 100%, 125%, 150%, 200% Windows scaling;
- tray icons at small sizes;
- multiple monitors;
- NVIDIA and non-NVIDIA capability presentation;
- first run and migrated run;
- start minimized;
- global toggle from both main window and tray menu.

## 17. Accessibility and Usability

- Do not communicate status by green color alone; pair lamp/color with text or icon shape where the user can inspect it.
- Sliders expose numeric values and keyboard control.
- Primary actions have text labels or accessible names.
- High contrast must remain sufficient despite the dark visual identity.
- Animation, glow, and decorative effects remain restrained and nonessential.

## 18. Delivery Shape for v1

The v1 implementation is complete when:

1. the app launches as RAT VISION on supported Windows systems;
2. three default profiles exist;
3. each profile has independent visual values;
4. profiles support multiple target executables;
5. a user can add a profile from a running window or `.exe`;
6. copy/duplicate/delete/enable profile actions work;
7. global ON/OFF works from main UI and tray;
8. profiles can select one or more displays with checkbox-based multi-select;
9. desktop colors restore reliably on focus loss, OFF, and Exit;
10. the tray icon clearly distinguishes OFF from ON/waiting using the approved lamp states;
11. both Night // Level Black and Day // Clean Lab themes work at runtime;
12. the new lab brand, RAT mark, XRAT copy, and semantic 3D emoji system are applied consistently;
13. the always-visible `Buy me a coffee` action is present;
14. Settings contains the update-check placeholder without pretending the update backend exists;
15. app version is visible in the title and About/diagnostics;
16. automated tests cover the core matching, state, persistence, and restore logic.

## 19. Explicit Design Decisions

The following are settled for v1 and should not be reopened during implementation unless a technical blocker is discovered:

- product name is **RAT VISION**;
- **XRAT TRACING** is secondary internal joke copy;
- separate profile settings per game;
- multiple executables allowed per profile;
- one global persistent ON/OFF switch;
- defaults: Tarkov, Tarkov Arena, Hunt: Showdown;
- Python 3.13 + custom Tkinter/Canvas + Win32 `ctypes` direction instead of continued WinForms/WPF development;
- tray has only OFF and ON/waiting visual states;
- tray status uses a separate indicator lamp;
- rat mark stays monochrome in tray;
- first-concept wild/stencil rat character is preferred;
- overall UI uses original TerraGroup-Black-inspired covert laboratory styling;
- bright green is sparse and functional;
- three white stripes are only an Easter egg;
- polished 3D emoji-style assets are a semantic navigation layer where useful;
- profiles can target multiple displays through checkboxes;
- `Buy me a coffee` remains always visible in the sticky sidebar footer;
- Night // Level Black and Day // Clean Lab are first-class themes, with Follow Windows available;
- an Updates section and `IUpdateService` slot are present before the actual update backend is implemented;
- UI-specific details are governed by the final UI blueprint document.
