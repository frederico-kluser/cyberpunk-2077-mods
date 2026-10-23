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

Alternatives considered:

| Approach | Why it was rejected |
| --- | --- |
| TweakDB `HeadshotDamageMultiplier` | It is a multiplier on final damage. Boss caps and armour still apply, and a high enough multiplier is clamped. |
| `attackComputed.SetAttackValue(maxHealth * N)` | Goes through the whole damage pipeline, so it is clamped on bosses and reduced by resistances; also produces absurd damage floaters. |
| `NPCPuppet.Kill()` | Bypasses the damage pipeline entirely and has different anim/ragdoll semantics; harder to keep compatible with other damage mods. |
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
| `SpareCivilians`, `SpareAllies` | Design choice: the mod is about adversaries, not a civilian massacre. |
| `SpareProtectedTargets` | `GetImmortality()` and the `IsInvulnerable` stat catch god-mode and quest-critical NPCs. |

Note that the mod does **not** check `hitFlag.Headshot`: that flag is suppressed
by `HeadshotImmunity` and by a zero headshot multiplier, which would make the
mod silently inert on some targets. It checks the hit shape directly, which is
what "the bullet hit the head" actually means.

## 4. Compatibility notes

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

## 5. References

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
