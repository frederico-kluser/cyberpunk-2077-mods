/*
 * Lethal Headshots — every headshot kills. Brute force edition.
 *
 * Kill: DamageSystem.ProcessLocalizedDamage is wrapped (the same place where
 * the vanilla game decides that a hit was a headshot). When the hit qualifies
 * the mod marks it with hitFlag.Kill AND calls ScriptedPuppet.Kill() on the
 * spot — the game's own force-kill — and fires the "QUE OTA" toast.
 *
 * Label: the red "QUE OTA" text sits above the crosshair ONLY while the
 * crosshair is over the target's HEAD (15 cm sphere around the "Head" slot —
 * the same slot the game's AI aims at — plus the game's own HeadTarget
 * component filter). It is driven by the callbacks proven to fire in game
 * (crosshair state changes, PlayerPuppet.OnAction, real hits) — never by a
 * DelayCallback ticker and never through GetGameInstance() inside UI hooks
 * (both proved dead/null there by the logging session).
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

// The label widget + state, owned by the ACTIVE crosshair controller.
@addField(gameuiCrosshairBaseGameController)
public let m_lhText: ref<inkText>;

@addField(gameuiCrosshairBaseGameController)
public let m_lhOverHead: Bool;

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

// Every crosshair state change (weapon ready, hip fire, aim, reload...).
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

// The player is given here as a parameter — no globals needed.
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

// The kill path (proven hot) — the toast fires here, on the headshot kill.
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
    let shooter: ref<PlayerPuppet> = hitEvent.attackData.GetInstigator() as PlayerPuppet;
    if IsDefined(target) {
      target.Kill(hitEvent.attackData.GetInstigator());
    };

    // The toast: only here — only on a headshot kill.
    if IsDefined(shooter) {
      PushQueOtaMessage(shooter);
    };
  };

  let instigator: ref<PlayerPuppet> = hitEvent.attackData.GetInstigator() as PlayerPuppet;
  if IsDefined(instigator) && IsDefined(instigator.m_lhCrosshairBase) {
    instigator.m_lhCrosshairBase.LhPoll(instigator);
  };
}

// ---------------------------------------------------------------------------
// The per-aim poll — the label only
// ---------------------------------------------------------------------------

@addMethod(gameuiCrosshairBaseGameController)
public final func LhPoll(player: ref<PlayerPuppet>) -> Void {
  if !IsDefined(player) {
    return;
  };

  let targetSeen: Bool;
  let overHead: Bool = IsCrosshairOnHead(player, targetSeen);
  let risingEdge: Bool = overHead && NotEquals(overHead, this.m_lhOverHead);
  this.LhUpdateOverlay(overHead, risingEdge);
  this.m_lhOverHead = overHead;
}

// The toast on a headshot kill — the only screen notification this mod shows.
func PushQueOtaMessage(player: ref<PlayerPuppet>) -> Void {
  if !IsDefined(player) {
    return;
  };
  let msg: SimpleScreenMessage;
  msg.isShown = true;
  msg.duration = 2.00;
  msg.message = "QUE OTA";
  msg.type = SimpleMessageType.Neutral;
  GameInstance.GetBlackboardSystem(player.GetGame()).Get(GetAllBlackboardDefs().UI_Notifications).SetVariant(GetAllBlackboardDefs().UI_Notifications.WarningMessage, ToVariant(msg), true);
}

// ---------------------------------------------------------------------------
// Aim geometry: is the crosshair over the target's HEAD?
// ---------------------------------------------------------------------------

// The head test is deliberately tight: a 15 cm sphere around the "Head" slot
// (the same slot the game's AI aims at) measured against the crosshair RAY.
// The previous 50 cm radius swallowed the whole torso — that is why the label
// appeared over any body part.
func IsCrosshairOnHead(player: ref<PlayerPuppet>, out targetSeen: Bool) -> Bool {
  targetSeen = false;

  let game: GameInstance = player.GetGame();
  let targetingSystem: ref<TargetingSystem> = GameInstance.GetTargetingSystem(game);
  if !IsDefined(targetingSystem) {
    return false;
  };

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

  // The game's own head-target filter: no head near the crosshair, no label.
  let headQuery: TargetSearchQuery;
  headQuery.testedSet = TargetingSet.Visible;
  headQuery.ignoreInstigator = true;
  headQuery.filterObjectByDistance = true;
  headQuery.maxDistance = 300.00;
  TargetSearchQuery.SetComponentFilter(headQuery, TargetComponentFilterType.HeadTarget);
  let headAngle: EulerAngles;
  let headComponent: wref<IPlacedComponent> = targetingSystem.GetComponentClosestToCrosshair(player, headAngle, headQuery);
  if !IsDefined(headComponent) {
    return false;
  };

  // Geometry: the crosshair ray must pass within 15 cm of the Head slot.
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
    return Vector4.LengthSquared(perp) < 0.0225;
  };

  // No Head slot on this target: no label (never guess over the body).
  return false;
}

// ---------------------------------------------------------------------------
// The label widget
// ---------------------------------------------------------------------------

// `fresh` rebuilds the widget on every rising edge, so a widget the game
// detached (weapon swap, holster, scene change) can never block the label.
@addMethod(gameuiCrosshairBaseGameController)
public final func LhUpdateOverlay(overHead: Bool, fresh: Bool) -> Void {
  let root: wref<inkCompoundWidget> = this.GetRootCompoundWidget();
  if !IsDefined(root) {
    return;
  };

  if fresh || !IsDefined(this.m_lhText) {
    this.m_lhText = null;
    this.LhCreateLabel(root);
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
private final func LhCreateLabel(root: wref<inkCompoundWidget>) -> Void {
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
