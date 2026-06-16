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
