/*
 * Lethal Headshots — every headshot kills. Brute force edition.
 *
 * Kill: DamageSystem.ProcessLocalizedDamage is wrapped (the same place where
 * the vanilla game decides that a hit was a headshot). When the hit qualifies
 * the mod marks it with hitFlag.Kill AND calls ScriptedPuppet.Kill() on the
 * spot — the game's own force-kill — so the target dies no matter what the
 * rest of the pipeline does with the flag.
 *
 * Label: a DelayCallback ticker polls the aim every ~0.12 s (the engine's aim
 * projection never fires reliably) and drives a three-channel overlay, so a
 * missing label can be diagnosed exactly:
 *   1. crosshair tint  — white (nothing) / orange (target under the crosshair)
 *                        / red (over a killable head). Lives OUTSIDE the
 *                        custom-widget layer: if this works, the ticker works.
 *   2. probe bars      — blue bar = a target is under the crosshair,
 *                        red bar = over the head (DebugProbes in Config).
 *   3. "QUE OTA" text  — the actual label, inkText with a font family that is
 *                        proven to exist in this game install (arame, found
 *                        in tweakdb.bin; orbitron was never verified locally).
 *
 * The widgets live in gameuiCrosshairContainerController's widget tree; the
 * player only carries a bridge plus the running ticker, re-established on
 * every OnPlayerAttach.
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

// Overlay widgets, created lazily inside the controller's widget tree.
@addField(gameuiCrosshairContainerController)
public let m_lhText: ref<inkText>;

@addField(gameuiCrosshairContainerController)
public let m_lhProbeTarget: ref<inkRectangle>;

@addField(gameuiCrosshairContainerController)
public let m_lhProbeHead: ref<inkRectangle>;

// ---------------------------------------------------------------------------
// Aim ticker: polls the crosshair-over-head state and drives the overlay.
// ---------------------------------------------------------------------------

public class LhAimTicker extends DelayCallback {

  private let m_ctrl: wref<gameuiCrosshairContainerController>;
  private let m_player: wref<PlayerPuppet>;
  private let m_overHead: Bool;
  private let m_targetSeen: Bool;
  private let m_msgTicks: Int32;
  private let m_ticks: Int32;
  private let m_delayId: DelayID;

  // Starts (or restarts) the ticker for a player/controller pair. A previous
  // ticker is retired (refs cleared + callback cancelled) instead of reused,
  // so no double schedules can stack — the pattern used by published mods.
  public final static func Start(player: ref<PlayerPuppet>, ctrl: ref<gameuiCrosshairContainerController>) -> Void {
    if !IsDefined(player) || !IsDefined(ctrl) {
      return;
    };

    if IsDefined(player.m_lhTicker) {
      let old: ref<LhAimTicker> = player.m_lhTicker;
      old.m_ctrl = null;
      old.m_player = null;
      let delaySystem: ref<DelaySystem> = GameInstance.GetDelaySystem(GetGameInstance());
      if IsDefined(delaySystem) && NotEquals(old.m_delayId, GetInvalidDelayID()) {
        delaySystem.CancelCallback(old.m_delayId);
      };
    };

    let ticker: ref<LhAimTicker> = new LhAimTicker();
    ticker.m_ctrl = ctrl;
    ticker.m_player = player;
    player.m_lhTicker = ticker;
    ticker.Schedule();

    // Life proof: the ticker started (visible without aiming at anything).
    // NOTE: the wording must NOT contain "QUE OTA" — that label is reserved
    // for the head case only, so the startup proof is unmistakable.
    if DebugProbes() {
      FTLog("LethalHeadshots: ticker iniciado");
      PushQueOtaMessage(player, "TICKER ATIVO");
    };
  }

  private final func Schedule() -> Void {
    let delaySystem: ref<DelaySystem> = GameInstance.GetDelaySystem(GetGameInstance());
    if IsDefined(delaySystem) {
      if NotEquals(this.m_delayId, GetInvalidDelayID()) {
        delaySystem.CancelCallback(this.m_delayId);
      };
      this.m_delayId = delaySystem.DelayCallback(this, 0.12, false);
    };
  }

  public func Call() -> Void {
    // Re-arm FIRST: if any logic below throws at runtime, the chain must not
    // die silently (a dead ticker explains every channel being dark).
    this.Schedule();

    // The HUD or the player is gone (loading screen, despawn): stop ticking.
    if !IsDefined(this.m_ctrl) || !IsDefined(this.m_player) {
      return;
    };

    let targetSeen: Bool;
    let overHead: Bool = IsCrosshairOnHead(this.m_player, targetSeen);
    let risingEdge: Bool = overHead && NotEquals(overHead, this.m_overHead);

    // Proofs FIRST (cheap and safe): they must keep working even if the widget
    // work at the end of the tick throws at runtime.
    if DebugProbes() {
      if targetSeen && NotEquals(targetSeen, this.m_targetSeen) {
        PushQueOtaMessage(this.m_player, "ALVO SOB A MIRA");
      };
      this.m_targetSeen = targetSeen;

      if risingEdge {
        this.m_msgTicks = 0;
        PushQueOtaMessage(this.m_player, "QUE OTA");
      } else {
        if overHead {
          this.m_msgTicks += 1;
          if this.m_msgTicks >= 16 {
            this.m_msgTicks = 0;
            PushQueOtaMessage(this.m_player, "QUE OTA");
          };
        } else {
          this.m_msgTicks = 0;
        };
      };
    };

    // Overlay LAST — the risky part. `fresh` rebuilds the widget tree from
    // scratch on every rising edge, so a widget the game detached (weapon
    // swap, holster, scene change) can never block the label again.
    this.m_ctrl.LhUpdateOverlay(targetSeen, overHead, risingEdge);
    this.m_overHead = overHead;

    if DebugProbes() {
      this.m_ticks += 1;
      if this.m_ticks == 1 {
        FTLog("LethalHeadshots: primeiro tick do ticker");
      };
      if risingEdge {
        FTLog("LethalHeadshots: cabeca sob a mira");
      };
    };
  }
}

// Vanilla HUD message through the UI_Notifications blackboard — the same path
// the game itself uses for warning messages (see player.SetWarningMessage).
func PushQueOtaMessage(player: ref<PlayerPuppet>, text: String) -> Void {
  let msg: SimpleScreenMessage;
  msg.isShown = true;
  msg.duration = 2.50;
  msg.message = text;
  msg.type = SimpleMessageType.Neutral;
  GameInstance.GetBlackboardSystem(player.GetGame()).Get(GetAllBlackboardDefs().UI_Notifications).SetVariant(GetAllBlackboardDefs().UI_Notifications.WarningMessage, ToVariant(msg), true);
}

// ---------------------------------------------------------------------------
// HUD overlay (tint + probe bars + "QUE OTA" text)
// ---------------------------------------------------------------------------

@wrapMethod(gameuiCrosshairContainerController)
protected cb func OnInitialize() -> Bool {
  let ret: Bool = wrappedMethod();
  this.m_lhText = null;
  this.m_lhProbeTarget = null;
  this.m_lhProbeHead = null;
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
  this.m_lhProbeTarget = null;
  this.m_lhProbeHead = null;
  let player: ref<PlayerPuppet> = playerGameObject as PlayerPuppet;
  if IsDefined(player) {
    player.m_lhCrosshair = this;
    LhAimTicker.Start(player, this);
  };
  return ret;
}

// Called every tick: refreshes all three channels. `fresh` rebuilds the
// overlay widgets from scratch — the game can detach them from the tree on
// weapon swap/holster/scene changes, and a stale ref would keep driving a dead
// widget forever (which is why the label used to work only once).
@addMethod(gameuiCrosshairContainerController)
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

  // Channel 1 — crosshair tint. If this changes colour in game, the ticker and
  // the head detection work, and any remaining problem is widget rendering.
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

  // Channels 2 and 3 — probe bars (debug) and the actual label.
  if IsDefined(this.m_lhProbeTarget) {
    this.m_lhProbeTarget.SetVisible(DebugProbes() && targetSeen);
  };
  if IsDefined(this.m_lhProbeHead) {
    this.m_lhProbeHead.SetVisible(DebugProbes() && overHead);
  };
  if IsDefined(this.m_lhText) {
    if overHead {
      // Re-assert the text on every show: the NativeDB notes that font-related
      // changes need a SetText/SetFontSize call to force a redraw.
      this.m_lhText.SetText("QUE OTA");
    };
    this.m_lhText.SetVisible(overHead);
  };
}

@addMethod(gameuiCrosshairContainerController)
private final func LhCreateOverlayWidgets(root: wref<inkCompoundWidget>) -> Void {
  // Probe bar: a target is under the crosshair (no font involved).
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

  // Probe bar: over a killable head (no font involved).
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

  // The label itself. Order matters: font family/style first, then size, then
  // SetText LAST — the NativeDB notes that font changes do not redraw a widget
  // unless SetText/SetFontSize runs afterwards. `raj` with `Medium` is the
  // game's own default font as used by the official wiki's inkText example.
  let text: ref<inkText> = new inkText();
  text.SetName(n"LethalHeadshotsQueOta");
  // Canonical pattern from the wiki's working HUD example: font family+style
  // in one call, then size, then SetText, then Reparent LAST.
  text.SetFontFamily("base\\gameplay\\gui\\fonts\\raj\\raj.inkfontfamily", n"Medium");
  text.SetFontSize(44);
  // Documented inkText setup: explicit margin + wrapping + fit-to-content, all
  // BEFORE Reparent, so the draw area can never end up with zero size.
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
// Aim geometry: is the crosshair over the target's head?
// ---------------------------------------------------------------------------

// Uses the game's own CROSSHAIR APIs (GetTrackedTargetObject /
// GetObjectClosestToCrosshair + GetDefaultCrosshairData), not the scanner's
// GetLookAtObject — that one goes quiet during combat, which is why the label
// only ever showed its startup message. The head test is pure geometry: the
// perpendicular distance from the crosshair RAY to the target's "Head" slot
// (the same slot the game's own AI aims at) — pose independent.
func IsCrosshairOnHead(player: ref<PlayerPuppet>, out targetSeen: Bool) -> Bool {
  targetSeen = false;

  let targetingSystem: ref<TargetingSystem> = GameInstance.GetTargetingSystem(player.GetGame());
  if !IsDefined(targetingSystem) {
    return false;
  };

  // 1) The aim-assist tracked target; 2) the object closest to the crosshair;
  // 3) the scanner look-at as a last resort.
  let target: ref<ScriptedPuppet> = targetingSystem.GetTrackedTargetObject(player) as ScriptedPuppet;
  if !IsDefined(target) {
    let query: TargetSearchQuery;
    query.testedSet = TargetingSet.Visible;
    query.ignoreInstigator = true;
    query.filterObjectByDistance = true;
    query.maxDistance = 300.00;
    let angleDistance: EulerAngles;
    target = targetingSystem.GetObjectClosestToCrosshair(player, angleDistance, query) as ScriptedPuppet;
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

  // The crosshair ray: origin + forward.
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
    // |toHead x fwd| is the perpendicular distance to the ray (fwd normalized).
    let perp: Vector4 = Vector4.Cross(toHead, fwd);
    return Vector4.LengthSquared(perp) < 0.25;
  };

  // No Head slot: assume a standing humanoid and use the height above the root.
  let rootPos: Vector4 = target.GetWorldPosition();
  return rayPos.Z - rootPos.Z > 1.20;
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

    // Self-heal: this path is proven alive in game (headshots kill), so it also
    // revives the aim ticker whenever its chain is missing.
    let shooter: ref<PlayerPuppet> = hitEvent.attackData.GetInstigator() as PlayerPuppet;
    if IsDefined(shooter) && IsDefined(shooter.m_lhCrosshair) && !IsDefined(shooter.m_lhTicker) {
      LhAimTicker.Start(shooter, shooter.m_lhCrosshair);
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
