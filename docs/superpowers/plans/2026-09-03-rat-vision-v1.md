# RAT VISION v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build RAT VISION as a modern .NET 8 WPF desktop application that applies separate visual profiles per foreground game, supports multiple target executables and displays, exposes the approved TerraGroup-inspired Day/Night UI, and lives safely in the Windows tray.

**Architecture:** Create a new SDK-style solution beside the upstream WinForms code, split into `RatVision.Core` (domain/policy), `RatVision.Windows` (Win32, gamma, NVAPI, discovery, startup), and `RatVision.App` (WPF/MVVM/tray/UI). A `ProfileActivationCoordinator` connects foreground-process events to profile matching and an `IColorService`; hardware APIs stay behind interfaces so all matching, persistence, copy, global toggle, and restore behavior can be tested without a GPU or monitor.

**Tech Stack:** .NET 8, WPF, WPF-UI 4.3.0, CommunityToolkit.Mvvm 8.4.2, H.NotifyIcon.Wpf 2.4.1, NvAPIWrapper.Net 0.8.1.101, Microsoft.Extensions.DependencyInjection 8.0.1, System.Text.Json, xUnit 2.9.0.

**Spec:** `docs/superpowers/specs/2026-09-03-rat-vision-design.md` and `docs/superpowers/specs/2026-09-03-rat-vision-ui-blueprint.md`

## Global Constraints

- Target Windows x64 and `.NET 8`; the shipping app is `net8.0-windows`.
- Product name is **RAT VISION**; `XRAT TRACING` is a secondary fictional protocol name only.
- Window title, About, and diagnostics must expose the running semantic version, beginning with `v1.0.0`.
- Default profiles: Escape from Tarkov, Escape from Tarkov: Arena, Hunt: Showdown.
- One profile may contain multiple process names and multiple selected displays.
- `Copy settings from...` copies only brightness, contrast, gamma, and saturation.
- Global OFF restores every modified display immediately but keeps RAT VISION and foreground monitoring alive.
- Leaving a matching foreground process restores each selected display to the captured desktop state.
- Tray has exactly two global-state visuals in v1: OFF = hollow/dark lamp; ON = bright green lamp. The rat mark itself remains monochrome.
- Night theme is `Night // Level Black`; Day theme is `Day // Clean Lab`; `Follow Windows` is also selectable.
- Clean Lab uses cold white/gray plus cyan/blue around `#39AEEA`; XRAT green remains a separate functional status color.
- 3D emoji are semantic navigation aids. Use a curated legal asset set, not Apple-owned emoji artwork; package the selected assets inside the application.
- `☕ Buy me a coffee` is always visible in the fixed left sidebar and also appears in the tray menu; target URL is `https://dalink.to/bazaz`.
- Settings contains a visible `Check for updates` control, but v1 performs no network update check and returns the approved `UPDATE PROTOCOL NOT CONNECTED` message.
- Preserve upstream attribution and the existing LGPL-2.1 license obligations for reused code.
- Do not introduce game-file modification, injection, overlays, anti-cheat interaction, or process memory access.
- Use TDD for Core behavior and adapter boundaries; hardware-specific tests are opt-in/manual and must never run by default in CI.

---

## File Structure Locked for Implementation

```text
RatVision.sln
Directory.Build.props
Directory.Packages.props
src/
  RatVision.Core/
    RatVision.Core.csproj
    Models/
      AppSettings.cs
      GameProfile.cs
      VisualParameters.cs
      DisplayInfo.cs
      ForegroundProcessInfo.cs
      RuntimeStatus.cs
      ThemePreference.cs
      ColorCapabilities.cs
    Services/
      ISettingsService.cs
      IProfileService.cs
      IForegroundWindowService.cs
      IColorService.cs
      IDisplayDiscoveryService.cs
      IApplicationDiscoveryService.cs
      IStartupService.cs
      IThemeService.cs
      IUpdateService.cs
      IDiagnosticsService.cs
      ILogService.cs
      ProfileService.cs
      SettingsService.cs
      ProfileActivationCoordinator.cs
      UpdateService.cs
    Defaults/
      BuiltInProfiles.cs
  RatVision.Windows/
    RatVision.Windows.csproj
    Foreground/
      Win32ForegroundWindowService.cs
      NativeWindowMethods.cs
    Display/
      WindowsDisplayDiscoveryService.cs
      GammaLutCalculator.cs
      GammaRampBackend.cs
      NvidiaSaturationBackend.cs
      WindowsColorService.cs
      NativeDisplayMethods.cs
    Apps/
      WindowsApplicationDiscoveryService.cs
    Startup/
      WindowsStartupService.cs
    Diagnostics/
      WindowsDiagnosticsService.cs
    Logging/
      FileLogService.cs
  RatVision.App/
    RatVision.App.csproj
    App.xaml
    App.xaml.cs
    MainWindow.xaml
    MainWindow.xaml.cs
    ViewModels/
      MainWindowViewModel.cs
      ProfileWorkspaceViewModel.cs
      GameProfileItemViewModel.cs
      AddGameViewModel.cs
      SettingsViewModel.cs
    Views/
      ProfileWorkspaceView.xaml
      SettingsView.xaml
      Dialogs/AddGameDialog.xaml
      Dialogs/CopyProfileDialog.xaml
      Dialogs/DeleteProfileDialog.xaml
    Services/
      ThemeService.cs
      TrayService.cs
      DialogService.cs
      ShellService.cs
      EmojiAssetCatalog.cs
    Themes/
      ThemeTokens.xaml
      LevelBlack.xaml
      CleanLab.xaml
      Controls.xaml
    Assets/
      Brand/
      Tray/
      Emoji/
    Properties/
      PublishProfiles/WinX64.pubxml
  RatVision.Tests/
    RatVision.Tests.csproj
    Defaults/BuiltInProfilesTests.cs
    Settings/SettingsServiceTests.cs
    Profiles/ProfileServiceTests.cs
    Activation/ProfileActivationCoordinatorTests.cs
    Display/GammaLutCalculatorTests.cs
    Display/WindowsColorServiceTests.cs
    ViewModels/MainWindowViewModelTests.cs
    ViewModels/ProfileWorkspaceViewModelTests.cs
    ViewModels/AddGameViewModelTests.cs
    ViewModels/SettingsViewModelTests.cs
    TestDoubles/
      InMemorySettingsStore.cs
      ManualForegroundWindowService.cs
      RecordingColorService.cs
      FakeDisplayDiscoveryService.cs
      FakeApplicationDiscoveryService.cs
README.md
THIRD_PARTY_NOTICES.md
```

The old `App/`, `Display/`, `GPU/`, `Setting/`, `tarkov-settings.csproj`, `packages.config`, Fody files, and WinForms resources remain untouched until the final migration-cleanup task so behavior can be compared during porting.

---

### Task 1: Establish the .NET 8 Solution and Dependency Baseline

**Files:**
- Create: `RatVision.sln`
- Create: `Directory.Build.props`
- Create: `Directory.Packages.props`
- Create: `src/RatVision.Core/RatVision.Core.csproj`
- Create: `src/RatVision.Windows/RatVision.Windows.csproj`
- Create: `src/RatVision.App/RatVision.App.csproj`
- Create: `src/RatVision.Tests/RatVision.Tests.csproj`
- Create: minimal `src/RatVision.App/App.xaml`, `App.xaml.cs`, `MainWindow.xaml`, `MainWindow.xaml.cs`
- Test: `src/RatVision.Tests/SmokeTests.cs`

**Interfaces:**
- Produces the project references and package baseline used by every later task.
- `RatVision.App` references `RatVision.Core` and `RatVision.Windows`.
- `RatVision.Windows` references `RatVision.Core`.
- `RatVision.Tests` references `RatVision.Core`, `RatVision.Windows`, and `RatVision.App`.

- [ ] **Step 1: Add a failing smoke test that names the new product assembly**

```csharp
using Xunit;

namespace RatVision.Tests;

public sealed class SmokeTests
{
    [Fact]
    public void CoreAssemblyUsesRatVisionName()
    {
        Assert.Equal("RatVision.Core", typeof(RatVision.Core.AssemblyMarker).Assembly.GetName().Name);
    }
}
```

Run: `dotnet test src/RatVision.Tests/RatVision.Tests.csproj --no-restore`

Expected: FAIL because the new projects and `AssemblyMarker` do not exist.

- [ ] **Step 2: Create the SDK-style projects, package pins, and x64 defaults**

`Directory.Build.props`:

```xml
<Project>
  <PropertyGroup>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
    <LangVersion>latest</LangVersion>
    <TreatWarningsAsErrors>true</TreatWarningsAsErrors>
    <Platforms>x64</Platforms>
  </PropertyGroup>
</Project>
```

`Directory.Packages.props`:

```xml
<Project>
  <PropertyGroup>
    <ManagePackageVersionsCentrally>true</ManagePackageVersionsCentrally>
  </PropertyGroup>
  <ItemGroup>
    <PackageVersion Include="WPF-UI" Version="4.3.0" />
    <PackageVersion Include="CommunityToolkit.Mvvm" Version="8.4.2" />
    <PackageVersion Include="H.NotifyIcon.Wpf" Version="2.4.1" />
    <PackageVersion Include="NvAPIWrapper.Net" Version="0.8.1.101" />
    <PackageVersion Include="Microsoft.Extensions.DependencyInjection" Version="8.0.1" />
    <PackageVersion Include="System.Management" Version="8.0.0" />
    <PackageVersion Include="xunit" Version="2.9.0" />
    <PackageVersion Include="xunit.runner.visualstudio" Version="2.8.2" />
    <PackageVersion Include="Microsoft.NET.Test.Sdk" Version="17.14.1" />
    <PackageVersion Include="coverlet.collector" Version="6.0.4" />
  </ItemGroup>
</Project>
```

Use `TargetFramework=net8.0` for Core/Tests and `TargetFramework=net8.0-windows` for Windows/App. Set `<UseWPF>true</UseWPF>` in App and `<UseWindowsForms>true</UseWindowsForms>` in Windows for `Screen`-based monitor enumeration only.

- [ ] **Step 3: Add the marker and minimal WPF shell**

```csharp
namespace RatVision.Core;
public sealed class AssemblyMarker;
```

`MainWindow.xaml` must render only `RAT VISION v1.0.0` at this stage. Do not start styling or hardware work in this task.

- [ ] **Step 4: Restore, build, and run tests**

Run:

```bash
dotnet restore RatVision.sln
dotnet build RatVision.sln -c Debug -p:Platform=x64
dotnet test RatVision.sln -c Debug -p:Platform=x64 --no-build
```

Expected: build succeeds with zero warnings and `SmokeTests.CoreAssemblyUsesRatVisionName` passes.

- [ ] **Step 5: Commit**

```bash
git add RatVision.sln Directory.Build.props Directory.Packages.props src
git commit -m "build: establish RAT VISION net8 solution"
```

---

### Task 2: Define Settings Schema, Built-in Profiles, Persistence, and Upstream Migration

**Files:**
- Create: `src/RatVision.Core/Models/AppSettings.cs`
- Create: `src/RatVision.Core/Models/GameProfile.cs`
- Create: `src/RatVision.Core/Models/VisualParameters.cs`
- Create: `src/RatVision.Core/Models/ThemePreference.cs`
- Create: `src/RatVision.Core/Defaults/BuiltInProfiles.cs`
- Create: `src/RatVision.Core/Services/ISettingsService.cs`
- Create: `src/RatVision.Core/Services/SettingsService.cs`
- Test: `src/RatVision.Tests/Defaults/BuiltInProfilesTests.cs`
- Test: `src/RatVision.Tests/Settings/SettingsServiceTests.cs`
- Test helper: `src/RatVision.Tests/TestDoubles/InMemorySettingsStore.cs`

**Interfaces:**
- Produces `AppSettings Current`, `Task InitializeAsync()`, `Task SaveAsync()`, `Task ImportAsync(Stream)`, and `Task ExportAsync(Stream)` via `ISettingsService`.
- Produces `GameProfile`, `VisualParameters`, and `ThemePreference` used by all remaining tasks.

- [ ] **Step 1: Write failing tests for defaults and copy-safe schema values**

```csharp
[Fact]
public void CreateDefaults_ReturnsThreeExpectedProfiles()
{
    var profiles = BuiltInProfiles.Create();
    Assert.Collection(profiles,
        p => Assert.Equal("Escape from Tarkov", p.Name),
        p => Assert.Equal("Escape from Tarkov: Arena", p.Name),
        p => Assert.Equal("Hunt: Showdown", p.Name));
}

[Fact]
public void HuntDefault_IncludesCurrentRuntimeExecutable()
{
    var hunt = BuiltInProfiles.Create().Single(p => p.BuiltInId == "hunt-showdown");
    Assert.Contains(hunt.ProcessNames, p => string.Equals(p, "HuntGame.exe", StringComparison.OrdinalIgnoreCase));
}
```

- [ ] **Step 2: Add the exact schema**

```csharp
public enum ThemePreference { FollowWindows, CleanLab, LevelBlack }

public sealed record VisualParameters(
    double Brightness = 0.5,
    double Contrast = 0.5,
    double Gamma = 1.0,
    int Saturation = 0);

public sealed class GameProfile
{
    public Guid Id { get; init; } = Guid.NewGuid();
    public string Name { get; set; } = string.Empty;
    public string EmojiKey { get; set; } = "gamepad";
    public bool Enabled { get; set; } = true;
    public List<string> ProcessNames { get; init; } = [];
    public List<string> DisplayIds { get; init; } = [];
    public VisualParameters Visuals { get; set; } = new();
    public string? BuiltInId { get; init; }
}

public sealed class AppSettings
{
    public const int CurrentSchemaVersion = 2;
    public int SchemaVersion { get; set; } = CurrentSchemaVersion;
    public bool GlobalEnabled { get; set; } = true;
    public ThemePreference Theme { get; set; } = ThemePreference.LevelBlack;
    public bool LaunchAtStartup { get; set; }
    public bool StartMinimized { get; set; }
    public bool CloseToTray { get; set; } = true;
    public bool ShowActivationNotifications { get; set; }
    public bool ShowErrorNotifications { get; set; } = true;
    public bool Use3DEmoji { get; set; } = true;
    public bool UseSubtleTexture { get; set; } = true;
    public List<GameProfile> Profiles { get; set; } = [];
}
```

- [ ] **Step 3: Implement JSON persistence under LocalAppData and upstream migration**

`SettingsService` stores the main file at `%LOCALAPPDATA%\RatVision\settings.json`. On first initialization:

1. If the new file exists, deserialize it.
2. Else if `./settings.json` contains the upstream fields `brightness`, `contrast`, `gamma`, `saturation`, `pTargets`, `display`, migrate those values into one `Escape from Tarkov` profile, copy the old file to `%LOCALAPPDATA%\RatVision\settings.upstream.backup.json`, then save schema v2.
3. Else create the three built-in profiles.
4. If JSON cannot be parsed, rename it to `settings.corrupt.<UTC timestamp>.json`, create defaults, and save a valid file.

Use `System.Text.Json` with `WriteIndented = true` and `JsonStringEnumConverter`.

- [ ] **Step 4: Test round-trip, corrupt recovery, and old-settings migration**

Tests must assert that process names survive case/punctuation, `GlobalEnabled` persists, and migration preserves the upstream target process set and selected display.

Run: `dotnet test src/RatVision.Tests/RatVision.Tests.csproj --filter "FullyQualifiedName~Settings|FullyQualifiedName~BuiltInProfiles"`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/RatVision.Core src/RatVision.Tests
git commit -m "feat: add RAT VISION profile settings schema"
```

---

### Task 3: Implement Profile CRUD, Matching, Copy, and Automatic Save Semantics

**Files:**
- Create: `src/RatVision.Core/Services/IProfileService.cs`
- Create: `src/RatVision.Core/Services/ProfileService.cs`
- Test: `src/RatVision.Tests/Profiles/ProfileServiceTests.cs`

**Interfaces:**
- Consumes: `ISettingsService`, `GameProfile`, `VisualParameters`.
- Produces:

```csharp
public interface IProfileService
{
    IReadOnlyList<GameProfile> Profiles { get; }
    GameProfile? FindMatching(string processName);
    GameProfile Add(string name, string emojiKey, IEnumerable<string> processes, IEnumerable<string> displays);
    bool Remove(Guid profileId);
    void SetEnabled(Guid profileId, bool enabled);
    void SetProcesses(Guid profileId, IEnumerable<string> processes);
    void SetDisplays(Guid profileId, IEnumerable<string> displays);
    void SetVisuals(Guid profileId, VisualParameters visuals);
    void CopyVisuals(Guid sourceProfileId, Guid targetProfileId);
    Task FlushAsync();
    event EventHandler? ProfilesChanged;
}
```

- [ ] **Step 1: Write failing matching and copy tests**

```csharp
[Fact]
public void FindMatching_IsCaseInsensitiveAndIgnoresDisabledProfiles()
{
    var service = CreateService(
        Profile("EFT", true, "EscapeFromTarkov.exe"),
        Profile("Arena", false, "Arena.exe"));

    Assert.Equal("EFT", service.FindMatching("escapefromtarkov.EXE")?.Name);
    Assert.Null(service.FindMatching("ARENA.EXE"));
}

[Fact]
public void CopyVisuals_DoesNotCopyIdentityOrTargets()
{
    var source = Profile("Source", true, "source.exe", visuals: new(0.7, 0.8, 1.2, 80));
    var target = Profile("Target", false, "target.exe", visuals: new());
    var service = CreateService(source, target);

    service.CopyVisuals(source.Id, target.Id);

    Assert.Equal(source.Visuals, target.Visuals);
    Assert.Equal("Target", target.Name);
    Assert.Contains("target.exe", target.ProcessNames);
    Assert.False(target.Enabled);
}
```

- [ ] **Step 2: Implement normalization and CRUD**

Normalize process names with `Path.GetFileName(value.Trim())`; remove blanks and duplicates using `StringComparer.OrdinalIgnoreCase`. Reject an add operation with zero valid process names. Keep display IDs distinct with `StringComparer.OrdinalIgnoreCase`.

- [ ] **Step 3: Implement debounced autosave**

Every mutation schedules `ISettingsService.SaveAsync()` through a single 250 ms debounce window. `FlushAsync()` waits for the pending save and is called before app exit. Do not write a settings file for every slider tick.

- [ ] **Step 4: Run the profile test suite**

Run: `dotnet test src/RatVision.Tests/RatVision.Tests.csproj --filter FullyQualifiedName~ProfileService`

Expected: PASS for case-insensitive matching, disabled filtering, visual-only copy, deduplication, remove, and autosave flush.

- [ ] **Step 5: Commit**

```bash
git add src/RatVision.Core/Services src/RatVision.Tests/Profiles
git commit -m "feat: add profile matching and autosave"
```

---

### Task 4: Port Foreground Window Detection Behind a Safe Service

**Files:**
- Create: `src/RatVision.Core/Models/ForegroundProcessInfo.cs`
- Create: `src/RatVision.Core/Services/IForegroundWindowService.cs`
- Create: `src/RatVision.Windows/Foreground/NativeWindowMethods.cs`
- Create: `src/RatVision.Windows/Foreground/Win32ForegroundWindowService.cs`
- Create: `src/RatVision.Tests/TestDoubles/ManualForegroundWindowService.cs`
- Test: `src/RatVision.Tests/Activation/ForegroundMatchingContractTests.cs`

**Interfaces:**

```csharp
public sealed record ForegroundProcessInfo(int ProcessId, string ProcessName, string? ExecutablePath);

public interface IForegroundWindowService : IDisposable
{
    ForegroundProcessInfo? Current { get; }
    event EventHandler<ForegroundProcessInfo?>? Changed;
    void Start();
    void Stop();
}
```

- [ ] **Step 1: Write a failing contract test for process-name normalization**

```csharp
[Theory]
[InlineData("EscapeFromTarkov", "EscapeFromTarkov.exe")]
[InlineData("HuntGame.exe", "HuntGame.exe")]
public void NormalizeProcessName_AlwaysReturnsExeName(string input, string expected)
{
    Assert.Equal(expected, Win32ForegroundWindowService.NormalizeProcessName(input));
}
```

- [ ] **Step 2: Port the WinEvent hook without WPF dependencies**

Use `SetWinEventHook(EVENT_SYSTEM_FOREGROUND, EVENT_SYSTEM_FOREGROUND, ..., WINEVENT_OUTOFCONTEXT | WINEVENT_SKIPOWNPROCESS)`, `GetWindowThreadProcessId`, and `Process.GetProcessById`. Keep the delegate rooted in a private field for the full service lifetime. Never call `ToLower()` on possibly null values; all matching is delegated to `IProfileService`.

- [ ] **Step 3: Make lifecycle idempotent**

Calling `Start()` twice installs one hook; calling `Stop()` repeatedly is safe. On callback errors or exited processes, publish `null` only when the previous foreground value was non-null, and log the exception through the later `ILogService` integration rather than showing UI from this class.

- [ ] **Step 4: Build and run non-hardware tests**

Run: `dotnet test src/RatVision.Tests/RatVision.Tests.csproj --filter FullyQualifiedName~Foreground`

Expected: PASS. No test should install a real WinEvent hook.

- [ ] **Step 5: Commit**

```bash
git add src/RatVision.Core/Models src/RatVision.Core/Services/IForegroundWindowService.cs src/RatVision.Windows/Foreground src/RatVision.Tests
git commit -m "feat: port foreground window monitoring"
```

---

### Task 5: Add Display Discovery and the Pure Gamma LUT Calculator

**Files:**
- Create: `src/RatVision.Core/Models/DisplayInfo.cs`
- Create: `src/RatVision.Core/Services/IDisplayDiscoveryService.cs`
- Create: `src/RatVision.Windows/Display/NativeDisplayMethods.cs`
- Create: `src/RatVision.Windows/Display/WindowsDisplayDiscoveryService.cs`
- Create: `src/RatVision.Windows/Display/GammaLutCalculator.cs`
- Create: `src/RatVision.Tests/Display/GammaLutCalculatorTests.cs`
- Create: `src/RatVision.Tests/TestDoubles/FakeDisplayDiscoveryService.cs`

**Interfaces:**

```csharp
public sealed record DisplayInfo(
    string Id,
    string Name,
    bool IsPrimary,
    int Width,
    int Height,
    int RefreshRateHz,
    bool IsOnline);

public interface IDisplayDiscoveryService
{
    IReadOnlyList<DisplayInfo> GetDisplays();
}
```

- [ ] **Step 1: Write failing LUT tests based on upstream behavior**

```csharp
[Fact]
public void NeutralSettings_ProduceLinearRamp()
{
    var lut = GammaLutCalculator.Calculate(0.5, 0.5, 1.0);
    Assert.Equal(256, lut.Length);
    Assert.Equal((ushort)0, lut[0]);
    Assert.InRange(lut[128], (ushort)32760, (ushort)33000);
    Assert.Equal(ushort.MaxValue, lut[255]);
}

[Theory]
[InlineData(-1, 0.5, 1.0)]
[InlineData(2, 0.5, 1.0)]
[InlineData(0.5, 0.5, 99)]
public void OutOfRangeInputs_AreClamped(double brightness, double contrast, double gamma)
{
    var lut = GammaLutCalculator.Calculate(brightness, contrast, gamma);
    Assert.Equal(256, lut.Length);
}
```

- [ ] **Step 2: Port `CalculateLUT` unchanged in behavior, then make it pure**

Move the formula from upstream `ColorController.CalculateLUT` into `GammaLutCalculator.Calculate`. Keep brightness clamp `[0,1]`, contrast clamp `[0,1]`, gamma clamp `[0.4,2.8]`, and return exactly 256 `ushort` values.

- [ ] **Step 3: Implement multi-display discovery**

Use `System.Windows.Forms.Screen.AllScreens` for ID, primary flag, and bounds. Use Win32 `EnumDisplaySettings` for refresh rate. Return deterministic ordering: primary first, then `Id` ordinal-ignore-case. If a configured display is absent later, `SettingsService` keeps the stored ID; the discovery result simply omits it and the UI labels it offline from stored state.

- [ ] **Step 4: Run tests and build Windows adapter**

Run:

```bash
dotnet test src/RatVision.Tests/RatVision.Tests.csproj --filter FullyQualifiedName~GammaLut
dotnet build src/RatVision.Windows/RatVision.Windows.csproj -c Debug -p:Platform=x64
```

Expected: PASS and no warning from Win32 signatures.

- [ ] **Step 5: Commit**

```bash
git add src/RatVision.Core src/RatVision.Windows/Display src/RatVision.Tests
git commit -m "feat: add display discovery and gamma calculation"
```

---

### Task 6: Implement Multi-Monitor Gamma Sessions, NVIDIA Saturation, and Safe Restore

**Files:**
- Create: `src/RatVision.Core/Models/ColorCapabilities.cs`
- Create: `src/RatVision.Core/Services/IColorService.cs`
- Create: `src/RatVision.Windows/Display/GammaRampBackend.cs`
- Create: `src/RatVision.Windows/Display/NvidiaSaturationBackend.cs`
- Create: `src/RatVision.Windows/Display/WindowsColorService.cs`
- Test: `src/RatVision.Tests/Display/WindowsColorServiceTests.cs`

**Interfaces:**

```csharp
public sealed record ColorCapabilities(bool GammaSupported, bool SaturationSupported, string? SaturationUnavailableReason);

public interface IColorService : IAsyncDisposable
{
    ColorCapabilities Capabilities { get; }
    Task ApplyAsync(GameProfile profile, CancellationToken cancellationToken = default);
    Task RestoreAllAsync(CancellationToken cancellationToken = default);
}
```

Internal adapter seams:

```csharp
internal interface IGammaRampBackend
{
    Task<IGammaRampSession> StartAsync(string displayId, VisualParameters visuals, CancellationToken ct);
}

internal interface IGammaRampSession : IAsyncDisposable { }

internal interface ISaturationBackend
{
    bool IsSupported { get; }
    string? UnavailableReason { get; }
    Task SetAsync(string displayId, int level, CancellationToken ct);
    Task RestoreAsync(string displayId, CancellationToken ct);
}
```

- [ ] **Step 1: Write failing tests for apply-switch-restore behavior**

```csharp
[Fact]
public async Task SwitchingProfiles_DisposesOldDisplaySessionsBeforeApplyingNewOnes()
{
    var gamma = new RecordingGammaBackend();
    var saturation = new RecordingSaturationBackend();
    await using var service = new WindowsColorService(gamma, saturation);

    await service.ApplyAsync(Profile(displays: ["DISPLAY1"]));
    await service.ApplyAsync(Profile(displays: ["DISPLAY2"]));

    Assert.Equal(new[] { "start:DISPLAY1", "restore:DISPLAY1", "start:DISPLAY2" }, gamma.Events);
}

[Fact]
public async Task RestoreAll_RestoresEverySelectedDisplayAndSaturation()
{
    // apply to DISPLAY1 and DISPLAY2, restore, assert both backends restored once each
}
```

- [ ] **Step 2: Port gamma ramp capture/write with one session per display**

`GammaRampBackend.StartAsync` must:

1. `CreateDC` for the display.
2. Capture the original `RAMP` with `GetDeviceGammaRamp`.
3. Calculate the target LUT.
4. Start a cancellable loop that writes the same target ramp every 250 ms, preserving the upstream workaround.
5. On `DisposeAsync`, cancel the loop, write the captured original ramp once, then `DeleteDC`.

A session owns its HDC lifecycle; no HDC may outlive its session.

- [ ] **Step 3: Port NVAPI DVC through `NvAPIWrapper.Net`**

`NvidiaSaturationBackend` initializes NVAPI once, resolves a `DisplayHandle` for each Windows display ID, captures its starting DVC level before first modification, clamps requested saturation to the driver-reported min/max, and restores the captured level on profile stop. If initialization or display-handle resolution fails, mark saturation unsupported and keep gamma functional.

Do not show `MessageBox` from this adapter. Return capability state and log failures.

- [ ] **Step 4: Make `WindowsColorService` transactional**

Before applying a new profile, call `RestoreAllAsync`. Start sessions only for profile display IDs currently available. If one display fails, restore any sessions already started for that attempt, then rethrow a typed `ColorApplyException` containing the failing display ID. Saturation failure is nonfatal when gamma succeeded; expose it through diagnostics/capability state.

- [ ] **Step 5: Run fake-backend tests plus an opt-in NVIDIA smoke command**

Default:

```bash
dotnet test src/RatVision.Tests/RatVision.Tests.csproj --filter FullyQualifiedName~WindowsColorService
```

Manual on an NVIDIA development machine:

```powershell
$env:RATVISION_HARDWARE_TESTS="1"
dotnet test src/RatVision.Tests/RatVision.Tests.csproj --filter Category=Hardware
```

Expected default suite: PASS without changing the display. Manual smoke: apply a harmless profile to one selected test monitor and restore it before test exit.

- [ ] **Step 6: Commit**

```bash
git add src/RatVision.Core src/RatVision.Windows/Display src/RatVision.Tests/Display
git commit -m "feat: port safe multi-display color control"
```

---

### Task 7: Implement the Activation Coordinator and Global XRAT Toggle

**Files:**
- Create: `src/RatVision.Core/Models/RuntimeStatus.cs`
- Create: `src/RatVision.Core/Services/ProfileActivationCoordinator.cs`
- Create: `src/RatVision.Tests/TestDoubles/RecordingColorService.cs`
- Test: `src/RatVision.Tests/Activation/ProfileActivationCoordinatorTests.cs`

**Interfaces:**

```csharp
public sealed record RuntimeStatus(
    bool GlobalEnabled,
    string? ForegroundProcessName,
    Guid? ActiveProfileId,
    string StateText);

public sealed class ProfileActivationCoordinator : IAsyncDisposable
{
    public RuntimeStatus Status { get; }
    public event EventHandler<RuntimeStatus>? StatusChanged;
    public Task StartAsync();
    public Task SetGlobalEnabledAsync(bool enabled);
    public Task StopAsync();
}
```

- [ ] **Step 1: Write the full state-transition tests first**

```csharp
[Fact]
public async Task MatchingForeground_AppliesProfile_ThenDesktopRestoresOnLeave()
{
    var foreground = new ManualForegroundWindowService();
    var colors = new RecordingColorService();
    var coordinator = CreateCoordinator(foreground, colors, globalEnabled: true);
    await coordinator.StartAsync();

    foreground.Publish("EscapeFromTarkov.exe");
    await coordinator.WhenIdleAsync();
    foreground.Publish("explorer.exe");
    await coordinator.WhenIdleAsync();

    Assert.Equal(new[] { "apply:Escape from Tarkov", "restore" }, colors.Events);
}

[Fact]
public async Task GlobalOff_RestoresImmediately_AndPreventsFurtherApply()
{
    // publish matching process, set false, publish matching process again; assert restore and no second apply
}
```

- [ ] **Step 2: Serialize activation work**

Use a `SemaphoreSlim(1,1)` so rapid Alt+Tab events cannot overlap `ApplyAsync`/`RestoreAllAsync`. Coalesce duplicate foreground events for the same process. Maintain `ActiveProfileId` only after `ApplyAsync` completes successfully.

- [ ] **Step 3: Implement runtime status copy exactly**

States:

- global OFF: `XRAT TRACING // DISABLED`
- enabled, no target: `READY`
- enabled, configured process detected but not current matching foreground: `WAITING FOR FOCUS`
- matching foreground successfully applied: `LIVE // PROFILE CURRENTLY APPLIED`
- apply failure: `PROFILE ERROR`

Persist `GlobalEnabled` through `ISettingsService` when the user toggles it.

- [ ] **Step 4: Verify all transition tests**

Run: `dotnet test src/RatVision.Tests/RatVision.Tests.csproj --filter FullyQualifiedName~ProfileActivationCoordinator`

Expected: PASS including rapid process changes, profile disabled, global OFF, and failed apply restore.

- [ ] **Step 5: Commit**

```bash
git add src/RatVision.Core src/RatVision.Tests/Activation src/RatVision.Tests/TestDoubles
git commit -m "feat: coordinate foreground profiles and XRAT state"
```

---

### Task 8: Add Application Discovery, Startup, File Logging, Diagnostics, and Update Placeholder Services

**Files:**
- Create: `src/RatVision.Core/Services/IApplicationDiscoveryService.cs`
- Create: `src/RatVision.Core/Services/IStartupService.cs`
- Create: `src/RatVision.Core/Services/ILogService.cs`
- Create: `src/RatVision.Core/Services/IDiagnosticsService.cs`
- Create: `src/RatVision.Core/Services/IUpdateService.cs`
- Create: `src/RatVision.Core/Services/UpdateService.cs`
- Create: `src/RatVision.Windows/Apps/WindowsApplicationDiscoveryService.cs`
- Create: `src/RatVision.Windows/Startup/WindowsStartupService.cs`
- Create: `src/RatVision.Windows/Logging/FileLogService.cs`
- Create: `src/RatVision.Windows/Diagnostics/WindowsDiagnosticsService.cs`
- Create: `src/RatVision.Tests/TestDoubles/FakeApplicationDiscoveryService.cs`
- Test: `src/RatVision.Tests/Services/SupportServicesTests.cs`

**Interfaces:**

```csharp
public sealed record RunningApplication(int ProcessId, string DisplayName, string ProcessName, string? ExecutablePath);
public interface IApplicationDiscoveryService { IReadOnlyList<RunningApplication> GetRunningApplications(); }
public interface IStartupService { bool IsEnabled { get; } void SetEnabled(bool enabled); }
public interface ILogService { string LogDirectory { get; } void Info(string message); void Error(Exception exception, string message); }
public interface IDiagnosticsService { Task<string> BuildReportAsync(); }
public sealed record UpdateCheckResult(bool Connected, bool UpdateAvailable, string Message);
public interface IUpdateService { Task<UpdateCheckResult> CheckAsync(CancellationToken ct = default); }
```

- [ ] **Step 1: Write failing support-service contract tests**

Test that `UpdateService.CheckAsync()` returns `Connected=false`, `UpdateAvailable=false`, and message exactly `Automatic update checks will be added in a future build.`. Test running-app deduplication by PID and exclusion of zero-title/system-only processes in a fake enumeration seam.

- [ ] **Step 2: Implement running-application discovery**

Enumerate top-level visible windows, map each to PID/process, and return display name from `FileVersionInfo.FileDescription` when available; fall back to `Process.ProcessName`. Return the executable path when accessible, otherwise `null`. Never fail the entire list because one protected process denies access.

- [ ] **Step 3: Implement startup and logs**

`WindowsStartupService` writes/removes `HKCU\Software\Microsoft\Windows\CurrentVersion\Run\RatVision` pointing at the quoted executable path plus `--minimized`. `FileLogService` appends UTF-8 lines to `%LOCALAPPDATA%\RatVision\logs\ratvision-YYYYMMDD.log` and keeps the latest 14 daily files.

- [ ] **Step 4: Implement diagnostics**

Report lines in this order: RAT VISION version, OS, GPU(s), displays, foreground-hook state, NVAPI capability, global XRAT state, active profile, foreground process, settings path, log path. This exact ordering makes copied reports diff-friendly.

- [ ] **Step 5: Run service tests**

Run: `dotnet test src/RatVision.Tests/RatVision.Tests.csproj --filter FullyQualifiedName~SupportServices`

Expected: PASS without touching the real startup registry by using a registry abstraction in tests.

- [ ] **Step 6: Commit**

```bash
git add src/RatVision.Core src/RatVision.Windows src/RatVision.Tests
git commit -m "feat: add discovery diagnostics and support services"
```

---

### Task 9: Build Theme Tokens, Brand Assets, and the WPF Application Composition Root

**Files:**
- Create: `src/RatVision.App/Services/ThemeService.cs`
- Create: `src/RatVision.Core/Services/IThemeService.cs`
- Create: `src/RatVision.App/Services/EmojiAssetCatalog.cs`
- Create: `src/RatVision.App/Themes/ThemeTokens.xaml`
- Create: `src/RatVision.App/Themes/LevelBlack.xaml`
- Create: `src/RatVision.App/Themes/CleanLab.xaml`
- Create: `src/RatVision.App/Themes/Controls.xaml`
- Add curated assets under `src/RatVision.App/Assets/Brand`, `Assets/Tray`, `Assets/Emoji`
- Modify: `src/RatVision.App/App.xaml`
- Modify: `src/RatVision.App/App.xaml.cs`
- Create: `THIRD_PARTY_NOTICES.md`

**Interfaces:**
- Consumes all Core/Windows service interfaces from earlier tasks.
- Produces `ThemeService.Apply(ThemePreference)` and dependency-injection registrations.

- [ ] **Step 1: Add theme-resource tests through a lightweight dictionary load smoke test**

```csharp
[Fact]
public void ThemeDictionaries_ExposeRequiredSemanticBrushKeys()
{
    var required = new[] { "RvBackgroundBrush", "RvPanelBrush", "RvTextPrimaryBrush", "RvBorderBrush", "RvCorporateAccentBrush", "RvXratGreenBrush" };
    Assert.All(required, key => Assert.True(ThemeTestLoader.HasKey("LevelBlack.xaml", key)));
    Assert.All(required, key => Assert.True(ThemeTestLoader.HasKey("CleanLab.xaml", key)));
}
```

- [ ] **Step 2: Define semantic colors, never raw colors in controls**

`LevelBlack.xaml` uses near-black background, graphite panels, off-white text, steel borders, and bright green only for `RvXratGreenBrush`.

`CleanLab.xaml` starts with:

```xml
<Color x:Key="RvBackgroundColor">#F3F5F6</Color>
<Color x:Key="RvPanelColor">#FFFFFF</Color>
<Color x:Key="RvTextPrimaryColor">#17191B</Color>
<Color x:Key="RvTextSecondaryColor">#616A70</Color>
<Color x:Key="RvBorderColor">#CCD4D8</Color>
<Color x:Key="RvCorporateAccentColor">#39AEEA</Color>
<Color x:Key="RvCorporateAccentPaleColor">#E8F6FB</Color>
<Color x:Key="RvXratGreenColor">#39FF6A</Color>
```

All XAML controls reference `DynamicResource` semantic brushes so runtime theme changes repaint without restarting.

- [ ] **Step 3: Add legal emoji and brand assets**

Use a curated subset of Microsoft Fluent Emoji 3D assets for semantic keys: `rat`, `gamepad`, `crossed-swords`, `cowboy-hat`, `target`, `eye`, `sun`, `half-moon`, `palette`, `desktop`, `test-tube`, `gear`, `plus`, `coffee`, `warning`, `check`, `cross`, `refresh`, `upload`, `download`, `rocket`, `bell`, `clipboard`, `info`, `trash`.

Add the applicable MIT notice to `THIRD_PARTY_NOTICES.md`. Do not ship Apple artwork or font files.

Create the approved RAT VISION monochrome rat-head brand mark and two tray `.ico` files: `tray-off.ico` with a hollow dark lamp, `tray-on.ico` with the bright green lamp/glow. Each `.ico` must contain 16, 20, 24, 32, and 48 px frames.

- [ ] **Step 4: Wire DI and application lifetime**

`App.xaml.cs` creates one `ServiceCollection`, registers Core services as singletons, Windows adapters as singletons, WPF view models/services, and `MainWindow`. On startup: initialize settings, apply theme, start the coordinator and foreground service, create tray service, then show or hide MainWindow based on `StartMinimized`/`--minimized`. On exit: flush profile saves, stop coordinator, restore colors, dispose tray and color service.

- [ ] **Step 5: Build and manually flip themes**

Run: `dotnet build src/RatVision.App/RatVision.App.csproj -c Debug -p:Platform=x64`

Manual check: launch shell, switch Level Black → Clean Lab → Level Black without restart; no text becomes unreadable and XRAT green remains green in both themes.

- [ ] **Step 6: Commit**

```bash
git add src/RatVision.App src/RatVision.Core/Services/IThemeService.cs THIRD_PARTY_NOTICES.md
git commit -m "feat: add RAT VISION brand themes and composition root"
```

---

### Task 10: Implement Main Window Master/Detail ViewModels and Profile Workspace

**Files:**
- Create: `src/RatVision.App/ViewModels/MainWindowViewModel.cs`
- Create: `src/RatVision.App/ViewModels/GameProfileItemViewModel.cs`
- Create: `src/RatVision.App/ViewModels/ProfileWorkspaceViewModel.cs`
- Create: `src/RatVision.App/Views/ProfileWorkspaceView.xaml`
- Modify: `src/RatVision.App/MainWindow.xaml`
- Test: `src/RatVision.Tests/ViewModels/MainWindowViewModelTests.cs`
- Test: `src/RatVision.Tests/ViewModels/ProfileWorkspaceViewModelTests.cs`

**Interfaces:**
- Consumes `IProfileService`, `ProfileActivationCoordinator`, `IDisplayDiscoveryService`, `IThemeService`, `IShellService`.
- Produces commands/properties bound by the approved main-screen XAML.

- [ ] **Step 1: Write selection/global-toggle/slider tests first**

```csharp
[Fact]
public async Task GlobalToggle_DelegatesToCoordinatorAndKeepsWindowAlive()
{
    var vm = CreateMainViewModel(globalEnabled: true);
    await vm.ToggleGlobalCommand.ExecuteAsync(null);
    Assert.False(vm.GlobalEnabled);
    Assert.False(vm.CloseRequested);
}

[Fact]
public void ChangingBrightness_UpdatesOnlySelectedProfileVisuals()
{
    var vm = CreateWorkspaceWithTwoProfiles();
    vm.SelectedProfile.Brightness = 0.73;
    Assert.Equal(0.73, vm.SelectedProfile.Model.Visuals.Brightness, 3);
    Assert.Equal(0.5, vm.OtherProfile.Model.Visuals.Brightness, 3);
}
```

- [ ] **Step 2: Implement the fixed shell layout**

MainWindow default `Width=1180`, `Height=760`, `MinWidth=980`, `MinHeight=640`. Top bar and left sidebar are fixed. Right workspace is a `ScrollViewer`. Sidebar width is 260 px. `☕ Buy me a coffee` and `⚙ Settings` live in a bottom-docked stack and never scroll with profile items.

- [ ] **Step 3: Implement workspace controls exactly from blueprint**

Bind wide sliders for brightness/contrast/gamma/saturation, visible numeric value, and a per-row reset command. Bind profile enabled toggle, monitor checkbox list, target process list, `Copy settings from`, `Reset all`, `Add process`, and `Delete profile` actions. Saturation control is disabled with capability reason when `IColorService.Capabilities.SaturationSupported` is false.

Monitor checkbox semantics: multiple selected; prevent user interaction from leaving zero selected online/known display IDs by reverting the last uncheck and showing a nonblocking warning toast.

- [ ] **Step 4: Add runtime status and theme shortcut**

Top-right contains theme icon and global XRAT status. Profile workspace displays `LIVE // PROFILE CURRENTLY APPLIED`, `WAITING FOR FOCUS`, `READY`, or `PROFILE ERROR` from coordinator state. Use XRAT green only for LIVE/global ON LEDs, not normal selection/checkboxes.

- [ ] **Step 5: Run ViewModel tests and a visual smoke**

Run:

```bash
dotnet test src/RatVision.Tests/RatVision.Tests.csproj --filter FullyQualifiedName~ViewModels
dotnet run --project src/RatVision.App/RatVision.App.csproj -c Debug -p:Platform=x64
```

Expected automated tests: PASS. Manual: switching sidebar selection updates the right workspace without opening a new page; sidebar and top bar remain fixed while the workspace scrolls.

- [ ] **Step 6: Commit**

```bash
git add src/RatVision.App src/RatVision.Tests/ViewModels
git commit -m "feat: build RAT VISION profile workspace"
```

---

### Task 11: Implement Add Game, Copy Settings, and Delete Dialog Flows

**Files:**
- Create: `src/RatVision.App/ViewModels/AddGameViewModel.cs`
- Create: `src/RatVision.App/Views/Dialogs/AddGameDialog.xaml`
- Create: `src/RatVision.App/Views/Dialogs/CopyProfileDialog.xaml`
- Create: `src/RatVision.App/Views/Dialogs/DeleteProfileDialog.xaml`
- Create: `src/RatVision.App/Services/DialogService.cs`
- Test: `src/RatVision.Tests/ViewModels/AddGameViewModelTests.cs`

**Interfaces:**
- Consumes `IApplicationDiscoveryService`, `IDisplayDiscoveryService`, `IProfileService`.
- Produces two-step Add Game workflow and modal results.

- [ ] **Step 1: Write failing Add Game tests**

```csharp
[Fact]
public void ChoosingRunningApplication_PrefillsNameAndProcess()
{
    var vm = CreateVm(new RunningApplication(42, "Example Game", "Example.exe", @"C:\Games\Example.exe"));
    vm.SelectRunningApplicationCommand.Execute(42);
    Assert.Equal("Example Game", vm.Name);
    Assert.Contains("Example.exe", vm.ProcessNames);
}

[Fact]
public void NewProfile_DefaultsToPrimaryDisplay()
{
    var vm = CreateVm(primaryDisplay: "DISPLAY1");
    Assert.Contains("DISPLAY1", vm.SelectedDisplayIds);
}
```

- [ ] **Step 2: Implement step 1 discovery paths**

Buttons: `🎮 RUNNING APPLICATION` and `📁 BROWSE FOR .EXE`. Running list supports text search across display name and process name. `.exe` picker uses `Microsoft.Win32.OpenFileDialog` with filter `Applications (*.exe)|*.exe`.

- [ ] **Step 3: Implement step 2 profile fields**

Fields: Name, Emoji, target process list, monitor checkboxes, starting parameters `Default` or `Copy from existing profile`. Choosing copy uses `IProfileService.CopyVisuals` after profile creation; it must not copy display/process/identity values.

Provide a curated emoji picker backed by `EmojiAssetCatalog`; default generic added apps to `gamepad`.

- [ ] **Step 4: Implement copy/delete modal semantics**

Copy modal lists every profile except the target. Delete modal copy is exactly:

`Remove “{profile name}” from RAT VISION?`  
`The game itself will not be modified.`

Delete is visually dangerous only at hover/confirmation; cancel is default focus.

- [ ] **Step 5: Run tests and manual creation smoke**

Run: `dotnet test src/RatVision.Tests/RatVision.Tests.csproj --filter FullyQualifiedName~AddGame`

Manual: add Notepad from running apps, verify it appears as a profile, delete it, and confirm no executable/file is changed.

- [ ] **Step 6: Commit**

```bash
git add src/RatVision.App src/RatVision.Tests/ViewModels/AddGameViewModelTests.cs
git commit -m "feat: add game profile dialog flows"
```

---

### Task 12: Implement Settings, Import/Export, Diagnostics, About, Donation, and Update Placeholder UI

**Files:**
- Create: `src/RatVision.App/ViewModels/SettingsViewModel.cs`
- Create: `src/RatVision.App/Views/SettingsView.xaml`
- Create: `src/RatVision.App/Services/ShellService.cs`
- Test: `src/RatVision.Tests/ViewModels/SettingsViewModelTests.cs`

**Interfaces:**
- Consumes `ISettingsService`, `IStartupService`, `IThemeService`, `IDiagnosticsService`, `IUpdateService`, `ILogService`.
- `IShellService.OpenUri(Uri)` is the only application path that launches donation/project links.

- [ ] **Step 1: Write failing tests for update, donation, theme, and import/export commands**

```csharp
[Fact]
public async Task CheckUpdates_ShowsNotConnectedMessage()
{
    var vm = CreateVm();
    await vm.CheckUpdatesCommand.ExecuteAsync(null);
    Assert.Equal("UPDATE PROTOCOL NOT CONNECTED", vm.LastNoticeTitle);
}

[Fact]
public void BuyCoffee_OpensApprovedUrl()
{
    var shell = new RecordingShellService();
    var vm = CreateVm(shell: shell);
    vm.BuyCoffeeCommand.Execute(null);
    Assert.Equal("https://dalink.to/bazaz", shell.LastUri?.AbsoluteUri.TrimEnd('/'));
}
```

- [ ] **Step 2: Implement Settings sections from blueprint**

Sections: Startup, Window Behavior, Notifications, Profile Data, Appearance, Diagnostics, Updates, About. Theme radio choices are Follow Windows, Clean Lab, Level Black; Level Black is the first-run default. `Use3DEmoji` and subtle texture settings apply immediately and persist through the debounced settings save.

- [ ] **Step 3: Implement import/export and restore defaults**

Export uses a save dialog and writes the same schema-v2 JSON format. Import validates into a temporary `AppSettings`, requires at least one valid profile, then replaces current settings only after successful validation and retains a pre-import backup. Restore defaults replaces only profile collection with `BuiltInProfiles.Create()`; global/theme/startup preferences remain intact.

- [ ] **Step 4: Implement diagnostics/About/actions**

`Copy diagnostics` writes the report to clipboard. `Open logs` launches the log directory. About shows RAT VISION version, `See what the rat sees.`, `XRAT TRACING — Experimental Rodent Visual Enhancement Technology`, optional `Powered by questionable research.`, upstream attribution, licenses, and project link if configured.

`☕ Buy me a coffee` is bound to the same command in the sticky sidebar and tray menu.

- [ ] **Step 5: Run settings tests**

Run: `dotnet test src/RatVision.Tests/RatVision.Tests.csproj --filter FullyQualifiedName~SettingsViewModel`

Expected: PASS for theme switching, startup delegation, update placeholder message, donation URL, diagnostics copy seam, and import rejection of malformed JSON.

- [ ] **Step 6: Commit**

```bash
git add src/RatVision.App src/RatVision.Tests/ViewModels/SettingsViewModelTests.cs
git commit -m "feat: add RAT VISION settings and about"
```

---

### Task 13: Implement Tray Lifecycle and Two-State Rat Indicator

**Files:**
- Create: `src/RatVision.App/Services/TrayService.cs`
- Modify: `src/RatVision.App/App.xaml.cs`
- Modify: `src/RatVision.App/MainWindow.xaml.cs`
- Use: `src/RatVision.App/Assets/Tray/tray-off.ico`
- Use: `src/RatVision.App/Assets/Tray/tray-on.ico`
- Test: `src/RatVision.Tests/ViewModels/MainWindowViewModelTests.cs`

**Interfaces:**
- Consumes `ProfileActivationCoordinator`, `SettingsViewModel`, `IShellService`, main window show/hide delegates.
- Uses H.NotifyIcon `TaskbarIcon` with command-bound context menu.

- [ ] **Step 1: Add state-to-icon and close-behavior tests**

```csharp
[Theory]
[InlineData(false, "tray-off.ico")]
[InlineData(true, "tray-on.ico")]
public void TrayIconDependsOnlyOnGlobalEnabled(bool enabled, string expected)
{
    Assert.EndsWith(expected, TrayIconSelector.ForGlobalState(enabled), StringComparison.OrdinalIgnoreCase);
}
```

Test that user-closing MainWindow hides it when `CloseToTray=true`, while explicit Exit restores colors and terminates the app.

- [ ] **Step 2: Build the tray menu**

Menu order:

1. `🐀 RAT VISION v1.0.0` disabled header.
2. Global `XRAT TRACING` checked/unchecked command and status.
3. separator.
4. `🪟 Open RAT VISION`.
5. `⚙ Settings`.
6. `☕ Buy me a coffee`.
7. separator.
8. `❌ Exit`.

Double-click tray icon opens MainWindow. Right-click opens menu. The icon never gets a third profile-active variant.

- [ ] **Step 3: Make exit restoration unconditional**

Explicit Exit sequence is: disable new activation events → `RestoreAllAsync` → `IProfileService.FlushAsync` → stop foreground service → dispose tray → shutdown WPF. Wrap each cleanup stage so a failure in one stage does not skip remaining restore/dispose attempts; log every failure.

- [ ] **Step 4: Manual tray smoke**

Run app, verify OFF/ON icon swap is visible at Windows tray scale, close main window and reopen from tray, toggle XRAT from tray, click coffee link, then Exit and confirm desktop colors are restored.

- [ ] **Step 5: Commit**

```bash
git add src/RatVision.App src/RatVision.Tests/ViewModels/MainWindowViewModelTests.cs
git commit -m "feat: add RAT VISION tray lifecycle"
```

---

### Task 14: Polish Approved Control Language, Toasts, Accessibility, and Responsive Behavior

**Files:**
- Modify: `src/RatVision.App/Themes/Controls.xaml`
- Modify: `src/RatVision.App/MainWindow.xaml`
- Modify: `src/RatVision.App/Views/ProfileWorkspaceView.xaml`
- Modify: `src/RatVision.App/Views/SettingsView.xaml`
- Modify dialog XAML files
- Create: `src/RatVision.App/Services/ToastService.cs`

**Interfaces:**
- Consumes existing view-model commands only; this task must not invent new product behavior.

- [ ] **Step 1: Encode the 8 px spacing system and control geometry**

Create resources for 8, 16, 24, and 32 px spacing; panel corner radius 5 px; restrained 1 px borders. Sliders are thin with numeric values to the right and a reset action. Toggles always show ON/OFF text plus a status lamp. Night checked monitor boxes use off-white; Day checked monitor boxes use corporate cyan, never XRAT green.

- [ ] **Step 2: Implement semantic toasts**

Supported notices:

- `✅ PARAMETERS SAVED`
- `🧪 TEST SUBJECT REGISTERED`
- `⚠️ DISPLAY UNAVAILABLE`
- `🧪 UPDATE PROTOCOL NOT CONNECTED`

Toasts are nonblocking, appear bottom-right, and auto-dismiss after 2.5 seconds except errors, which remain for 6 seconds.

- [ ] **Step 3: Add keyboard/accessibility metadata**

Every icon-only control has `AutomationProperties.Name` and tooltip. Tab order follows top bar → profile list → workspace → sticky sidebar actions. Sliders respond to arrows/PageUp/PageDown and expose current numeric value to accessibility APIs. Do not encode enabled/disabled state only by color.

- [ ] **Step 4: Verify both themes and minimum window size**

Manual matrix at 100%, 125%, and 150% Windows scaling:

- 1180×760 Level Black
- 1180×760 Clean Lab
- 980×640 Level Black
- 980×640 Clean Lab

Pass criteria: no overlap, sidebar donation/settings remain visible, right workspace scrolls, text is legible, emoji do not alter row heights unpredictably.

- [ ] **Step 5: Commit**

```bash
git add src/RatVision.App
git commit -m "style: finish RAT VISION approved UI system"
```

---

### Task 15: Remove Legacy WinForms Runtime, Preserve Attribution, and Document the New Product

**Files:**
- Delete after parity verification: `App/`, `Display/`, `GPU/`, `Setting/`
- Delete: `tarkov-settings.csproj`, old `.sln`, `packages.config`, `App.config`, `FodyWeavers.xml`, `FodyWeavers.xsd`, old `T.ico`, old screenshot if no longer used
- Modify: `README.md`
- Preserve: `LICENSE`
- Modify: `THIRD_PARTY_NOTICES.md`

**Interfaces:**
- No runtime interface changes; this is migration cleanup only.

- [ ] **Step 1: Run parity checklist before deleting anything**

Verify the new app can: detect EFT foreground, apply/restore gamma, apply/restore NVIDIA DVC when supported, select monitor(s), hide to tray, restore on Exit, persist settings, and show version. If any item fails, do not perform legacy deletion in this task.

- [ ] **Step 2: Remove old build/runtime files from the working tree**

Delete only after the parity checklist passes. Git history remains the source reference for old implementation. Keep upstream `LICENSE` unchanged.

- [ ] **Step 3: Rewrite README for RAT VISION**

README sections: What it does, screenshots, default game profiles, Add Game, multi-monitor, Day/Night themes, tray behavior, GPU support, safety/anti-cheat disclaimer, download/build instructions, donation, upstream attribution, license, known limitations. Explicitly credit `incheon-kim/tarkov-settings` as the upstream project whose display-control behavior was ported.

- [ ] **Step 4: Add third-party notice entries**

List WPF-UI, CommunityToolkit.Mvvm, H.NotifyIcon, NvAPIWrapper, and Fluent Emoji with their project/license names. Do not duplicate full dependency source code.

- [ ] **Step 5: Build/test after legacy removal**

Run:

```bash
dotnet clean RatVision.sln
dotnet restore RatVision.sln
dotnet build RatVision.sln -c Release -p:Platform=x64
dotnet test RatVision.sln -c Release -p:Platform=x64 --no-build
```

Expected: no reference to the old WinForms project and all tests PASS.

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "refactor: complete migration from tarkov-settings"
```

---

### Task 16: Publish x64 Portable Build and Run Final Verification

**Files:**
- Create: `src/RatVision.App/Properties/PublishProfiles/WinX64.pubxml`
- Create: `scripts/build-release.ps1`
- Modify: `README.md` release section if needed

**Interfaces:**
- Produces `artifacts/RatVision-v1.0.0-win-x64/` and `artifacts/RatVision-v1.0.0-win-x64.zip`.

- [ ] **Step 1: Add the self-contained publish profile**

```xml
<Project>
  <PropertyGroup>
    <Configuration>Release</Configuration>
    <TargetFramework>net8.0-windows</TargetFramework>
    <RuntimeIdentifier>win-x64</RuntimeIdentifier>
    <SelfContained>true</SelfContained>
    <PublishSingleFile>false</PublishSingleFile>
    <PublishReadyToRun>false</PublishReadyToRun>
    <DebugType>none</DebugType>
  </PropertyGroup>
</Project>
```

Keep multi-file publishing because WPF/native/NvAPI dependencies are easier to inspect and troubleshoot in the first release.

- [ ] **Step 2: Create deterministic build script**

`scripts/build-release.ps1` must delete only `artifacts/RatVision-v1.0.0-win-x64`, run restore/test/publish, copy `LICENSE` and `THIRD_PARTY_NOTICES.md` into the publish folder, then zip that folder. Print numbered stages `[1/5]` through `[5/5]` so the user always sees progress.

- [ ] **Step 3: Run full automated verification**

```powershell
./scripts/build-release.ps1
```

Expected: all tests pass, publish succeeds, ZIP exists, and the folder contains `RatVision.App.exe`, tray/emoji resources, license, and notices.

- [ ] **Step 4: Run final Windows manual matrix**

On a Windows x64 machine:

1. Launch clean settings → three default profiles exist.
2. Toggle Clean Lab/Level Black/Follow Windows.
3. Add a harmless app profile through running-app discovery.
4. Select two displays if available; verify both restore after leaving target.
5. Test EFT/Arena/Hunt process matching where installed.
6. Toggle global XRAT OFF while a profile is active → immediate restore.
7. Close to tray, reopen, toggle from tray, verify lamp states.
8. Restart app → settings/global state persist.
9. Click `Check for updates` → approved not-connected message, no network request.
10. Click `Buy me a coffee` → `https://dalink.to/bazaz` opens.
11. Exit from tray while profile active → desktop state restored.

- [ ] **Step 5: Run verification-before-completion skill before any completion claim**

Required commands/output evidence:

```bash
git status --short
dotnet build RatVision.sln -c Release -p:Platform=x64
dotnet test RatVision.sln -c Release -p:Platform=x64 --no-build
```

Do not claim v1 complete unless all commands succeed and the manual restore/exit check passes.

- [ ] **Step 6: Commit**

```bash
git add src/RatVision.App/Properties scripts README.md
git commit -m "build: add RAT VISION portable release pipeline"
```

---

## Plan Self-Review Results

### Spec coverage

- Per-game profiles: Tasks 2, 3, 10.
- Multiple executables: Tasks 2, 3, 11.
- Multi-monitor checkboxes and restore: Tasks 5, 6, 10.
- Global ON/OFF with immediate restore: Task 7 and tray Task 13.
- Foreground activation: Tasks 4 and 7.
- Gamma + NVIDIA saturation: Tasks 5 and 6.
- Add running application / browse `.exe`: Tasks 8 and 11.
- Copy visual settings only: Tasks 3 and 11.
- Autosave: Task 3.
- Level Black / Clean Lab / Follow Windows: Tasks 9, 10, 12, 14.
- TerraGroup-inspired visual system and green XRAT separation: Tasks 9 and 14.
- 3D emoji: Task 9 and UI tasks.
- Rat brand/tray lamp: Tasks 9 and 13.
- Donation always visible: Tasks 10, 12, 13.
- Updates placeholder: Tasks 8 and 12.
- Startup/tray/notifications/diagnostics/About/import/export: Tasks 8, 12, 13.
- Version visibility: Tasks 1, 8, 12, 13.
- Upstream attribution/license: Task 15.
- Portable x64 release and visible progress: Task 16.

### Placeholder scan

The plan intentionally implements the update feature as a **not-connected v1 service**, which is a final v1 behavior required by the spec, not an unfinished code placeholder. No unspecified implementation markers are used.

### Type consistency

`GameProfile`, `VisualParameters`, `ISettingsService`, `IProfileService`, `IForegroundWindowService`, `IColorService`, and coordinator signatures defined in earlier tasks are used consistently by later tasks. UI tasks depend only on published service interfaces; Windows hardware adapters never depend on WPF views or view models.
