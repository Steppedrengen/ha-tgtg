# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-06-16

### Added
- Initial release
- One sensor entity per TGTG favourite store
- `distance_km` attribute — Haversine distance from HA home coordinates
- `store_latitude` / `store_longitude` attributes for map cards
- Formatted `pickup_display` attribute (e.g. `17/06 19:30 – 20:30`)
- Config flow with magic link authentication
- Configurable polling interval (1–60 minutes)
- Dynamic entity creation — new favourites appear without restart
- GitHub Actions: HACS validation, hassfest, release automation
- Bilingual UI: English and Danish (`da`)

## [1.0.1] - 2026-06-16

### Fixed
- Replaced deprecated `FlowResult` with `config_entries.ConfigFlowResult` (HA 2024.x compatibility)
- Fixed `OptionsFlow.__init__` signature — removed `config_entry` parameter (now accessed via `self.config_entry`)
- Renamed config flow step `login` → `link` to avoid broken `description_placeholders`
- Guarded `tgtg` import inside functions to prevent 500 error if package not yet installed
- Added `missing_dependency` and `cannot_connect` error keys to translations
- Updated `en.json` and `da.json` to match corrected step IDs

## [1.0.2] - 2026-06-16

### Fixed
- Removed `ConfigFlowResult` return type annotations — caused 500 error on older HA builds
- Fixed wrong PyPI package name: `tgtg-python` → `tgtg>=0.17.0`
- Fixed documentation and issue_tracker URLs in manifest.json

## [1.0.3] - 2026-06-16

### Changed
- **New authentication flow**: Replaced magic link (async/manual verification) with **PIN code from email** ✉️
  - User enters email → TGTG sends PIN code email → User pastes 6-digit PIN in HA config flow
  - Much simpler, no need to click links or wait for email verification
  - Both EN and DA translations updated

### Technical
- Uses TGTG API endpoints: `/auth/v0/requestPolling` + `/auth/v0/validateToken`
- Polling ID tracked per login session
- More reliable error handling for PIN validation

## [1.0.4] - 2026-06-16

### Fixed
- PIN authentication was not working — `start_polling()` uses `input()` which doesn't work in async context
- Now uses direct TGTG API calls to `/auth/v0/authByEmail` and `/auth/v0/authByRequestPin`
- Removed dependency on `start_polling()` method
- Better error messages for TGTG API failures

## [1.0.5] - 2026-06-16

### Fixed
- **Root cause found: wrong API endpoint version** — was calling `auth/v0/` which doesn't exist; correct endpoint is `auth/v5/authByEmail` and `auth/v5/authByRequestPin`
- This is why PIN email was never sent — the request was hitting a non-existent endpoint
- Now uses `_post()` from TgtgClient so DataDome bot-protection cookie is handled automatically
- Now uses `_auth_by_pin()` directly from TgtgClient for PIN validation
- Added error handling for `too_many_requests` and `not_registered` states
- Debug logging added for easier troubleshooting
