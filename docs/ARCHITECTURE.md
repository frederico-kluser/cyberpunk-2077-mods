# Architecture — how Lethal Headshots hooks the damage pipeline

This document explains the engine behaviour the mod relies on. It is based on
the decompiled 2.5 scripts (the canonical reference used by the modding
community, linked below) and on type-checking the mod against the retail
`r6/cache/final.redscripts` bundle.

## 1. Where a hit is processed

`DamageSystem` runs each hit event through four stages:

```text
PreProcess  →  Process  →  ProcessHitReaction  →  PostProcess
```

Inside `PreProcess`, the game computes the hit data in `ModifyHitData`:

```text
DamageManager.ModifyHitData(hitEvent)
  → ProcessDamageReduction(hitEvent)
  → ProcessLocalizedDamage(hitEvent)     ← the mod wraps this
  → ProcessInstantKill(hitEvent)         ← consumes hitFlag.Kill
  → ProcessDodge / ProcessEvasion / ProcessMitigation
  → ProcessPlayerIncomingDamageMultiplier
```

`ProcessLocalizedDamage` is where the vanilla game:

1. ignores non-player instigators and area-of-effect attacks;
2. resolves the hit shape (`hitRepresentationResult.hitShapes[0]`);
3. checks `HitShapeUserDataBase.IsHitReactionZoneHead(...)`;
4. adds `hitFlag.Headshot` when the attack is ranged/direct/thrown, the headshot
   multiplier is non-zero and the target has no `HeadshotImmunity`.

Because `ProcessInstantKill` is called **right after** `ProcessLocalizedDamage`,
a flag added by a wrapper of the latter is consumed in the same hit, before any
damage is dealt.

## 2. Why `hitFlag.Kill`

`ProcessInstantKill` implements the engine's native instant kill:

```text
if attackData.HasFlag(hitFlag.Kill):
    AddFlag(DealNoDamage)
    AddFlag(DontShowDamageFloater)
    StatPoolsSystem.RequestSettingStatPoolMinValue(
        targetID, gamedataStatPoolType.Health, attackData.GetInstigator())
```

That path:

- bypasses armour, resistances, mitigation and the per-hit damage cap that
  bosses and MaxTac use (`MaxPercentDamageTakenPerHit`);
- preserves the instigator, so kill credit, loot and quest/neutralisation events
  still run;
- does **not** show a damage number or award damage XP for the killing hit.

On top of the flag, the mod calls `ScriptedPuppet.Kill(instigator)` on the
target in the same hit — the game's force kill (it zeroes the Health stat pool
with `RequestSettingStatPoolValueIgnoreChangeMode` and logs a `ForceKill`
telemetry entry). The two mechanisms use the same stat-pool channel, so calling
both is safe and guarantees the death even if another mod eats the flag.

Alternatives considered:

| Approach | Why it was rejected |
| --- | --- |
| TweakDB `HeadshotDamageMultiplier` | It is a multiplier on final damage. Boss caps and armour still apply, and a high enough multiplier is clamped. |
| `attackComputed.SetAttackValue(maxHealth * N)` | Goes through the whole damage pipeline, so it is clamped on bosses and reduced by resistances; also produces absurd damage floaters. |
| `NPCPuppet.Kill()` alone | Different anim/ragdoll semantics and it bypasses the damage pipeline; today it is used only as a complement to `hitFlag.Kill`, never instead of it. |
| CET Lua observer | Adds a hard dependency (CET) for something Redscript does natively. |

## 3. Safety guards

The wrapper only marks the hit when every guard passes:

| Guard | Why |
| --- | --- |
| `!hitEvent.projectionPipeline` | The same pipeline runs when the player merely *aims* at a target (hit projection). Without this guard, aiming at a head would kill. |
| `instigator.IsPlayer()` | NPCs must never trigger the effect; it also keeps the player safe from enemy headshots. |
| `!AttackData.IsAreaOfEffect(...)` | Explosions have no meaningful head hit shape. |
| `target as ScriptedPuppet`, alive, not player | Devices, vehicles and corpses are out of scope. |
| `IsHitReactionZoneHead(hitShape)` | Uses the engine's own head classification (`EHitReactionZone.Head`), not a distance or bone-name heuristic. |
| `SpareCivilians`, `SpareAllies` | Optional mercy (off by default): flip them on to spare civilians or friendly-attitude characters. |
| `SpareProtectedTargets` | Optional mercy for god-mode/quest-critical NPCs (`GetImmortality()`, `IsInvulnerable`). **Off by default** — the brute policy spares nobody. |

Note that the mod does **not** check `hitFlag.Headshot`: that flag is suppressed
by `HeadshotImmunity` and by a zero headshot multiplier, which would make the
mod silently inert on some targets. It checks the hit shape directly, which is
what "the bullet hit the head" actually means.

## 4. The aim preview label ("QUE OTA")

The label is driven by an aim **ticker**, not by engine events. A
`DelayCallback` subclass (`LhAimTicker`) re-arms itself every ~0.12 s and asks,
per tick:

```text
TargetingSystem.GetLookAtObject(player, withLOS, ignoreTransparent)  → target
TargetingSystem.GetLookAtPosition(player, withLOS, ignoreTransparent) → aim point
AIActionHelper.GetTargetSlotPosition(target, "Head", out headPos)     → head slot
over a head := Distance(aimPoint, headPos) < 0.30
```

The `Head` slot is the same slot the game's own AI uses to aim at heads
(`AIActionHelper`, `aiLookats`, headshot prereqs), so the test is pose
independent — standing, crouched or seated — and needs no bone-name or bbox
heuristics (a height-above-root heuristic remains as fallback for targets
without the slot). The result is filtered by the same `ShouldSpare` config as
the kill, so the label previews exactly what the next shot would do.

History: earlier versions sourced the signal from the engine's aim projection
(`gameHitEvent.projectionPipeline`), which the vanilla
`CheckProjectionPipelineTargetConditions` only lets through on target/body-part
transitions. That pipeline never fires reliably in game (it appears to depend
on aim-assist internals), so the label never appeared; polling the aim removes
that whole dependency. `DamageSystem.ClearPreviewTargetStruct()` is still
wrapped for an instant hide when the crosshair leaves every target (holster,
scene change).

The widget is a plain `inkText` created lazily under the root widget of
`gameuiCrosshairContainerController` (font `orbitron`, anchored centered,
140 px above the crosshair). It is owned by the **controller**, not by the
player puppet: the HUD can initialize before the player exists and is rebuilt
across loading screens, so the player only carries a bridge (`m_lhCrosshair`)
and the running ticker, re-established in `OnInitialize` and — reliably, with
the player as a parameter — in `OnPlayerAttach`. Capturing the HUD root once
through `GetPlayer()` in `OnInitialize` (the 1.0.x approach) silently failed
whenever the player was not ready yet.

## 5. Compatibility notes

- **Redscript module name:** `LethalHeadshots`. Redscript resolves `@wrapMethod`
  chains in load order; wrapping (not replacing) keeps other damage mods alive.
- **REDmod and RED4ext are not required.** The mod is a plain `r6/scripts`
  Redscript mod; the engine compiles it at launch through
  `engine/config/base/scripts.ini`.
- **Other `@replaceMethod(DamageSystem.ProcessLocalizedDamage)` mods** can bypass
  the wrapper. If a damage mod misbehaves, test with only one enabled.
- **Patch changes:** `ProcessLocalizedDamage` has been stable since 2.0, but a
  future patch can change it. The type-check in `tools/validate.ps1` catches
  signature/API breaks as soon as the game bundle is updated.

## 6. References

- Decompiled game scripts (community reference):
  <https://codeberg.org/adamsmasher/cyberpunk>
  - `cyberpunk/damage/damageSystem.swift` — `ModifyHitData`,
    `ProcessLocalizedDamage`, `ProcessInstantKill`
  - `cyberpunk/damage/statPoolsManager.swift` — `ApplyDamage`, damage caps
  - `core/components/hitRepresentationComponent.swift` —
    `HitShapeUserDataBase.IsHitReactionZoneHead`
- REDmodding wiki — hooks and damage pipeline:
  <https://wiki.redmodding.org/scripting-cyberpunk>
- Redscript releases and compiler: <https://github.com/jac3km4/redscript>
- RED4ext: <https://github.com/WopsS/RED4ext>
