# Changelog

All notable changes to Dofusinator are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), versioning follows [Semantic Versioning](https://semver.org/).

## [1.1.0] — 2026-05-06

### Highlight
- 🚀 First public release on GitHub! Auto-update powered by Velopack.

### Changed
- Version bumped from v1.0.34 to v1.1.0 to mark transition from internal scaffolding to public release.

## [1.0.34] — 2026-05-06

### Added
- Velopack auto-update scaffolding (`update_manager_service.py`, hooks in main entry)
- Build pipeline now uses Velopack instead of Inno Setup
- Splash image during installation
- Auto-update UI: 5s post-startup background check, Discord-style toast notification, modal dialog with download progress, and a manual "Check for updates" button in the Advanced tab

### Added
- Velopack auto-update scaffolding (`update_manager_service.py`, hooks in main entry)
- Build pipeline now uses Velopack instead of Inno Setup
- Splash image during installation

### Changed
- Build system completely rewritten: `Dofusinator.spec` auto-scans `src/` for modules, `build.bat` runs `vpk pack`, replacing the previous Inno Setup workflow

### Fixed
- Quick input popup (`Ctrl+Shift+T`) sizing regression
- Sound files not loading in installed builds (resource path now correctly resolves to PyInstaller's `_internal/` directory when frozen)
- Asset paths for tray icon and slang dictionary in installed builds

## [1.0.33] — 2026-05-05

### Changed
- App description and metadata now correctly reflect the 4 supported translation languages (French, Portuguese, English, Spanish) — no longer implies the app is limited to FR↔PT.

### Fixed
- Executable copyright string updated with proper legal name and current year.

## [1.0.32] — 2026-05-05

### Fixed
- Scrollbar of the **Appearance** tab no longer has unwanted right margin — now sits flush with the window border like the other tabs (`padx=(SPACING_LG, 0)`)
- Section title in Appearance tab no longer renders as raw i18n key `appearance.section.lang` — now correctly translates to "Idioma do app" (PT) / "App language" (EN) / etc.

---

[1.0.32]: https://github.com/afkdino/dofusinator/releases/tag/v1.0.32