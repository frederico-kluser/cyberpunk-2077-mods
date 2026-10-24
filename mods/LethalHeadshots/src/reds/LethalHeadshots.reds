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
 * crosshair container — no Cyber Engine Tweaks, no Codeware, no RED4ext. The
 * widget lives in gameuiCrosshairContainerController's own widget tree: that
 * controller always owns its root widget, while the player puppet may not
 * exist yet when the HUD initializes (and is a fresh instance after every
 * loading screen). The player only holds a bridge to the live controller,
 * re-established on every OnPlayerAttach.
 */

module LethalHeadshots

import LethalHeadshots.Config.*

// True while the crosshair is over a head that the mod would kill.
@addField(PlayerPuppet)
public let m_lhAimOnHead: Bool;

// Bridge to the live crosshair HUD controller, re-established on every
// OnInitialize / OnPlayerAttach so it survives loading screens and respawns.
@addField(PlayerPuppet)
public let m_lhCrosshair: wref<gameuiCrosshairContainerController>;

// The label widget, created lazily inside the controller's widget tree.
@addField(gameuiCrosshairContainerController)
public let m_lhText: ref<inkText>;

@wrapMethod(gameuiCrosshairContainerController)
protected cb func OnInitialize() -> Bool {
  let ret: Bool = wrappedMethod();
  this.m_lhText = null;
  let player: ref<PlayerPuppet> = GetPlayer(GetGameInstance());
  if IsDefined(player) {
    player.m_lhCrosshair = this;
    player.m_lhAimOnHead = false;
  };
  return ret;
}

// The reliable bridge point: OnPlayerAttach receives the player as a parameter,
// so it does not depend on GetPlayer() being ready when the HUD initializes.
@wrapMethod(gameuiCrosshairContainerController)
protected cb func OnPlayerAttach(playerGameObject: ref<GameObject>) -> Bool {
  let ret: Bool = wrappedMethod(playerGameObject);
  this.m_lhText = null;
  let player: ref<PlayerPuppet> = playerGameObject as PlayerPuppet;
  if IsDefined(player) {
    player.m_lhCrosshair = this;
    player.m_lhAimOnHead = false;
  };
  return ret;
}

// Shows or hides the label. The widget is created on first use, directly under
// the controller's root widget — the controller always has its widget tree, so
// creation never depends on the player or on the HUD initialization order.
@addMethod(gameuiCrosshairContainerController)
public final func LhSetLabelVisible(visible: Bool) -> Void {
  if !visible {
    if IsDefined(this.m_lhText) {
      this.m_lhText.SetVisible(false);
    };
    return;
  };

  if !IsDefined(this.m_lhText) {
    let root: wref<inkCompoundWidget> = this.GetRootCompoundWidget();
    if !IsDefined(root) {
      return;
    };

    let text: ref<inkText> = new inkText();
    text.SetName(n"LethalHeadshotsQueOta");
    text.SetText("QUE OTA");
    text.SetFontFamily("base\\gameplay\\gui\\fonts\\orbitron\\orbitron.inkfontfamily");
    text.SetFontStyle(n"Bold");
    text.SetFontSize(44);
    text.SetAnchor(inkEAnchor.Centered);
    text.SetAnchorPoint(0.50, 0.50);

    let position: Vector2;
    position.X = 0.00;
    position.Y = -140.00;
    text.SetTranslation(position);

    let color: HDRColor = new HDRColor(1.00, 0.10, 0.10, 1.00);
    text.SetTintColor(color);

    text.SetVisible(false);
    text.Reparent(root);
    this.m_lhText = text;
  };

  this.m_lhText.SetVisible(true);
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

// Mirrors the kill guards: the label is on exactly when the next shot on the
// head would kill. Anything else — an invalid, dead or player target included —
// counts as "not over a lethal head", so the label never sticks on screen.
func UpdateAimLabel(hitEvent: ref<gameHitEvent>) -> Void {
  let player: ref<PlayerPuppet> = GetPlayer(GetGameInstance());
  if !IsDefined(player) {
    return;
  };

  let target: ref<ScriptedPuppet> = hitEvent.target as ScriptedPuppet;
  let overHead: Bool = IsDefined(target) && !target.IsDead() && !target.IsPlayer() && IsHeadshot(hitEvent) && !ShouldSpare(target);
  if Equals(overHead, player.m_lhAimOnHead) {
    return;
  };

  player.m_lhAimOnHead = overHead;
  SetQueOtaVisible(player, overHead);
}

func SetQueOtaVisible(player: ref<PlayerPuppet>, visible: Bool) -> Void {
  if IsDefined(player.m_lhCrosshair) {
    player.m_lhCrosshair.LhSetLabelVisible(visible);
  };
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
