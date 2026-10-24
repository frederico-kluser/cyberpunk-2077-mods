"""Read and summarize ALL game logs in one shot (the post-launch report).

Sources, in priority order:
  r6/logs/logsentry.jsonl                      - LogSentry structured catalog
  bin/x64/plugins/cyber_engine_tweaks/gamelog.log - engine stream + [LogSentry] lines
  red4ext/plugins/ArchiveXL/ArchiveXL*.log     - ArchiveXL (archive/xl loading)
  red4ext/plugins/TweakXL/TweakXL*.log         - TweakXL (yaml/tweakdb loading)
  r6/logs/redscript_rCURRENT.log               - redscript compile
  %LOCALAPPDATA%/CD Projekt Red/.../CrashInfo.json - crash marker

python3 read_game_logs.py [game_root]
"""

import glob
import json
import os
import sys

GAME = sys.argv[1] if len(sys.argv) > 1 else r"C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077"
CET = os.path.join(GAME, "bin", "x64", "plugins", "cyber_engine_tweaks")
LOCALAPPDATA = os.environ.get("LOCALAPPDATA", "")


def show(path, label, tail=40, filters=None):
    print(f"\n===== {label} =====")
    if not os.path.isfile(path):
        print("  (nao existe)")
        return []
    size = os.path.getsize(path)
    print(f"  {path.replace(GAME, '')}  [{size} B]")
    if size == 0:
        print("  (vazio)")
        return []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
    hits = [ln for ln in lines if not filters or any(x in ln for x in filters)]
    for ln in (hits or lines)[-tail:]:
        print("  " + ln.rstrip()[:220])
    return lines


def main():
    out = {}
    # 1. LogSentry catalog (JSONL) — the structured event stream
    jl = os.path.join(GAME, "r6", "logs", "logsentry.jsonl")
    print("===== LogSentry catalog =====")
    if os.path.isfile(jl):
        recs = [json.loads(ln) for ln in open(jl, encoding="utf-8") if ln.strip()]
        print(f"  {len(recs)} eventos")
        cats = {}
        for r in recs:
            cats[r.get("cat", "?")] = cats.get(r.get("cat", "?"), 0) + 1
        print("  por categoria:", cats)
        for r in recs[-25:]:
            print(f"  {r.get('wall','?')} [{r.get('lvl')}] {r.get('cat')}/{r.get('ev')} "
                  f"{ {k: v for k, v in r.items() if k not in ('wall','lvl','cat','ev')} }"[:220])
    else:
        print("  (ainda nao existe — o jogo nao correu com o LogSentry Lua ativo)")

    # 2. engine stream — DesertEagle + errors + LogSentry lines
    show(os.path.join(CET, "gamelog.log"), "gamelog.log (filtro: DesertEagle/erro/LogSentry)",
         tail=30, filters=["DesertEagle", "error", "Error", "ERROR", "LogSentry"])

    # 3. mod frameworks
    for pat, label in (
        (os.path.join(GAME, "red4ext", "plugins", "ArchiveXL", "ArchiveXL*.log"), "ArchiveXL"),
        (os.path.join(GAME, "red4ext", "plugins", "TweakXL", "TweakXL*.log"), "TweakXL"),
    ):
        for p in sorted(glob.glob(pat)):
            show(p, f"{label}: {os.path.basename(p)}", tail=25,
                 filters=["error", "Error", "fail", "Fail", "DesertEagle", "starting", "load"])

    # 4. redscript
    show(os.path.join(GAME, "r6", "logs", "redscript_rCURRENT.log"), "redscript", tail=15)

    # 5. crash marker + Windows crash events
    crash = os.path.join(LOCALAPPDATA, "CD Projekt Red", "Cyberpunk 2077", "CrashInfo.json")
    show(crash, "CrashInfo.json", tail=10)
    print("\n===== Windows eventos de crash (ultimas 2h) =====")
    try:
        import subprocess
        res = subprocess.run(
            ["powershell", "-Command",
             "Get-WinEvent -FilterHashtable @{LogName='Application'; Id=1000,1001; StartTime=(Get-Date).AddHours(-2)} -ErrorAction SilentlyContinue | Select-Object -First 4 | ForEach-Object { \"$($_.TimeCreated) $($_.Id): \" + (($_.Message -split \"`n\")[0..6] -join ' | ') }"],
            capture_output=True, text=True, timeout=60)
        print(res.stdout or "  (sem eventos)")
    except Exception as exc:  # noqa: BLE001
        print(f"  (nao foi possivel ler: {exc})")

    print("\nREAD_GAME_LOGS_DONE")


if __name__ == "__main__":
    main()
