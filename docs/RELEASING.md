# Releasing

Releases are cut from `main` after the release PR is merged. Versioning follows
[SemVer](https://semver.org/): a `feat` commit bumps MINOR, a `fix` commit bumps
PATCH, and a `!`/`BREAKING CHANGE` bumps MAJOR.

## Checklist

1. **Everything green**

   ```powershell
   pwsh -File tools/validate.ps1 -DownloadTools
   pwsh -File tools/validate.ps1 -Static
   ```

2. **Version** — calculate the next version from the commits since the last tag:

   ```bash
   python3 C:/Users/kluse/.dsh/skills/opensource-project/scripts/oss-version.py next
   ```

   Update `mods/LethalHeadshots/mod.json` (`version` and, when applicable,
   `gameVersion`). Do not edit `CHANGELOG.md` by hand.

3. **Changelog**

   ```bash
   python3 C:/Users/kluse/.dsh/skills/opensource-project/scripts/oss-changelog.py --write
   ```

4. **Build and inspect the artifact**

   ```powershell
   pwsh -File tools/build.ps1
   ```

   The zip must contain `r6/scripts/LethalHeadshots/*.reds`, `INSTALL.txt` and
   `LICENSE` at the expected paths. `dist/SHA256SUMS.txt` is generated next to it.

5. **Commit, tag, push**

   ```bash
   git add -A
   git commit -m "chore(release): vX.Y.Z"
   git tag -a vX.Y.Z -m "vX.Y.Z"
   git push origin main --follow-tags
   ```

   Pushing the tag triggers `.github/workflows/release.yml`, which builds the zip
   on a clean runner, creates the GitHub release and uploads the artifact plus
   `SHA256SUMS.txt`.

6. **Verify** the release page: the tag is `vX.Y.Z`, the zip asset is attached,
   and the release notes match the changelog.

## Rollback

Never move or delete a published tag. If a release is broken, publish a new
PATCH with the fix and mark the broken release as pre-release on GitHub.
