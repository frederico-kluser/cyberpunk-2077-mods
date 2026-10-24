/*
 * Lethal Headshots — every headshot kills.
 *
 * Hook: DamageSystem.ProcessLocalizedDamage, the same place where the vanilla
 * game decides that a hit was a headshot (see docs/ARCHITECTURE.md).
 *
 * Instead of scaling damage (which bosses clamp and armour/resistance reduce),
 * the mod marks the hit with hitFlag.Kill. DamageSystem.ProcessInstantKill runs
 * immediately after ProcessLocalizedDamage and drops the target's Health stat
 * pool to its minimum, which is the engine's own instant-kill path.
 *
 * The on-screen "QUE OTA" label is a plain inkText added to the game's own
 * crosshair container — no Cyber Engine Tweaks, no Codeware, no RED4ext.
 */

module LethalHeadshots

import LethalHeadshots.Config.*

// True while the crosshair is over a head that the mod would kill.
@addField(PlayerPuppet)
public let m_lhAimOnHead: Bool;

// Root of the game's crosshair container, captured when the HUD initializes.
@addField(PlayerPuppet)
public let m_lhHudRoot: wref<inkCompoundWidget>;

// The label widget, created lazily on the first headshot aim.
@addField(PlayerPuppet)
public let m_lhText: wref<inkText>;

@wrapMethod(gameuiCrosshairContainerController)
protected cb func OnInitialize() -> Bool {
  let ret: Bool = wrappedMethod();
  let player: ref<PlayerPuppet> = GetPlayer(GetGameInstance());
  if IsDefined(player) {
    player.m_lhHudRoot = this.GetRootWidget() as inkCompoundWidget;
    player.m_lhText = null;
    player.m_lhAimOnHead = false;
  };
  return ret;
}

@wrapMethod(DamageSystem)
private final func ProcessLocalizedDamage(hitEvent: ref<gameHitEvent>) -> Void {
  wrappedMethod(hitEvent);

  // The projection pipeline runs while the player aims. Use it to show the
  // label, without touching the hit itself.
  if hitEvent.projectionPipeline {
    UpdateAimLabel(hitEvent);
    return;
  };

  if IsLethalHeadshot(hitEvent) {
    hitEvent.attackData.AddFlag(hitFlag.Kill, n"LethalHeadshots");
  };
}

// The preview target is cleared when the crosshair leaves every target, which
// is the signal to hide the label.
@wrapMethod(DamageSystem)
public final func ClearPreviewTargetStruct() -> Void {
  wrappedMethod();
  let player: ref<PlayerPuppet> = GetPlayer(GetGameInstance());
  if IsDefined(player) {
    player.m_lhAimOnHead = false;
    SetQueOtaVisible(player, false);
  };
}

func UpdateAimLabel(hitEvent: ref<gameHitEvent>) -> Void {
  let target: ref<ScriptedPuppet> = hitEvent.target as ScriptedPuppet;
  if !IsDefined(target) || target.IsDead() || target.IsPlayer() {
    return;
  };

  let player: ref<PlayerPuppet> = GetPlayer(target.GetGame());
  if !IsDefined(player) {
    return;
  };

  let overHead: Bool = IsHeadshot(hitEvent) && !ShouldSpare(target);
  if Equals(overHead, player.m_lhAimOnHead) {
    return;
  };
  player.m_lhAimOnHead = overHead;
  SetQueOtaVisible(player, overHead);
}

func SetQueOtaVisible(player: ref<PlayerPuppet>, visible: Bool) -> Void {
  if !visible {
    if IsDefined(player.m_lhText) {
      player.m_lhText.SetVisible(false);
    };
    return;
  };

  if !IsDefined(player.m_lhHudRoot) {
    return;
  };

  if !IsDefined(player.m_lhText) {
    let text: ref<inkText> = new inkText();
    text.SetText("QUE OTA");
    text.SetFontFamily("base\\gameplay\\gui\\fonts\\orbitron\\orbitron.inkfontfamily");
    text.SetFontStyle(n"Bold");
    text.SetFontSize(44);
    text.SetAnchor(inkEAnchor.Centered);
    text.SetAnchorPoint(0.5, 0.5);

    let position: Vector2;
    position.X = 0.00;
    position.Y = -140.00;
    text.SetTranslation(position);

    let color: HDRColor;
    color.Red = 1.00;
    color.Green = 0.10;
    color.Blue = 0.10;
    color.Alpha = 1.00;
    text.SetTintColor(color);

    text.Reparent(player.m_lhHudRoot);
    player.m_lhText = text;
  };

  player.m_lhText.SetVisible(true);
}

/*
 * A hit is lethal when all of the following are true:
 *  - it is a real hit, not the aim-assist projection pipeline;
 *  - the player is the instigator;
 *  - it is not area-of-effect damage (grenades, explosions);
 *  - the target is a living, non-player puppet;
 *  - the hit shape is the head;
 *  - the target is not spared by the configuration.
 */
func IsLethalHeadshot(hitEvent: ref<gameHitEvent>) -> Bool {
  if hitEvent.projectionPipeline {
    return false;
  };

  let attackData: ref<AttackData> = hitEvent.attackData;
  if !IsDefined(attackData) {
    return false;
  };

  let instigator: wref<GameObject> = attackData.GetInstigator();
  if !IsDefined(instigator) || !instigator.IsPlayer() {
    return false;
  };

  if AttackData.IsAreaOfEffect(attackData.GetAttackType()) {
    return false;
  };

  let target: ref<ScriptedPuppet> = hitEvent.target as ScriptedPuppet;
  if !IsDefined(target) || target.IsDead() || target.IsPlayer() {
    return false;
  };

  if !IsHeadshot(hitEvent) {
    return false;
  };

  return !ShouldSpare(target);
}

func IsHeadshot(hitEvent: ref<gameHitEvent>) -> Bool {
  let hitShapes: array<HitShapeData> = hitEvent.hitRepresentationResult.hitShapes;
  if ArraySize(hitShapes) == 0 {
    return false;
  };

  let userData: ref<HitShapeUserDataBase> = DamageSystemHelper.GetHitShapeUserDataBase(hitShapes[0]);
  if !IsDefined(userData) {
    return false;
  };

  return HitShapeUserDataBase.IsHitReactionZoneHead(userData);
}

func ShouldSpare(target: ref<ScriptedPuppet>) -> Bool {
  if SpareCivilians() && target.IsCharacterCivilian() {
    return true;
  };

  if SpareAllies() {
    let player: ref<PlayerPuppet> = GetPlayer(target.GetGame());
    if IsDefined(player) && Equals(target.GetAttitudeTowards(player), EAIAttitude.AIA_Friendly) {
      return true;
    };
  };

  if SpareProtectedTargets() {
    let godMode: gameGodModeType;
    if GetImmortality(target, godMode) {
      return true;
    };

    let stats: ref<StatsSystem> = GameInstance.GetStatsSystem(target.GetGame());
    if stats.GetStatValue(Cast<StatsObjectID>(target.GetEntityID()), gamedataStatType.IsInvulnerable) > 0.00 {
      return true;
    };
  };

  return false;
}
