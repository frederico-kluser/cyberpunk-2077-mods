/*
 * LogSentry — diagnostic capture mod (redscript side).
 *
 * Emits STRUCTURED, TIMESTAMPED log lines through every sink available in
 * vanilla redscript, and mirrors the same events as a file-name catalog:
 *
 *   FTLog line (logfmt, one event per line — lands in the CET game log):
 *     [LogSentry] ts=<GetGameTimeStamp 3dp> sim=<EngineTime seconds 3dp>
 *                 game=<game seconds> lvl=<DEBUG|INFO|WARN|ERROR> cat=<...>
 *                 ev=<stable_name> <key=value ...>
 *
 *   File catalog: ResourceMetricsReportGenerator.WriteReportToFile("LS-...")
 *   — the only vanilla write-to-file channel with a caller-controlled NAME,
 *   so the file name itself carries the event (content is the engine's own
 *   metrics report). Also the empirical probe of that undocumented API.
 *
 *   Clocks (three, deliberately): ts = TimeSystem.GetGameTimeStamp (semantics
 *   proven by the CLOCK_PROBE line: real epoch vs game seconds),
 *   sim = EngineTime.ToFloat(GetSimTime) (monotonic engine seconds — ordering
 *   within a session), game = GameTime.GetSeconds (world clock).
 *
 * The CET side (src/lua/init.lua) adds wall-clock timestamps, a JSONL file
 * and captures the game log this stream lands in.
 */

module LogSentry

// Running sequence number for the file-name catalog.
@addField(PlayerPuppet)
public let m_sentrySeq: Int32;

// ---------------------------------------------------------------------------
// Structured line
// ---------------------------------------------------------------------------

func LSEmit(lvl: String, cat: String, ev: String, fields: String) -> Void {
  let game: GameInstance = GetGameInstance();
  let ts: Float = GameInstance.GetTimeSystem(game).GetGameTimeStamp();
  let sim: Float = EngineTime.ToFloat(GameInstance.GetSimTime(game));
  let world: Int32 = GameTime.GetSeconds(GameInstance.GetGameTime(game));
  let line: String = s"[LogSentry] ts=\(FloatToStringPrec(ts, 3)) sim=\(FloatToStringPrec(sim, 3)) game=\(world) lvl=\(lvl) cat=\(cat) ev=\(ev) \(fields)";
  FTLog(line);
}

// Sparse events also go to the file-name catalog (name = the log line).
func LSCatalog(player: ref<PlayerPuppet>, ev: String) -> Void {
  let seq: String = "0";
  if IsDefined(player) {
    player.m_sentrySeq += 1;
    seq = IntToString(player.m_sentrySeq);
  };
  ResourceMetricsReportGenerator.WriteReportToFile("LS-" + seq + "-" + ev + ".txt");
}

func LSNote(player: ref<PlayerPuppet>, lvl: String, cat: String, ev: String, fields: String) -> Void {
  LSEmit(lvl, cat, ev, fields);
  LSCatalog(player, ev);
}

// ---------------------------------------------------------------------------
// Aim query report — the raw answer the label needs
// ---------------------------------------------------------------------------

func LSAimReport() -> Void {
  let player: ref<PlayerPuppet> = GetPlayer(GetGameInstance());
  if !IsDefined(player) {
    LSEmit("INFO", "aim", "aim_probe", "result=noplayer");
    return;
  };

  let ts: ref<TargetingSystem> = GameInstance.GetTargetingSystem(player.GetGame());
  if !IsDefined(ts) {
    LSEmit("INFO", "aim", "aim_probe", "result=notargetingsystem");
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

  let found: String = "";
  if IsDefined(tracked) { found += "T"; };
  if IsDefined(closest) { found += "C"; };
  if IsDefined(lookA) { found += "A"; };
  if IsDefined(lookB) { found += "B"; };
  if Equals(found, "") { found = "NONE"; };

  LSEmit("INFO", "aim", "aim_probe", s"found=\(found)");
}

// ---------------------------------------------------------------------------
// Ticker probe — proves the DelayCallback chain and the three clocks
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
    LSNote(player, "INFO", "sessao", "ticker_start", "");
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
      LSEmit("WARN", "sessao", "ticker_dead", "");
      return;
    };

    this.m_count += 1;
    if this.m_count == 1 {
      // The clock probe: all three clocks in one line — settles the
      // GetGameTimeStamp semantics (real epoch vs game seconds).
      LSCatalog(this.m_player, "clock_probe");
      LSAimReport();
    };
    if this.m_count <= 3 {
      LSEmit("DEBUG", "sessao", "tick", s"n=\(this.m_count)");
    } else {
      if this.m_count % 25 == 0 {
        LSEmit("DEBUG", "sessao", "tick", s"n=\(this.m_count)");
      };
    };
  }
}

// ---------------------------------------------------------------------------
// Engine hooks (script methods only — @wrapMethod cannot wrap natives)
// ---------------------------------------------------------------------------

@wrapMethod(gameuiCrosshairContainerController)
protected cb func OnInitialize() -> Bool {
  let ret: Bool = wrappedMethod();
  LSNote(GetPlayer(GetGameInstance()), "INFO", "hud", "cont_init", "");
  SentryTicker.Start(GetPlayer(GetGameInstance()));
  return ret;
}

@wrapMethod(gameuiCrosshairContainerController)
protected cb func OnPlayerAttach(playerGameObject: ref<GameObject>) -> Bool {
  let ret: Bool = wrappedMethod(playerGameObject);
  LSNote(playerGameObject as PlayerPuppet, "INFO", "hud", "cont_attach", "");
  SentryTicker.Start(playerGameObject as PlayerPuppet);
  return ret;
}

@wrapMethod(gameuiCrosshairContainerController)
protected cb func OnWeaponSwap(value: Variant) -> Bool {
  let ret: Bool = wrappedMethod(value);
  LSEmit("INFO", "equip", "weapon_swap", "");
  return ret;
}

@wrapMethod(gameuiCrosshairContainerController)
protected cb func OnPSMVisionStateChanged(value: Int32) -> Bool {
  let ret: Bool = wrappedMethod(value);
  LSEmit("DEBUG", "psm", "vision_state", s"value=\(value)");
  return ret;
}

@wrapMethod(gameuiCrosshairContainerController)
protected cb func OnInteractionStateChange(value: Variant) -> Bool {
  let ret: Bool = wrappedMethod(value);
  LSEmit("DEBUG", "psm", "interaction", "");
  return ret;
}

@wrapMethod(gameuiCrosshairBaseGameController)
protected func OnCrosshairStateChange(oldState: gamePSMCrosshairStates, newState: gamePSMCrosshairStates) -> Void {
  wrappedMethod(oldState, newState);
  LSEmit("DEBUG", "hud", "xhair_state", s"old=\(oldState) new=\(newState)");
  LSAimReport();
}

@wrapMethod(DamageSystem)
private final func ProcessLocalizedDamage(hitEvent: ref<gameHitEvent>) -> Void {
  wrappedMethod(hitEvent);
  if hitEvent.projectionPipeline {
    LSEmit("DEBUG", "damage", "proj_hit", "");
  } else {
    LSEmit("INFO", "damage", "real_hit", "");
    LSAimReport();
  };
}

@wrapMethod(DamageSystem)
public final func ClearPreviewTargetStruct() -> Void {
  wrappedMethod();
  LSEmit("DEBUG", "aim", "clear_preview", "");
}

// Session boundaries (the community's own session detectors).
@wrapMethod(QuestTrackerGameController)
protected cb func OnInitialize() -> Bool {
  let ret: Bool = wrappedMethod();
  LSNote(GetPlayer(GetGameInstance()), "INFO", "sessao", "session_ui_init", "");
  return ret;
}

@wrapMethod(QuestTrackerGameController)
protected cb func OnUninitialize() -> Bool {
  let ret: Bool = wrappedMethod();
  LSEmit("INFO", "sessao", "session_ui_uninit", "");
  return ret;
}

@wrapMethod(gameuiInGameMenuGameController)
protected cb func OnInitialize() -> Bool {
  let ret: Bool = wrappedMethod();
  LSEmit("INFO", "sessao", "menu_open", "");
  return ret;
}

@wrapMethod(gameuiInGameMenuGameController)
protected cb func OnUninitialize() -> Bool {
  let ret: Bool = wrappedMethod();
  LSEmit("INFO", "sessao", "menu_close", "");
  return ret;
}
