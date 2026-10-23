# Changelog

All notable changes to **cyberpunk-2077-mods** are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

- Versions are tagged as `v<MAJOR>.<MINOR>.<PATCH>` from `main`.
- Entries are generated from [Conventional Commits](https://www.conventionalcommits.org/)
  at release time (see `cliff.toml` and `.github/workflows/release.yml`).

## [Unreleased]

## [1.0.1] - 2026-10-23

### Fixed

- Corrected the runtime requirements: the mod only needs **redscript 0.5.32+**.
  RED4ext was listed as a dependency, but the engine compiles `r6/scripts` at
  launch on its own.

## [1.0.0] - 2026-10-23

### Added

- **Lethal Headshots 1.0.0** — Redscript mod that turns any valid headshot into an
  instant kill through the engine's native `hitFlag.Kill` path, with guards for
  aim projection, friendly fire, civilians, allies and quest-protected NPCs.
- `tools/validate.ps1` — repository checks plus Redscript type-check against the
  installed 2.5 script bundle (`final.redscripts`).
- `tools/build.ps1` — reproducible zip packaging with SHA256 checksums.
- `tools/deploy.ps1` — one-command deployment into a local game installation.
- CI (PowerShell parsing, Redscript lint, package layout, Conventional Commits)
  and a tag-driven release workflow that publishes the zip and checksums.
- Documentation: architecture walk-through of the damage pipeline, in-game test
  matrix, release process and the deep-research dossier behind the design.

[Unreleased]: https://github.com/frederico-kluser/cyberpunk-2077-mods/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/frederico-kluser/cyberpunk-2077-mods/releases/tag/v1.0.0
