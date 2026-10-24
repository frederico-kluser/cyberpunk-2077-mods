/*
 * LogSentry — diagnostic capture mod.
 *
 * Traces every relevant engine callback through EVERY sink the vanilla game
 * offers, so the game's behaviour can be catalogued from the outside instead
 * of guessed:
 *
 *   1. FILES  — ResourceMetricsReportGenerator.WriteReportToFile() writes a
 *               real file whose NAME encodes the event ("LH_<seq>_<event>.txt").
 *               The file CONTENT is the engine's own metrics report; the
 *               CATALOG is the directory listing itself (who fired, in what
 *               order, how many times).
 *   2. HUD    — SimpleScreenMessage via the UI_Notifications blackboard: the
 *               one visual channel proven to render in this install.
 *   3. FTLog  — the engine's script log channel.
 *
 * It also runs the same aim query the label uses and reports the raw result,
 * so "no target" can be told apart from "query never runs".
 *
 * This mod is intentionally independent of LethalHeadshots: it must keep
 * working even when everything else fails.
 */

module LogSentry

// Running sequence number, so file names sort in event order.
@addField(PlayerPuppet)
public let m_sentrySeq: Int32;

// ---------------------------------------------------------------------------
// The three sinks
// ---------------------------------------------------------------------------

func SentryNote(tag: String) -> Void {
  let player: ref<PlayerPuppet> = GetPlayer(GetGameInstance());

  // Sink 1 — the file catalog (name = the log line).
  let seq: String = "0";
  if IsDefined(player) {
    player.m_sentrySeq += 1;
    seq = IntToString(player.m_sentrySeq);
  };
  ResourceMetricsReportGenerator.WriteReportToFile("LH_" + seq + "_" + tag + ".txt");

  // Sink 3 — engine log channel.
  FTLog("LogSentry: " + seq + " " + tag);

  // Sink 2 — visible HUD message (always; these events are sparse on purpose).
  if IsDefined(player) {
    let msg: SimpleScreenMessage;
    msg.isShown = true;
    msg.duration = 3.00;
    msg.message = "LH " + seq + " " + tag;
    msg.type = SimpleMessageType.Neutral;
    GameInstance.GetBlackboardSystem(player.GetGame()).Get(GetAllBlackboardDefs().UI_Notifications).SetVariant(GetAllBlackboardDefs().UI_Notifications.WarningMessage, ToVariant(msg), true);
  };
}

// ---------------------------------------------------------------------------
// Aim query report — the exact question the label needs answered
// ---------------------------------------------------------------------------

func SentryAimReport() -> Void {
  let player: ref<PlayerPuppet> = GetPlayer(GetGameInstance());
  if !IsDefined(player) {
    SentryNote("AIM_NOP");
    return;
  };

  let ts: ref<TargetingSystem> = GameInstance.GetTargetingSystem(player.GetGame());
  if !IsDefined(ts) {
    SentryNote("AIM_NOTS");
    return;
  };

  let tracked: ref<GameObject> = ts.GetTrackedTargetObject(player);

  let query: TargetSearchQuery;
  query.testedSet = TargetingSet.Visible;
  query.ignoreInstigator = true;
  query.filterObjectByDistance = true;
  query.maxDistance = 300.00;
  let ang: EulerAngles;
  let closest: ref<GameObject> = ts.GetObjectClosestToCrosshair(player, ang, query);

  let lookA: ref<GameObject> = ts.GetLookAtObject(player, true, true);
  let lookB: ref<GameObject> = ts.GetLookAtObject(player, false, false);

  let t: String = "";
  if IsDefined(tracked) { t += "T"; };
  if IsDefined(closest) { t += "C"; };
  if IsDefined(lookA) { t += "A"; };
  if IsDefined(lookB) { t += "B"; };
  if Equals(t, "") { t = "NONE"; };

  SentryNote("AIM_" + t);
}

// ---------------------------------------------------------------------------
// Ticker probe — does a DelayCallback ever fire at all?
// ---------------------------------------------------------------------------

public class SentryTicker extends DelayCallback {

  private let m_player: wref<PlayerPuppet>;
  private let m_count: Int32;
  private let m_delayId: DelayID;

  public final static func Start(player: ref<PlayerPuppet>) -> Void {
    if !IsDefined(player) {
      return;
    };
    let ticker: ref<SentryTicker> = new SentryTicker();
    ticker.m_player = player;
    ticker.m_count = 0;
    SentryNote("TICKER_START");
    ticker.Schedule();
  }

  private final func Schedule() -> Void {
    let delaySystem: ref<DelaySystem> = GameInstance.GetDelaySystem(GetGameInstance());
    if IsDefined(delaySystem) {
      if NotEquals(this.m_delayId, GetInvalidDelayID()) {
        delaySystem.CancelCallback(this.m_delayId);
      };
      this.m_delayId = delaySystem.DelayCallback(this, 0.25, false);
    };
  }

  public func Call() -> Void {
    this.Schedule();
    if !IsDefined(this.m_player) {
      SentryNote("TICKER_DEAD");
      return;
    };

    this.m_count += 1;
    if this.m_count <= 3 {
      SentryNote("TICK_" + IntToString(this.m_count));
      SentryAimReport();
    } else {
      if this.m_count % 25 == 0 {
        SentryNote("TICK_" + IntToString(this.m_count));
      };
    };
  }
}

// ---------------------------------------------------------------------------
// Engine hooks — every sparse, proven callback we can wrap
// ---------------------------------------------------------------------------

@wrapMethod(gameuiCrosshairContainerController)
protected cb func OnInitialize() -> Bool {
  let ret: Bool = wrappedMethod();
  SentryNote("CONT_INIT");
  SentryTicker.Start(GetPlayer(GetGameInstance()));
  return ret;
}

@wrapMethod(gameuiCrosshairContainerController)
protected cb func OnPlayerAttach(playerGameObject: ref<GameObject>) -> Bool {
  let ret: Bool = wrappedMethod(playerGameObject);
  SentryNote("CONT_ATTACH");
  SentryTicker.Start(playerGameObject as PlayerPuppet);
  return ret;
}

@wrapMethod(gameuiCrosshairContainerController)
protected cb func OnWeaponSwap(value: Variant) -> Bool {
  let ret: Bool = wrappedMethod(value);
  SentryNote("WEAPON_SWAP");
  return ret;
}

@wrapMethod(gameuiCrosshairContainerController)
protected cb func OnPSMVisionStateChanged(value: Int32) -> Bool {
  let ret: Bool = wrappedMethod(value);
  SentryNote("VISION_" + IntToString(value));
  return ret;
}

@wrapMethod(gameuiCrosshairContainerController)
protected cb func OnInteractionStateChange(value: Variant) -> Bool {
  let ret: Bool = wrappedMethod(value);
  SentryNote("INTERACT");
  return ret;
}

@wrapMethod(gameuiCrosshairBaseGameController)
protected func OnCrosshairStateChange(oldState: gamePSMCrosshairStates, newState: gamePSMCrosshairStates) -> Void {
  wrappedMethod(oldState, newState);
  SentryNote("XHAIR_STATE");
  SentryAimReport();
}

@wrapMethod(DamageSystem)
private final func ProcessLocalizedDamage(hitEvent: ref<gameHitEvent>) -> Void {
  wrappedMethod(hitEvent);
  if hitEvent.projectionPipeline {
    SentryNote("PROJ_HIT");
  } else {
    SentryNote("REAL_HIT");
    SentryAimReport();
  };
}

@wrapMethod(DamageSystem)
public final func ClearPreviewTargetStruct() -> Void {
  wrappedMethod();
  SentryNote("CLEAR_PREVIEW");
}
