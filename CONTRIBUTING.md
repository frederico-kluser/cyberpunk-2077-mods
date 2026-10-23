# Contributing to cyberpunk-2077-mods

Thanks for your interest in contributing! This document explains the workflow,
conventions and quality bar for every change.

Please note that this project is released with a
[Code of Conduct](CODE_OF_CONDUCT.md). By participating you are expected to
uphold it.

## Getting started

1. **Fork** the repository and clone your fork:

   ```bash
   git clone https://github.com/<your-user>/cyberpunk-2077-mods.git
   cd cyberpunk-2077-mods
   git remote add upstream https://github.com/frederico-kluser/cyberpunk-2077-mods.git
   ```

2. **Install the local hooks** (they enforce branch names and Conventional
   Commits before you push):

   ```bash
   bash C:/Users/kluse/.dsh/skills/opensource-project/scripts/oss-hooks.sh install
   ```

3. **Verify the baseline**:

   ```powershell
   pwsh -File tools/validate.ps1 -Static
   ```

   If you have the game installed, also run the full type-check:

   ```powershell
   pwsh -File tools/validate.ps1 -DownloadTools
   ```

## How to submit a change

- **Never push directly to `main`.** Direct pushes are blocked by repository
  rulesets; all changes land through pull requests.
- Work on a short-lived branch following `<type>/<slug>` and open a pull request
  against `main`.
- Keep each branch focused on a single change.
- Rebase on `upstream/main`; do not merge `main` into your branch.

## Branch naming — enforced, not advisory

A repository ruleset rejects names outside `<type>/<slug>`. The type set is
closed: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`,
`ci`, `chore`, `revert`, `hotfix`, `release`.

Examples: `feat/melee-headshots`, `fix/civilian-detection`,
`docs/install-red4ext`.

## Commit convention

We use [Conventional Commits](https://www.conventionalcommits.org/). The commit
message becomes the changelog entry and drives the semantic version bump.

```text
feat(mod): add a config toggle for melee headshots
fix(damage): skip defeated targets
docs: document the 2.5 requirement
feat!: drop support for patch 2.3

BREAKING CHANGE: the mod now requires redscript 0.5.32.
```

Header must be at most **72 characters** and use the imperative mood. Allowed
types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`,
`ci`, `chore`, `revert`.

## Local quality gates

Run these before opening a pull request — all must pass:

```powershell
pwsh -File tools/validate.ps1 -Static
pwsh -File tools/validate.ps1 -DownloadTools   # if the game is installed
pwsh -File tools/build.ps1 -SkipValidation     # package still builds
```

Because the mod hooks engine code, a change is only complete when it has been
**type-checked against the installed 2.5 bundle**. If you cannot run that locally,
say so in the pull request so a maintainer can run it.

Add or update the manual test matrix in [docs/TESTING.md](docs/TESTING.md) for
behavioural changes.

## Pull request process

1. **Title = Conventional Commit message.** It becomes the squash-merge commit.
2. **Describe what and why**, plus how you tested it (game version, redscript
   version, scenarios from the test matrix).
3. **Link related issues** with closing keywords (`Closes #123`).
4. **All checks green** before requesting review.
5. **Squash and merge only**; the source branch is deleted afterwards.

## Reporting bugs

Use the [bug report template](.github/ISSUE_TEMPLATE/bug_report.md) and include:

- game version (`Cyberpunk2077.exe` → Properties → Details);
- redscript and RED4ext versions;
- the relevant lines from `r6\logs\redscript_rCURRENT.log`;
- mods installed alongside this one.

**Security vulnerabilities must not be reported as public issues.** Follow the
private process in [SECURITY.md](SECURITY.md).

## Recognition

Every contribution counts: the changelog attributes merged changes to their
authors and release notes credit first-time contributors.

Thank you for helping make cyberpunk-2077-mods better!
