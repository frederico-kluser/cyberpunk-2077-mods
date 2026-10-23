# Adding a mod to this repository

Every mod is a self-contained folder under `mods/`. The build and release
pipeline discovers mods by their `mod.json`, so adding one is mechanical.

## 1. Create the folder

```text
mods/MyMod/
  mod.json
  README.md
  src/reds/
    MyMod.reds
    Config.reds        # optional
```

Use `mods/LethalHeadshots` as the reference implementation.

## 2. Write `mod.json`

```json
{
  "id": "MyMod",
  "name": "My Mod",
  "version": "1.0.0",
  "gameVersion": "2.5",
  "author": "Frederico Kluser",
  "license": "MIT",
  "description": "One sentence that explains what the mod changes.",
  "tags": ["gameplay"],
  "requires": {
    "redscript": ">=0.5.32"
  },
  "files": [
    "src/reds/MyMod.reds"
  ]
}
```

Rules enforced by `tools/validate.ps1`:

- `id` equals the folder name;
- `version` is valid SemVer;
- every entry in `files` exists;
- every `.reds` file declares a `module`.

## 3. Write the Redscript

```redscript
module MyMod

@wrapMethod(SomeSystem)
private final func SomeMethod() -> Void {
  wrappedMethod();
  // your logic
}
```

Prefer `@wrapMethod` over `@replaceMethod` so other mods can coexist. Add a
comment above every hook explaining which engine function it touches and why.

## 4. Validate

```powershell
pwsh -File tools/validate.ps1 -Static          # structure + syntax
pwsh -File tools/validate.ps1 -DownloadTools   # type-check against 2.5
```

The type-check is the important gate: it fails if a class, method or enum used by
the mod does not exist in the installed game version.

## 5. Package and deploy

```powershell
pwsh -File tools/build.ps1        # dist/MyMod-<version>.zip + SHA256SUMS.txt
pwsh -File tools/deploy.ps1 -ModId MyMod
```

## 6. Document and ship

- Add a row to the table in the root `README.md`.
- Write `README.md` inside the mod folder: what it does, requirements, install,
  configuration, limitations and how it was tested.
- Add an entry to `CHANGELOG.md` (generated from Conventional Commits at release
  time — see [RELEASING.md](RELEASING.md)).
- Open a PR with a Conventional title (`feat(MyMod): ...`).
