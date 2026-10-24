# Lethal Headshots

**Every headshot kills.** One clean hit to the head drops the target — no damage
multipliers, no armour math, no boss damage cap.

- Version: **1.0.1**
- Game: **Cyberpunk 2077 2.5** (PC)
- Requires: [redscript](https://github.com/jac3km4/redscript/releases) **0.5.32+**
  (RED4ext is **not** required for this mod)
- License: MIT

## Install

1. Install **redscript** into the Cyberpunk 2077 folder (extract its release zip
   into the game root).
2. Download `LethalHeadshots-1.0.1.zip` from the
   [releases page](https://github.com/frederico-kluser/cyberpunk-2077-mods/releases).
3. Extract it into the Cyberpunk 2077 folder (merge folders). You should end up
   with:

   ```text
   Cyberpunk 2077\r6\scripts\LethalHeadshots\LethalHeadshots.reds
   Cyberpunk 2077\r6\scripts\LethalHeadshots\Config.reds
   ```

4. Start the game. Redscript compiles the files at launch.

From a clone of this repository you can also run:

```powershell
pwsh -File tools/deploy.ps1
```

### Uninstall

Delete `Cyberpunk 2077\r6\scripts\LethalHeadshots\`.

## Configuration

Edit `r6\scripts\LethalHeadshots\Config.reds`, change `true` to `false`, save and
restart the game (the scripts are compiled on startup).

| Option | Default | Effect |
| --- | --- | --- |
| `SpareCivilians` | `false` | When `true`, civilians survive a headshot. Off by default: any headshot kills. |
| `SpareAllies` | `false` | When `true`, characters with a friendly attitude towards V survive. Off by default. |
| `SpareProtectedTargets` | `false` | God-mode / scripted-invulnerable / quest-protected NPCs also take the kill. No exceptions by default — set to `true` if you want to protect quest-critical NPCs. |

```redscript
module LethalHeadshots.Config

public func SpareCivilians() -> Bool {
  return true;
}
```

## What counts as a headshot

A hit is lethal when **all** of these are true:

- the player is the instigator;
- it is a direct hit, not an area-of-effect explosion;
- it is a real hit, not the aim-assist "projection" pass (so merely aiming at a
  head never kills);
- the hit shape is the head (`EHitReactionZone.Head`);
- the target is a living, non-player puppet that is not spared by the config.

Consequences:

- **Firearms, melee, mantis blades, throwing weapons:** yes, if the hit lands on
  the head hit shape.
- **Grenades, explosions, vehicle collisions:** no — they are area-of-effect and
  do not target a body part.
- **Quickhacks and damage over time:** no — they do not go through the localized
  damage path.
- **Drones, mechs, turrets, vehicles:** only if the game exposes a head hit shape
  for them; otherwise they take normal damage. Weakspots are a separate system.

## Aim preview — the "QUE OTA" label

While aiming, the mod previews the outcome: a red **QUE OTA** label appears
above the crosshair whenever the crosshair is over a head that would die on the
next shot. It is purely cosmetic — aiming never kills.

The label is driven by an aim **ticker** (`DelayCallback`, ~8 checks/second),
not by the engine's aim-projection pipeline (which never fires reliably in
game). Each tick asks `TargetingSystem.GetLookAtObject`/`GetLookAtPosition`
where the crosshair ray hits and compares that point with the target's `Head`
slot — the same slot the game's own AI aims at — so the label is precise in any
pose (standing, crouched, seated).

While `DebugProbes` is on (the default), the overlay reports itself on four
channels so a missing label pinpoints its own cause: the crosshair **tints**
white → orange (target under it) → red (over a killable head); a **blue bar**
(target) and a **red bar** (head) appear above the crosshair; the red **QUE
OTA** `inkText` appears between them; and the game's own **HUD warning
message** shows `QUE OTA` too (vanilla `UI_Notifications` blackboard — it works
even if every custom widget fails). See `docs/TESTING.md` for how to read them.

The widget is owned by `gameuiCrosshairContainerController` — the controller
that owns the crosshair widget tree — and the player only carries a bridge plus
the running ticker, re-established on every `OnInitialize`/`OnPlayerAttach`.
Earlier versions captured the HUD root once through `GetPlayer()` (the HUD can
initialize before the player exists) and later relied on the aim-projection
pipeline for the signal; both silently failed, which is why the label never
appeared. Polling the aim removes that whole class of failure.

## How it works (short version)

The mod wraps `DamageSystem.ProcessLocalizedDamage` — the same function where
the vanilla game decides that a hit was a headshot. When the hit qualifies it
does two things, in this order:

1. adds `hitFlag.Kill` to the attack, so the engine's own `ProcessInstantKill`
   (running immediately afterwards) drops the target's Health stat pool to its
   minimum — the game's native instant-kill path;
2. calls `ScriptedPuppet.Kill()` on the target right away — the game's force
   kill — so the target dies even if another mod interferes with the flag.

This is deliberately **not** a damage multiplier:

- a multiplier is clamped by boss/MaxTac per-hit damage caps and reduced by
  armour, resistances and mitigation;
- writing a huge damage value into the hit would still pass through those
  systems, and would show absurd damage numbers;
- `hitFlag.Kill` is the engine's "this target dies now" signal.

The full pipeline walk-through, including the exact call order and the safety
guards, is in [docs/ARCHITECTURE.md](../../docs/ARCHITECTURE.md).

## Known limitations

- **No damage floater / no damage XP for the killing hit.** The instant-kill path
  sets Health directly instead of dealing damage, so the game does not show a
  number or award damage-based XP for that hit. Kill credit, loot and quest
  events still fire because the instigator is preserved.
- **Other mods that `@replaceMethod` the same function** (instead of wrapping it)
  can bypass this mod. Load order between Redscript mods is by module name; if
  another damage mod misbehaves, test with only this mod enabled.
- **Protected targets die too, by default.** `SpareProtectedTargets` is `false`:
  one-shotting a quest-critical NPC can break a playthrough. Set it to `true` to
  spare god-mode / quest-protected NPCs.
- **Patch 2.5 only.** Older redscript versions cannot compile the 2.5 script
  bundle, and older game versions may not expose the same damage pipeline.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Nothing happens | `r6\logs\redscript_rCURRENT.log` must end with a successful compile and list `LethalHeadshots`. |
| Compile error in the log | You are probably on redscript < 0.5.32 or on a different game patch. |
| Works on enemies, not on a specific boss | The boss is probably protected (god mode / quest flag) and `SpareProtectedTargets` is `true`. Defaults spare nobody. |
| Civilians survive a headshot | `SpareCivilians` is set to `true`; set it to `false` to kill everyone. |
| Headshots kill, but the "QUE OTA" label never appears | The label polls the aim ~8×/s while the HUD is attached; draw a weapon and check `r6\logs\redscript_rCURRENT.log` for a successful compile. If the game compiled an old `r6\scripts` copy, redeploy with `tools/deploy.ps1`. |

## Development

```powershell
pwsh -File tools/validate.ps1 -DownloadTools   # type-check against your 2.5 bundle
pwsh -File tools/deploy.ps1 -Launch            # deploy and start the game
```

See [docs/TESTING.md](../../docs/TESTING.md) for the full validation and manual
test matrix.



