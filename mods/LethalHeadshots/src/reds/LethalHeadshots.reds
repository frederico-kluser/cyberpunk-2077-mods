/*
 * Lethal Headshots — every headshot kills. Brute force edition.
 *
 * Kill: DamageSystem.ProcessLocalizedDamage is wrapped (the same place where
 * the vanilla game decides that a hit was a headshot). When the hit qualifies
 * the mod marks it with hitFlag.Kill AND calls ScriptedPuppet.Kill() on the
 * spot — the game's own force-kill.
 *
 * Label ("QUE OTA"): driven by the game's own CROSSHAIR STATE CHANGES and by
 * PlayerPuppet.OnAction — the callbacks the logging session proved to fire
 * reliably. It does NOT use a DelayCallback ticker (proved dead: zero ticks
 * ever fired) nor GetGameInstance() inside UI callbacks (proved null there).
 * The player is cached from OnPlayerAttach's parameter and resolved through
 * GameInstance.GetPlayerSystem().GetLocalPlayerMainGameObject() as fallback —
 * both proven patterns from the game's own code.
 *
 * Head test: the crosshair ray (GetDefaultCrosshairData) against the target's
 * "Head" slot — the same slot the game's AI aims at. The aim queries
 * (GetObjectClosestToCrosshair / GetTrackedTargetObject / GetLookAtObject)
 * were proven to find targets in game (LogSentry aim_probe found=CAB).
 */

module LethalHeadshots

import LethalHeadshots.Config.*

// Player cached on attach (UI callbacks cannot see the player through
// GetGameInstance() — the logging session proved it).
@addField(gameuiCrosshairBaseGameController)
public let m_lhPlayer: wref<PlayerPuppet>;

// Bridge back to the active crosshair controller, for out-of-UI drivers.
@addField(PlayerPuppet)
public let m_lhCrosshairBase: wref<gameuiCrosshairBaseGameController>;

// Throttle for the per-input driver.
@addField(PlayerPuppet)
public let m_lhLastPoll: Float;

// Overlay widgets + state, owned by the ACTIVE crosshair controller.
@addField(gameuiCrosshairBaseGameController)
public let m_lhText: ref<inkText>;

@addField(gameuiCrosshairBaseGameController)
public let m_lhProbeTarget: ref<inkRectangle>;

@addField(gameuiCrosshairBaseGameController)
public let m_lhProbeHead: ref<inkRectangle>;

@addField(gameuiCrosshairBaseGameController)
public let m_lhOverHead: Bool;

@addField(gameuiCrosshairBaseGameController)
public let m_lhTargetSeen: Bool;

@addField(gameuiCrosshairBaseGameController)
public let m_lhMsgTicks: Int32;

// ---------------------------------------------------------------------------
// Player resolution — proven patterns only
// ---------------------------------------------------------------------------

func LhResolvePlayer() -> ref<PlayerPuppet> {
  let player: ref<PlayerPuppet> = GameInstance.GetPlayerSystem(GetGameInstance()).GetLocalPlayerMainGameObject() as PlayerPuppet;
  if IsDefined(player) {
    return player;
  };
  return GetPlayer(GetGameInstance());
}

// ---------------------------------------------------------------------------
// Drivers — only callbacks proven to fire in game
// ---------------------------------------------------------------------------

// The main driver: the game calls this on every crosshair state change
// (weapon ready, hip fire, aim, reload...) — literally "every time you aim".
@wrapMethod(gameuiCrosshairBaseGameController)
protected func OnCrosshairStateChange(oldState: gamePSMCrosshairStates, newState: gamePSMCrosshairStates) -> Void {
  wrappedMethod(oldState, newState);
  if !IsDefined(this.m_lhPlayer) {
    this.m_lhPlayer = LhResolvePlayer();
    if IsDefined(this.m_lhPlayer) {
      this.m_lhPlayer.m_lhCrosshairBase = this;
    };
  };
  if IsDefined(this.m_lhPlayer) {
    this.LhPoll(this.m_lhPlayer);
  };
}

// The player is given to us here as a parameter — the only source that does
// not depend on any global.
@wrapMethod(gameuiCrosshairBaseGameController)
protected cb func OnPlayerAttach(playerPuppet: ref<GameObject>) -> Bool {
  let ret: Bool = wrappedMethod(playerPuppet);
  this.m_lhPlayer = playerPuppet as PlayerPuppet;
  if IsDefined(this.m_lhPlayer) {
    this.m_lhPlayer.m_lhCrosshairBase = this;
    this.LhPoll(this.m_lhPlayer);
  };
  return ret;
}

// Continuous driver: input actions fire constantly while the player moves the
// mouse/aims — throttled to ~8 polls/second.
@wrapMethod(PlayerPuppet)
protected cb func OnAction(action: ListenerAction, consumer: ListenerActionConsumer) -> Bool {
  let ret: Bool = wrappedMethod(action, consumer);
  let now: Float = EngineTime.ToFloat(GameInstance.GetEngineTime(this.GetGame()));
  if now - this.m_lhLastPoll > 0.12 {
    this.m_lhLastPoll = now;
    if IsDefined(this.m_lhCrosshairBase) {
      this.m_lhCrosshairBase.LhPoll(this);
    };
  };
  return ret;
}

// Extra driver on a proven-hot path (every real hit).
@wrapMethod(DamageSystem)
private final func ProcessLocalizedDamage(hitEvent: ref<gameHitEvent>) -> Void {
  wrappedMethod(hitEvent);

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

  let shooter: ref<PlayerPuppet> = hitEvent.attackData.GetInstigator() as PlayerPuppet;
  if IsDefined(shooter) && IsDefined(shooter.m_lhCrosshairBase) {
    shooter.m_lhCrosshairBase.LhPoll(shooter);
  };
}

// ---------------------------------------------------------------------------
// The per-aim poll
// ---------------------------------------------------------------------------

@addMethod(gameuiCrosshairBaseGameController)
public final func LhPoll(player: ref<PlayerPuppet>) -> Void {
  if !IsDefined(player) {
    return;
  };

  let targetSeen: Bool;
  let overHead: Bool = IsCrosshairOnHead(player, targetSeen);
  let risingEdge: Bool = overHead && NotEquals(overHead, this.m_lhOverHead);

  // Proofs first (cheap and safe): they must keep working even if the widget
  // work below throws at runtime.
  if DebugProbes() {
    if targetSeen && NotEquals(targetSeen, this.m_lhTargetSeen) {
      PushQueOtaMessage(player, "ALVO SOB A MIRA");
    };
    this.m_lhTargetSeen = targetSeen;

    if risingEdge {
      this.m_lhMsgTicks = 0;
      PushQueOtaMessage(player, "QUE OTA");
    } else {
      if overHead {
        this.m_lhMsgTicks += 1;
        if this.m_lhMsgTicks >= 16 {
          this.m_lhMsgTicks = 0;
          PushQueOtaMessage(player, "QUE OTA");
        };
      } else {
        this.m_lhMsgTicks = 0;
      };
    };
  };

  this.LhUpdateOverlay(targetSeen, overHead, risingEdge);
  this.m_lhOverHead = overHead;
}

// Vanilla HUD message through the UI_Notifications blackboard — the same path
// the game itself uses for warning messages (see player.SetWarningMessage).
func PushQueOtaMessage(player: ref<PlayerPuppet>, text: String) -> Void {
  if !IsDefined(player) {
    return;
  };
  let msg: SimpleScreenMessage;
  msg.isShown = true;
  msg.duration = 2.50;
  msg.message = text;
  msg.type = SimpleMessageType.Neutral;
  GameInstance.GetBlackboardSystem(player.GetGame()).Get(GetAllBlackboardDefs().UI_Notifications).SetVariant(GetAllBlackboardDefs().UI_Notifications.WarningMessage, ToVariant(msg), true);
}

// ---------------------------------------------------------------------------
// Aim geometry: is the crosshair over the target's head?
// ---------------------------------------------------------------------------

// The aim queries were proven to find targets in game (aim_probe found=CAB).
// The head test is pure geometry: the perpendicular distance from the
// crosshair RAY to the target's "Head" slot — pose independent.
func IsCrosshairOnHead(player: ref<PlayerPuppet>, out targetSeen: Bool) -> Bool {
  targetSeen = false;

  let game: GameInstance = player.GetGame();
  let targetingSystem: ref<TargetingSystem> = GameInstance.GetTargetingSystem(game);
  if !IsDefined(targetingSystem) {
    return false;
  };

  // 1) closest-to-crosshair (proven), 2) aim-assist tracked target,
  // 3) scanner look-at as a last resort.
  let query: TargetSearchQuery;
  query.testedSet = TargetingSet.Visible;
  query.ignoreInstigator = true;
  query.filterObjectByDistance = true;
  query.maxDistance = 300.00;
  let angleDistance: EulerAngles;
  let target: ref<ScriptedPuppet> = targetingSystem.GetObjectClosestToCrosshair(player, angleDistance, query) as ScriptedPuppet;
  if !IsDefined(target) {
    target = targetingSystem.GetTrackedTargetObject(player) as ScriptedPuppet;
  };
  if !IsDefined(target) {
    target = targetingSystem.GetLookAtObject(player, true, true) as ScriptedPuppet;
  };
  if !IsDefined(target) {
    target = targetingSystem.GetLookAtObject(player, false, false) as ScriptedPuppet;
  };

  if !IsDefined(target) || target.IsDead() || target.IsPlayer() {
    return false;
  };

  targetSeen = true;

  if ShouldSpare(target) {
    return false;
  };

  let rayPos: Vector4;
  let rayFwd: Vector4;
  targetingSystem.GetDefaultCrosshairData(player, rayPos, rayFwd);
  let fwd: Vector4 = Vector4.Normalize(rayFwd);

  let headPos: Vector4;
  if AIActionHelper.GetTargetSlotPosition(target, n"Head", headPos) {
    let toHead: Vector4 = headPos - rayPos;
    let along: Float = Vector4.Dot(toHead, fwd);
    if along <= 0.50 || along > 300.00 {
      return false;
    };
    let perp: Vector4 = Vector4.Cross(toHead, fwd);
    return Vector4.LengthSquared(perp) < 0.25;
  };

  let rootPos: Vector4 = target.GetWorldPosition();
  return rayPos.Z - rootPos.Z > 1.20;
}

// ---------------------------------------------------------------------------
// Overlay widgets (tint + probe bars + "QUE OTA" text)
// ---------------------------------------------------------------------------

// `fresh` rebuilds the widgets from scratch on every rising edge, so a widget
// the game detached (weapon swap, holster, scene change) can never block the
// label again.
@addMethod(gameuiCrosshairBaseGameController)
public final func LhUpdateOverlay(targetSeen: Bool, overHead: Bool, fresh: Bool) -> Void {
  let root: wref<inkCompoundWidget> = this.GetRootCompoundWidget();
  if !IsDefined(root) {
    return;
  };

  if fresh || !IsDefined(this.m_lhText) {
    this.m_lhText = null;
    this.m_lhProbeTarget = null;
    this.m_lhProbeHead = null;
    this.LhCreateOverlayWidgets(root);
  };

  let tint: HDRColor;
  if overHead {
    tint = new HDRColor(1.00, 0.10, 0.10, 1.00);
  } else {
    if targetSeen {
      tint = new HDRColor(1.00, 0.65, 0.10, 1.00);
    } else {
      tint = new HDRColor(1.00, 1.00, 1.00, 1.00);
    };
  };
  root.SetTintColor(tint);

  if IsDefined(this.m_lhProbeTarget) {
    this.m_lhProbeTarget.SetVisible(DebugProbes() && targetSeen);
  };
  if IsDefined(this.m_lhProbeHead) {
    this.m_lhProbeHead.SetVisible(DebugProbes() && overHead);
  };
  if IsDefined(this.m_lhText) {
    if overHead {
      // Re-assert the text on every show: font changes do not redraw without
      // a later SetText/SetFontSize (NativeDB).
      this.m_lhText.SetText("QUE OTA");
    };
    this.m_lhText.SetVisible(overHead);
  };
}

@addMethod(gameuiCrosshairBaseGameController)
private final func LhCreateOverlayWidgets(root: wref<inkCompoundWidget>) -> Void {
  let probeTarget: ref<inkRectangle> = new inkRectangle();
  probeTarget.SetName(n"LhProbeTarget");
  probeTarget.SetFitToContent(false);
  probeTarget.SetSize(28.00, 28.00);
  probeTarget.SetAnchor(inkEAnchor.Centered);
  probeTarget.SetAnchorPoint(0.50, 0.50);
  probeTarget.SetTranslation(0.00, -140.00);
  probeTarget.SetTintColor(new HDRColor(0.10, 0.45, 1.00, 1.00));
  probeTarget.SetVisible(false);
  probeTarget.Reparent(root);
  this.m_lhProbeTarget = probeTarget;

  let probeHead: ref<inkRectangle> = new inkRectangle();
  probeHead.SetName(n"LhProbeHead");
  probeHead.SetFitToContent(false);
  probeHead.SetSize(260.00, 12.00);
  probeHead.SetAnchor(inkEAnchor.Centered);
  probeHead.SetAnchorPoint(0.50, 0.50);
  probeHead.SetTranslation(0.00, -100.00);
  probeHead.SetTintColor(new HDRColor(1.00, 0.10, 0.10, 1.00));
  probeHead.SetVisible(false);
  probeHead.Reparent(root);
  this.m_lhProbeHead = probeHead;

  // Canonical pattern from the wiki's working HUD example: font family+style
  // in one call, then size, wrapping/margin/fit-to-content, SetText, and
  // Reparent LAST.
  let text: ref<inkText> = new inkText();
  text.SetName(n"LethalHeadshotsQueOta");
  text.SetFontFamily("base\\gameplay\\gui\\fonts\\raj\\raj.inkfontfamily", n"Medium");
  text.SetFontSize(44);
  text.SetMargin(0.00, 0.00, 0.00, 0.00);
  text.SetWrapping(true, 700.00);
  text.SetFitToContent(true);
  text.SetText("QUE OTA");
  text.SetOpacity(1.00);
  text.SetAnchor(inkEAnchor.Centered);
  text.SetAnchorPoint(0.50, 0.50);
  text.SetTranslation(0.00, -58.00);
  text.SetTintColor(new HDRColor(1.00, 0.10, 0.10, 1.00));
  text.SetVisible(false);
  text.Reparent(root);
  this.m_lhText = text;
}

// ---------------------------------------------------------------------------
// Kill pipeline
// ---------------------------------------------------------------------------

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
    let player: ref<PlayerPuppet> = LhResolvePlayer();
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
