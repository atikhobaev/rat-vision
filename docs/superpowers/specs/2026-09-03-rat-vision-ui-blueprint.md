# RAT VISION — Final UI Blueprint

Date: 2026-09-03  
Status: Approved UI blueprint  
Companion design spec: `2026-09-03-rat-vision-design.md`

## 1. UI Intent

RAT VISION should feel like an internal visual-systems utility built by a fictional covert biotech corporation: sterile, precise, black-ops, and slightly absurd when the user notices the rat/XRAT jokes.

The interface is not a Tarkov UI clone and must not reproduce official TerraGroup assets. It uses an original corporate-laboratory visual language inspired by that mood. The approved Python/Tkinter implementation must reproduce this blueprint through custom RAT VISION controls rather than default Tk styling.

Core visual formula:

- sterile laboratory structure;
- covert black-ops restraint;
- readable modern Windows interaction patterns;
- 3D emoji used liberally where they improve visual recognition;
- humor in labels and microcopy, never at the cost of clarity.

Primary product name: **RAT VISION**  
Secondary fictional technology: **XRAT TRACING**  
Secondary slogan: **See what the rat sees.**

## 2. Window Shell

Default window size: approximately **1180 × 760 px**.  
Minimum useful size: approximately **980 × 640 px**.  
The layout must remain usable at 100%, 125%, 150%, and 200% Windows scaling.

The shell has three persistent zones:

1. top global bar;
2. fixed left profile sidebar;
3. scrollable right profile workspace.

The top bar and left sidebar never scroll.

### 2.1 Top global bar

Left:

- `RAT VISION v1.0.0`
- small technical subtitle: `VISUAL SYSTEMS // INTERNAL PROTOCOL`

Right:

- theme shortcut (`☀️` in Night, `🌙` in Day);
- `XRAT TRACING` label;
- separate status lamp;
- global ON/OFF toggle.

Global status examples:

- `○ XRAT TRACING // DISABLED`
- `● XRAT TRACING // ENABLED`

Green is not used as the toggle fill by default. The green lamp is the primary powered-state indicator; text also states the state for accessibility.

## 3. Main Master/Detail Layout

The application uses a **master/detail** structure instead of separate profile-editor pages.

### 3.1 Left sidebar

Target width: approximately **250–270 px**.

Top section:

`🎮 GAME PROFILES`

Each profile row contains:

- a 3D emoji profile mark;
- display name;
- compact enabled/disabled state;
- selection highlight when being edited.

Default visual marks:

- 🐀 Escape from Tarkov
- ⚔️ Escape from Tarkov: Arena
- 🤠 Hunt: Showdown

Profiles selected for editing use a thin high-contrast border/edge and stronger text, not a green flood fill.

Disabled profiles use reduced contrast and explicit `DISABLED` text.

Below the profile list:

- `➕ ADD GAME`

The profile list may scroll independently if many profiles exist, but the bottom utility area remains sticky.

### 3.2 Sticky sidebar footer

Always visible:

- `☕ Buy me a coffee`
- `⚙️ SETTINGS`

The donation button opens the configured donation URL in the default browser. It is visually secondary and never uses the XRAT green accent as a permanent fill.

A small three-white-stripe Easter egg may appear as decorative lab marking in this sidebar or About area. It is not navigation and not part of the logo.

## 4. Right Profile Workspace

The right side is scrollable and displays the selected profile immediately; there is no separate editor page.

### 4.1 Profile header

Example:

- `PROFILE // 01`
- `🐀 ESCAPE FROM TARKOV`
- `🎯 EscapeFromTarkov.exe`
- profile-level `ENABLED [ON/OFF]` control aligned right.

Runtime status line underneath:

- `● LIVE // PROFILE CURRENTLY APPLIED`
- `○ PROCESS DETECTED // WAITING FOR FOCUS`
- `○ READY`
- `○ PROFILE DISABLED`

Only the actual live/active state may use the bright green accent.

## 5. Visual Parameters

Section header:

`👁️ VISUAL PARAMETERS`

Four primary controls:

- `☀️ BRIGHTNESS`
- `◐ CONTRAST`
- `🌗 GAMMA`
- `🎨 SATURATION`

Each row contains:

1. semantic emoji/icon and label;
2. wide thin slider;
3. numeric value in monospaced text;
4. reset-one-parameter action (`↺`).

Example:

`☀️ Brightness   ─────────●────────   0.50   ↺`

### 5.1 Slider visual rule

Night / Level Black:

- inactive track: graphite/steel gray;
- active track: off-white/light gray;
- thumb: compact light neutral control.

Day / Clean Lab:

- inactive track: pale steel gray;
- active track: TerraGroup-like cyan/blue;
- thumb: dark or blue-accented neutral control.

The XRAT green is **not** used for ordinary slider progress.

### 5.2 Reset behavior

- clicking `↺` resets that single parameter;
- double-clicking the parameter label may retain the upstream quick-reset shortcut;
- tooltip states exactly what will reset.

Changes save automatically. No Save/Apply button is shown.

When the selected profile is currently live, slider changes preview immediately through the normal profile application path.

A lightweight acknowledgement may appear briefly:

`✅ PARAMETERS SAVED`

## 6. Profile Tools

Section:

`🧪 PROFILE TOOLS`

Actions:

- `🧬 COPY SETTINGS FROM...`
- `🔄 RESET ALL`

### 6.1 Copy settings popup

Shows available profiles with their emoji marks.

Copies only visual values:

- brightness;
- contrast;
- gamma;
- saturation.

It does **not** copy:

- profile name;
- emoji;
- enabled state;
- target processes;
- display selection;
- profile ID.

Copying produces a compact confirmation toast such as:

`🧪 PROFILE PARAMETERS CLONED`

## 7. Displays

Section:

`🖥️ DISPLAYS`

Displays use a checkbox list, not a single dropdown.

Example:

- `☑ DISPLAY 1   PRIMARY`
  - `2560×1440 · 165 Hz`
  - `\\.\DISPLAY1`
- `☐ DISPLAY 2`
  - `1920×1080 · 60 Hz`
  - `\\.\DISPLAY2`

Rules:

- multiple monitors may be selected;
- at least one display must remain selected for an enabled profile;
- `PRIMARY` is a compact metadata badge;
- technical IDs are monospaced and low contrast;
- disconnected known displays may appear as `OFFLINE` rather than being silently deleted;
- each selected monitor's original desktop state must be restored independently.

Optional compact actions:

- `SELECT ALL`
- `PRIMARY ONLY`

These are tertiary text actions, not large buttons.

## 8. Target Processes

Section:

`🎯 TARGET PROCESSES`

Each process row shows the executable identity and a remove action.

Example:

- `EscapeFromTarkov.exe    ✕`
- `EscapeFromTarkov_BE.exe ✕`

Action:

`➕ ADD PROCESS`

Adding offers:

- `🎮 Choose running application`
- `📁 Browse for .exe`

The user should rarely need to type a process name manually.

## 9. Add Game Flow

`➕ ADD GAME` opens a short two-step modal flow rather than a large wizard.

### Step 1 — choose source

Header:

`➕ ADD GAME`  
`REGISTER NEW TEST SUBJECT`

Choices:

- `🎮 RUNNING APPLICATION` — choose from currently running apps;
- `📁 BROWSE FOR .EXE` — select an executable manually.

Running-app list shows friendly product/window name prominently and `.exe` in smaller technical text.

A search field filters the list.

### Step 2 — profile setup

Fields:

- `🎮 NAME`
- `😀 PROFILE EMOJI`
- `🎯 TARGET PROCESSES`
- `🖥️ DISPLAYS`
- `🧪 STARTING PARAMETERS`

Starting parameters choices:

- Default
- Copy from an existing profile

Primary display is preselected by default.

After creation, close the modal and show:

`🧪 TEST SUBJECT REGISTERED`  
`Profile ready for XRAT tracing.`

Do not add a separate success page.

## 10. Emoji System

Emoji are a **semantic navigation layer**, not merely rare decoration.

Use polished embedded 3D emoji-style images anywhere they materially improve visual differentiation, including:

- 🎮 profiles/games;
- 🎯 processes;
- 👁️ visual settings;
- ☀️ brightness;
- ◐ contrast (may use a custom monochrome symbol if no suitable 3D asset exists);
- 🌗 gamma;
- 🎨 saturation;
- 🖥️ displays;
- 🧪 lab/profile tools;
- 🧬 copy/clone;
- ➕ add;
- 📁 browse;
- ⚙️ settings;
- 🚀 startup;
- 🔔 notifications;
- 📤 export;
- 📥 import;
- 📋 diagnostics;
- 🔄 reset/update;
- 🗑️ delete;
- ℹ️ About;
- ✅ success;
- ⚠️ warning;
- ❌ error.

The desired feel is similar to polished Apple-style emoji: dimensional, readable, friendly. Apple artwork itself must not be redistributed. Use a legally compatible embedded asset set with license verification, such as Microsoft Fluent Emoji 3D where appropriate.

Rules:

- emoji reinforce text; they never replace essential text labels;
- consistent asset rendering across Windows versions is preferred over system emoji fonts;
- typical section size: 18–22 px;
- profile-list size: 22–26 px;
- avoid emoji in dense technical annotation rows where they add noise.

## 11. Settings Screen

Settings replaces the right workspace while the left sidebar and top global bar remain visible.

Header:

`⚙️ SETTINGS`  
`SYSTEM CONFIGURATION`

### 11.1 Startup

`🚀 STARTUP`

- Launch RAT VISION with Windows
- Start minimized to tray

### 11.2 Window behavior

`🪟 WINDOW BEHAVIOR`

- Closing the window minimizes to tray
- Show window on profile activation — default OFF

### 11.3 Notifications

`🔔 NOTIFICATIONS`

- Show important notifications
- Notify when a game profile activates — default OFF
- Notify on errors — default ON

Avoid activation spam by default.

### 11.4 Profile data

`🧪 PROFILE DATA`

- `📤 EXPORT PROFILES`
- `📥 IMPORT PROFILES`
- `🔄 RESTORE DEFAULT PROFILES`

Export format is a single portable configuration file suitable for backup/migration.

### 11.5 Appearance

`🎨 APPEARANCE`

Theme options:

- `🖥️ Follow Windows`
- `☀️ Day // Clean Lab`
- `🌙 Night // Level Black`

Default: **Night // Level Black**.

Additional presentation toggles may include:

- subtle interface texture;
- 3D emoji.

If 3D emoji are disabled, replace them with consistent monochrome semantic icons without changing layout.

### 11.6 Diagnostics

`📋 SYSTEM STATUS`

Shows at minimum:

- GPU model/vendor;
- number of displays;
- foreground-hook state;
- NVIDIA/NvAPI capability state when relevant;
- XRAT global state;
- current foreground process;
- application version.

Actions:

- Copy diagnostics
- Open logs

## 12. Updates Placeholder

Settings includes a reserved section now even though update checking is not implemented in v1.

`🔄 UPDATES`

Shows:

- Current version
- Update channel: Stable
- `🔄 CHECK FOR UPDATES`

Until the update backend/service exists, clicking the button produces an honest informational message:

`🧪 UPDATE PROTOCOL NOT CONNECTED`  
`Automatic update checks will be added in a future build.`

Architecture must reserve an `IUpdateService`/equivalent abstraction so later implementation does not require redesigning the Settings UI.

Future top-bar update status may appear beside the version, e.g. `⬆ UPDATE AVAILABLE`, using neutral/amber treatment rather than XRAT green.

## 13. About

About is part of Settings rather than a top-level navigation destination.

Example:

`🐀 RAT VISION`  
`v1.0.0`

`See what the rat sees.`

`🧪 XRAT TRACING`  
`Experimental Rodent Visual Enhancement Technology`

Optional footer joke:

`Powered by questionable research.`

Also include:

- upstream `tarkov-settings` attribution;
- licenses;
- GitHub/project link when available.

## 14. Tray Experience

Tray icon uses the approved first-concept rat-head character simplified for 16–24 px.

The rat remains monochrome in both states.

### OFF

- monochrome rat;
- separate lower-right dark-gray hollow lamp `○`;
- no bright green glow.

### ON / waiting

- same rat;
- separate lower-right bright green filled lamp `●`;
- small soft night-vision-like green glow around the lamp.

No third `profile active` tray state is required.

### 14.1 Tray menu

At minimum:

- `🐀 RAT VISION v1.0.0`
- global `XRAT TRACING` enabled/disabled command/status
- `🪟 Open RAT VISION`
- `⚙️ Settings`
- `☕ Buy me a coffee`
- `❌ Exit`

Profiles may be listed as nonessential contextual items if useful, but must not turn the tray menu into a full profile editor.

## 15. Theme System

Themes are two expressions of the same design system. Layout, typography, spacing, emoji positions, and control geometry do not change between themes.

### 15.1 Night // Level Black

Mood: covert laboratory / black division.

Palette direction:

- near-black application background;
- graphite panels;
- off-white primary text;
- steel-gray secondary text and rules;
- bright XRAT green only for powered/active status.

### 15.2 Day // Clean Lab

Mood: ordinary clean TerraGroup-like public laboratory identity.

Base palette target:

- application background: approximately `#F3F5F6`;
- panels: `#FFFFFF`;
- primary text: approximately `#17191B`;
- secondary text: approximately `#616A70`;
- borders: approximately `#CCD4D8`;
- primary cyan/blue accent: approximately `#39AEEA`;
- pale cyan support: approximately `#E8F6FB`.

Exact production color values should be tuned against visual references during implementation because no authoritative official HEX specification is assumed.

The XRAT status green remains separate from the blue corporate accent.

### 15.3 Theme shortcut

Top bar contains one icon button:

- Night mode shows `☀️` with tooltip `Switch to Clean Lab`;
- Day mode shows `🌙` with tooltip `Switch to Level Black`.

Settings provides the full three-option theme selection including Follow Windows.

## 16. Controls

### 16.1 Toggles

Compact instrument-like toggles rather than oversized platform-default switches.

Always pair visual state with `ON` / `OFF` text.

### 16.2 Checkboxes

Large enough for reliable pointer use.

Selected monitor checkbox:

- Night: white/off-white checked state;
- Day: cyan/blue checked state.

Do not use XRAT green for ordinary checkboxes.

### 16.3 Buttons

Three levels:

Primary:

- Add Game / Create Profile / equivalent high-level action.

Secondary:

- Copy Settings / Reset / Browse.

Danger:

- Delete Profile.

Danger red appears mainly on hover/confirmation, not as a permanent giant red block.

### 16.4 Popovers

Use compact lab-panel popovers with thin rules/borders instead of default-looking system dropdown menus where custom presentation materially improves clarity.

### 16.5 Modals

Small, focused, low-drama modal windows.

Example:

`⚠️ DELETE PROFILE?`  
`Remove “Hunt: Showdown” from RAT VISION?`  
`The game itself will not be modified.`

Actions: Cancel / Delete.

### 16.6 Toasts

Short nonblocking notifications bottom-right.

Examples:

- `✅ PARAMETERS SAVED`
- `🧪 TEST SUBJECT REGISTERED`
- `⚠️ DISPLAY UNAVAILABLE`

## 17. Spacing and Geometry

Use an 8 px spacing system:

- 8 px micro spacing;
- 16 px standard component spacing;
- 24 px section padding;
- 28–32 px between major sections.

Cards/panels should feel technical and restrained:

- small corner radius approximately 4–6 px;
- thin borders;
- very limited shadow;
- no oversized pill-shaped cards everywhere;
- no glassmorphism overload.

## 18. Typography

Three roles:

1. tall/condensed uppercase display face for brand and major section headers;
2. neutral readable grotesk/sans for normal interface copy;
3. monospaced technical face for `.exe`, display IDs, versions, diagnostics, profile IDs, and lab annotations.

Do not use the display face for all body text.

## 19. Branding Details

Main logo/large identity:

- first-concept wild/stencil monochrome rat head;
- strong RAT VISION wordmark;
- optic/lens idea may be incorporated into `VISION` in large branding;
- the tray state is still represented by the separate lamp, not by recoloring the entire rat.

Secondary protocol labels can use:

- `XRAT TRACING // ENABLED`
- `TURN ON XRAT TRACING`
- `XRAT-VS/01`

Do not rename the product XRAT VISION; the product remains RAT VISION.

## 20. Final Main-Screen Reference

Conceptual structure:

```text
┌────────────────────────────────────────────────────────────────────────────┐
│ RAT VISION v1.0.0        VISUAL SYSTEMS // INTERNAL PROTOCOL   ☀️  ● [ON] │
│                                                           XRAT TRACING     │
├──────────────────────┬─────────────────────────────────────────────────────┤
│ 🎮 GAME PROFILES    │ PROFILE // 01                                      │
│                     │ 🐀 ESCAPE FROM TARKOV             PROFILE [ON]      │
│ 🐀 Tarkov           │ 🎯 EscapeFromTarkov.exe                            │
│ ⚔️ Tarkov: Arena    │ ● LIVE // PROFILE CURRENTLY APPLIED                │
│ 🤠 Hunt: Showdown   │                                                     │
│                     │ 👁️ VISUAL PARAMETERS                               │
│ ➕ ADD GAME         │ ☀️ Brightness  ───────●────── 0.50 ↺               │
│                     │ ◐ Contrast    ─────────●──── 0.55 ↺                │
│                     │ 🌗 Gamma       ──────●─────── 1.10 ↺                │
│                     │ 🎨 Saturation  ──────────●── 72   ↺                 │
│                     │                                                     │
│                     │ 🧪 PROFILE TOOLS                                    │
│                     │ [🧬 Copy settings from...] [🔄 Reset all]           │
│                     │                                                     │
│                     │ 🖥️ DISPLAYS                                         │
│                     │ ☑ DISPLAY 1 · PRIMARY · 2560×1440 · 165 Hz          │
│                     │ ☐ DISPLAY 2 · 1920×1080 · 60 Hz                     │
│                     │                                                     │
│                     │ 🎯 TARGET PROCESSES                                 │
│                     │ EscapeFromTarkov.exe                         ✕       │
│                     │ [➕ Add process]                                    │
│                     │                                                     │
│ ☕ Buy me a coffee │ 🧬 XRAT-VS/01 // PROFILE READY                       │
│ ⚙️ SETTINGS        │                                      🗑️ Delete      │
└──────────────────────┴─────────────────────────────────────────────────────┘
```

## 21. Settled UI Decisions

The following are approved design directions and should not be casually changed during implementation:

- master/detail main screen;
- fixed top bar and sidebar, scrollable right workspace;
- sticky `Buy me a coffee` and Settings actions;
- profile-specific visual values;
- multi-monitor selection through checkboxes;
- multiple executable targets per profile;
- two-step Add Game flow;
- automatic saving;
- wide parameter sliders with visible numeric values and per-row reset;
- profile copy copies visual parameters only;
- global XRAT state always visible;
- tray has two states, differentiated by a separate indicator lamp;
- Night // Level Black and Day // Clean Lab themes;
- Follow Windows option in Settings;
- Clean Lab uses white/cold gray + cyan/blue; XRAT green remains functional and separate;
- theme shortcut always available in top bar;
- semantic 3D emoji used wherever they materially improve visual recognition;
- update-check UI placeholder exists even before update logic;
- About lives inside Settings;
- version visible in title/About/diagnostics;
- three white stripes remain a subtle Easter egg only.

