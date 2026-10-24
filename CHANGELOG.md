# Changelog

All notable changes to **cyberpunk-2077-mods** are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

- Versions are tagged as `v<MAJOR>.<MINOR>.<PATCH>` from `main`.
- Entries are generated from [Conventional Commits](https://www.conventionalcommits.org/)
  at release time (see `cliff.toml` and `.github/workflows/release.yml`).

## [Unreleased]

## [1.1.0] - 2026-10-24

### Features
- **DesertEagle:** decode and verify mesh render buffer format ([251bb45](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/251bb45))
- **DesertEagle:** author app and ent via CR2W json round-trip (#23) ([b826cc5](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/b826cc5))
- **DesertEagle:** calibrate mag set anims and split export by set (#21) ([0c7e71f](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/0c7e71f))
- **DesertEagle:** calibrated .re animsets from CS2 motion (#20) ([8600aa0](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/8600aa0))
- **DesertEagle:** CS2 model retarget to Nue rig bones (#17) ([1875e78](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/1875e78))
- **DesertEagle:** rig mapping to Nue bones, model provenance, renders (#16) ([4207691](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/4207691))
- **lethalheadshots:** force-kill headshots and poll the aim label (#15) ([d4dae69](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/d4dae69))
- **DesertEagle:** scaffold weapon mod and Blender pipeline (#13) ([1a6f999](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/1a6f999))
- **lethalheadshots:** aim preview label and lethal defaults (#11) ([ad7b0ab](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/ad7b0ab))

### Bug Fixes
- **lethalheadshots:** trace the aim ticker with FTLog markers ([830399b](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/830399b))
- **lethalheadshots:** make the aim ticker immortal and self-healing (#24) ([408af34](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/408af34))
- **lethalheadshots:** four-channel aim label with vanilla HUD fallback (#19) ([403fd02](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/403fd02))
- **lethalheadshots:** show aim label from the crosshair controller (#14) ([a73ed64](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/a73ed64))

### Documentation
- **lethalheadshots:** record engineering lessons and pitfalls (#22) ([d49fcf9](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/d49fcf9))
- **DesertEagle:** CS2 to Nue animation calibration map (#18) ([2dc8241](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/2dc8241))
- require merge to main to finish any task (#12) ([ca2a4f2](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/ca2a4f2))
- **research:** add manual de HUD e guia de armas + indice (#10) ([9305f32](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/9305f32))
- **research:** add guia de modding tecnico do CP2077 (#9) ([e95cb48](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/e95cb48))
- add CoALA project memory and catalog (#8) ([86182d6](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/86182d6))
- explain how to add a mod to the monorepo (#5) ([049c2c8](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/049c2c8))

### Build & CI
- pin scorecard action to its commit SHA (#7) ([935cf60](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/935cf60))
- keep optional release-please automation pinned (#6) ([1ad01a2](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/1ad01a2))
- version enterprise commit-message ruleset (#4) ([625f04e](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/625f04e))

## [1.1.0] - 2026-10-24

### Features
- **DesertEagle:** author app and ent via CR2W json round-trip (#23) ([b826cc5](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/b826cc5))
- **DesertEagle:** calibrate mag set anims and split export by set (#21) ([0c7e71f](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/0c7e71f))
- **DesertEagle:** calibrated .re animsets from CS2 motion (#20) ([8600aa0](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/8600aa0))
- **DesertEagle:** CS2 model retarget to Nue rig bones (#17) ([1875e78](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/1875e78))
- **DesertEagle:** rig mapping to Nue bones, model provenance, renders (#16) ([4207691](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/4207691))
- **lethalheadshots:** force-kill headshots and poll the aim label (#15) ([d4dae69](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/d4dae69))
- **DesertEagle:** scaffold weapon mod and Blender pipeline (#13) ([1a6f999](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/1a6f999))
- **lethalheadshots:** aim preview label and lethal defaults (#11) ([ad7b0ab](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/ad7b0ab))

### Bug Fixes
- **lethalheadshots:** make the aim ticker immortal and self-healing ([50816ca](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/50816ca))
- **lethalheadshots:** four-channel aim label with vanilla HUD fallback (#19) ([403fd02](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/403fd02))
- **lethalheadshots:** show aim label from the crosshair controller (#14) ([a73ed64](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/a73ed64))

### Documentation
- **lethalheadshots:** record engineering lessons and pitfalls (#22) ([d49fcf9](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/d49fcf9))
- **DesertEagle:** CS2 to Nue animation calibration map (#18) ([2dc8241](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/2dc8241))
- require merge to main to finish any task (#12) ([ca2a4f2](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/ca2a4f2))
- **research:** add manual de HUD e guia de armas + indice (#10) ([9305f32](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/9305f32))
- **research:** add guia de modding tecnico do CP2077 (#9) ([e95cb48](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/e95cb48))
- add CoALA project memory and catalog (#8) ([86182d6](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/86182d6))
- explain how to add a mod to the monorepo (#5) ([049c2c8](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/049c2c8))

### Build & CI
- pin scorecard action to its commit SHA (#7) ([935cf60](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/935cf60))
- keep optional release-please automation pinned (#6) ([1ad01a2](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/1ad01a2))
- version enterprise commit-message ruleset (#4) ([625f04e](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/625f04e))

## [1.1.0] - 2026-10-24

### Features
- **DesertEagle:** calibrate mag set anims and split export by set (#21) ([0c7e71f](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/0c7e71f))
- **DesertEagle:** calibrated .re animsets from CS2 motion (#20) ([8600aa0](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/8600aa0))
- **DesertEagle:** CS2 model retarget to Nue rig bones (#17) ([1875e78](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/1875e78))
- **DesertEagle:** rig mapping to Nue bones, model provenance, renders (#16) ([4207691](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/4207691))
- **lethalheadshots:** force-kill headshots and poll the aim label (#15) ([d4dae69](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/d4dae69))
- **DesertEagle:** scaffold weapon mod and Blender pipeline (#13) ([1a6f999](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/1a6f999))
- **lethalheadshots:** aim preview label and lethal defaults (#11) ([ad7b0ab](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/ad7b0ab))

### Bug Fixes
- **lethalheadshots:** four-channel aim label with vanilla HUD fallback (#19) ([403fd02](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/403fd02))
- **lethalheadshots:** show aim label from the crosshair controller (#14) ([a73ed64](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/a73ed64))

### Documentation
- **lethalheadshots:** record engineering lessons and pitfalls ([d1840f7](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/d1840f7))
- **DesertEagle:** CS2 to Nue animation calibration map (#18) ([2dc8241](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/2dc8241))
- require merge to main to finish any task (#12) ([ca2a4f2](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/ca2a4f2))
- **research:** add manual de HUD e guia de armas + indice (#10) ([9305f32](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/9305f32))
- **research:** add guia de modding tecnico do CP2077 (#9) ([e95cb48](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/e95cb48))
- add CoALA project memory and catalog (#8) ([86182d6](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/86182d6))
- explain how to add a mod to the monorepo (#5) ([049c2c8](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/049c2c8))

### Build & CI
- pin scorecard action to its commit SHA (#7) ([935cf60](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/935cf60))
- keep optional release-please automation pinned (#6) ([1ad01a2](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/1ad01a2))
- version enterprise commit-message ruleset (#4) ([625f04e](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/625f04e))

## [1.1.0] - 2026-10-24

### Features
- **DesertEagle:** CS2 model retarget to Nue rig bones (#17) ([1875e78](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/1875e78))
- **DesertEagle:** rig mapping to Nue bones, model provenance, renders (#16) ([4207691](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/4207691))
- **lethalheadshots:** force-kill headshots and poll the aim label (#15) ([d4dae69](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/d4dae69))
- **DesertEagle:** scaffold weapon mod and Blender pipeline (#13) ([1a6f999](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/1a6f999))
- **lethalheadshots:** aim preview label and lethal defaults (#11) ([ad7b0ab](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/ad7b0ab))

### Bug Fixes
- **lethalheadshots:** four-channel aim label with vanilla HUD fallback ([6c0a601](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/6c0a601))
- **lethalheadshots:** show aim label from the crosshair controller (#14) ([a73ed64](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/a73ed64))

### Documentation
- **DesertEagle:** CS2 to Nue animation calibration map (#18) ([2dc8241](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/2dc8241))
- require merge to main to finish any task (#12) ([ca2a4f2](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/ca2a4f2))
- **research:** add manual de HUD e guia de armas + indice (#10) ([9305f32](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/9305f32))
- **research:** add guia de modding tecnico do CP2077 (#9) ([e95cb48](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/e95cb48))
- add CoALA project memory and catalog (#8) ([86182d6](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/86182d6))
- explain how to add a mod to the monorepo (#5) ([049c2c8](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/049c2c8))

### Build & CI
- pin scorecard action to its commit SHA (#7) ([935cf60](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/935cf60))
- keep optional release-please automation pinned (#6) ([1ad01a2](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/1ad01a2))
- version enterprise commit-message ruleset (#4) ([625f04e](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/625f04e))

## [1.1.0] - 2026-10-23

### Features
- **lethalheadshots:** force-kill headshots and poll the aim label ([28cb5a8](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/28cb5a8))
- **DesertEagle:** scaffold weapon mod and Blender pipeline (#13) ([1a6f999](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/1a6f999))
- **lethalheadshots:** aim preview label and lethal defaults (#11) ([ad7b0ab](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/ad7b0ab))

### Bug Fixes
- **lethalheadshots:** show aim label from the crosshair controller (#14) ([a73ed64](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/a73ed64))

### Documentation
- require merge to main to finish any task (#12) ([ca2a4f2](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/ca2a4f2))
- **research:** add manual de HUD e guia de armas + indice (#10) ([9305f32](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/9305f32))
- **research:** add guia de modding tecnico do CP2077 (#9) ([e95cb48](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/e95cb48))
- add CoALA project memory and catalog (#8) ([86182d6](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/86182d6))
- explain how to add a mod to the monorepo (#5) ([049c2c8](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/049c2c8))

### Build & CI
- pin scorecard action to its commit SHA (#7) ([935cf60](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/935cf60))
- keep optional release-please automation pinned (#6) ([1ad01a2](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/1ad01a2))
- version enterprise commit-message ruleset (#4) ([625f04e](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/625f04e))

## [1.1.0] - 2026-10-23

### Features
- **lethalheadshots:** aim preview label and lethal defaults (#11) ([ad7b0ab](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/ad7b0ab))

### Bug Fixes
- **lethalheadshots:** show aim label from the crosshair controller ([fd52d91](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/fd52d91))

### Documentation
- require merge to main to finish any task (#12) ([ca2a4f2](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/ca2a4f2))
- **research:** add manual de HUD e guia de armas + indice (#10) ([9305f32](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/9305f32))
- **research:** add guia de modding tecnico do CP2077 (#9) ([e95cb48](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/e95cb48))
- add CoALA project memory and catalog (#8) ([86182d6](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/86182d6))
- explain how to add a mod to the monorepo (#5) ([049c2c8](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/049c2c8))

### Build & CI
- pin scorecard action to its commit SHA (#7) ([935cf60](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/935cf60))
- keep optional release-please automation pinned (#6) ([1ad01a2](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/1ad01a2))
- version enterprise commit-message ruleset (#4) ([625f04e](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/625f04e))

## [1.1.0] - 2026-10-23

### Features
- **lethalheadshots:** aim preview label and lethal defaults (#11) ([ad7b0ab](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/ad7b0ab))

### Documentation
- require merge to main to finish any task (#12) ([ca2a4f2](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/ca2a4f2))
- **research:** add manual de HUD e guia de armas + indice (#10) ([9305f32](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/9305f32))
- **research:** add guia de modding tecnico do CP2077 (#9) ([e95cb48](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/e95cb48))
- add CoALA project memory and catalog (#8) ([86182d6](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/86182d6))
- explain how to add a mod to the monorepo (#5) ([049c2c8](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/049c2c8))

### Build & CI
- pin scorecard action to its commit SHA (#7) ([935cf60](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/935cf60))
- keep optional release-please automation pinned (#6) ([1ad01a2](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/1ad01a2))
- version enterprise commit-message ruleset (#4) ([625f04e](https://github.com/frederico-kluser/cyberpunk-2077-mods/commit/625f04e))

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
