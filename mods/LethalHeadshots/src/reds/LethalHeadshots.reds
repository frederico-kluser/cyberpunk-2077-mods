/*
 * Lethal Headshots — every headshot kills. Brute force edition.
 *
 * Kill: DamageSystem.ProcessLocalizedDamage is wrapped (the same place where
 * the vanilla game decides that a hit was a headshot). When the hit qualifies
 * the mod marks it with hitFlag.Kill AND calls ScriptedPuppet.Kill() on the
 * spot — the game's own force-kill — so the target dies no matter what the
 * rest of the pipeline does with the flag.
 *
 * Label: the on-screen "QUE OTA" label does NOT rely on the aim-projection
 * pipeline (it never fires reliably in game). Instead a DelayCallback ticker
 * polls the aim every ~0.12 s: TargetingSystem.GetLookAtObject/Position plus
 * the target's "Head" slot (the same slot the game's AI aims with) tell
 * exactly whether the crosshair is over the head.
 *
 * The label is a plain inkText added to the game's own crosshair container —
 * no Cyber Engine Tweaks, no Codeware, no RED4ext. The widget lives in
 * gameuiCrosshairContainerController's widget tree; the player only carries a
 * bridge plus the running ticker, re-established on every OnPlayerAttach.
 */

module LethalHeadshots

import LethalHeadshots.Config.*

// Bridge to the live crosshair HUD controller, re-established on every
// OnInitialize / OnPlayerAttach so it survives loading screens and respawns.
@addField(PlayerPuppet)
public let m_lhCrosshair: wref<gameuiCrosshairContainerController>;

// The running aim ticker (strong ref so it outlives the delay system's hold).
@addField(PlayerPuppet)
public let m_lhTicker: ref<LhAimTicker>;

// The label widget, created lazily inside the controller's widget tree.
@addField(gameuiCrosshairContainerController)
public let m_lhText: ref<inkText>;

// ---------------------------------------------------------------------------
// Aim ticker: polls the crosshair-over-head state and drives the label.
// ---------------------------------------------------------------------------

public class LhAimTicker extends DelayCallback {

  private let m_ctrl: wref<gameuiCrosshairContainerController>;
  private let m_player: wref<PlayerPuppet>;
  private let m_overHead: Bool;

  // Starts (or restarts) the ticker for a player/controller pair. A previous
  // ticker is retired instead of reused, so no double schedules can stack.
  public final static func Start(player: ref<PlayerPuppet>, ctrl: ref<gameuiCrosshairContainerController>) -> Void {
    if !IsDefined(player) || !IsDefined(ctrl) {
      return;
    };

    if IsDefined(player.m_lhTicker) {
      player.m_lhTicker.m_ctrl = null;
      player.m_lhTicker.m_player = null;
    };

    let ticker: ref<LhAimTicker> = new LhAimTicker();
    ticker.m_ctrl = ctrl;
    ticker.m_player = player;
    ticker.m_overHead = false;
    player.m_lhTicker = ticker;
    ticker.Schedule();
  }

  private final func Schedule() -> Void {
    let delaySystem: ref<DelaySystem> = GameInstance.GetDelaySystem(GetGameInstance());
    if IsDefined(delaySystem) {
      delaySystem.DelayCallback(this, 0.12, false);
    };
  }

  public func Call() -> Void {
    // The HUD or the player is gone (loading screen, despawn): stop ticking.
    if !IsDefined(this.m_ctrl) || !IsDefined(this.m_player) {
      return;
    };

    let overHead: Bool = IsCrosshairOnHead(this.m_player);
    if NotEquals(overHead, this.m_overHead) {
      this.m_overHead = overHead;
      this.m_ctrl.LhSetLabelVisible(overHead);
    };

    this.Schedule();
  }
}

// ---------------------------------------------------------------------------
// HUD label
// ---------------------------------------------------------------------------

@wrapMethod(gameuiCrosshairContainerController)
protected cb func OnInitialize() -> Bool {
  let ret: Bool = wrappedMethod();
  this.m_lhText = null;
  let player: ref<PlayerPuppet> = GetPlayer(GetGameInstance());
  if IsDefined(player) {
    player.m_lhCrosshair = this;
    LhAimTicker.Start(player, this);
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
    LhAimTicker.Start(player, this);
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

// Instant hide when the crosshair leaves every target (holster, scene change).
@wrapMethod(DamageSystem)
public final func ClearPreviewTargetStruct() -> Void {
  wrappedMethod();
  let player: ref<PlayerPuppet> = GetPlayer(GetGameInstance());
  if IsDefined(player) && IsDefined(player.m_lhCrosshair) {
    player.m_lhCrosshair.LhSetLabelVisible(false);
  };
}

// ---------------------------------------------------------------------------
// Aim geometry: is the crosshair over the target's head?
// ---------------------------------------------------------------------------

// Brute force and pose independent: the aim ray's hit point is compared with
// the target's "Head" slot — the same slot the game's own AI aims at. Works
// standing, crouched or seated. Falls back to a height heuristic when the
// target has no Head slot.
func IsCrosshairOnHead(player: ref<PlayerPuppet>) -> Bool {
  let targetingSystem: ref<TargetingSystem> = GameInstance.GetTargetingSystem(player.GetGame());
  if !IsDefined(targetingSystem) {
    return false;
  };

  let target: ref<ScriptedPuppet> = targetingSystem.GetLookAtObject(player, true, true) as ScriptedPuppet;
  if !IsDefined(target) || target.IsDead() || target.IsPlayer() {
    return false;
  };

  if ShouldSpare(target) {
    return false;
  };

  let aimPoint: Vector4 = targetingSystem.GetLookAtPosition(player, true, true);
  let headPos: Vector4;
  if AIActionHelper.GetTargetSlotPosition(target, n"Head", headPos) {
    return Vector4.Distance(aimPoint, headPos) < 0.30;
  };

  // No Head slot: assume a standing humanoid and use the height above the root.
  let rootPos: Vector4 = target.GetWorldPosition();
  return aimPoint.Z - rootPos.Z > 1.35;
}

// ---------------------------------------------------------------------------
// Kill pipeline
// ---------------------------------------------------------------------------

@wrapMethod(DamageSystem)
private final func ProcessLocalizedDamage(hitEvent: ref<gameHitEvent>) -> Void {
  wrappedMethod(hitEvent);

  // The projection pipeline runs when the player merely aims: never kill on it.
  if hitEvent.projectionPipeline {
    return;
  };

  if IsLethalHeadshot(hitEvent) {
    // Flag for the engine's own instant-kill pass...
    hitEvent.attackData.AddFlag(hitFlag.Kill, n"LethalHeadshots");

    // ...and the brute call: kill the puppet right now, no matter what.
    let target: ref<ScriptedPuppet> = hitEvent.target as ScriptedPuppet;
    if IsDefined(target) {
      target.Kill(hitEvent.attackData.GetInstigator());
    };
  };
}

/*
 * A hit is lethal when all of the following are true:
 *  - it is a real hit, not the aim-assist projection pipeline;
 *  - the player is the instigator;
 *  - it is not area-of-effect damage (grenades, explosions);
 *  - the target is a living, non-player puppet;
 *  - the hit shape is the head;
 *  - the target is not spared by the configuration (defaults spare nobody).
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
