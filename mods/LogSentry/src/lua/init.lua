--[[
  LogSentry — diagnostic capture mod (CET/Lua side).

  Adds what pure redscript cannot:
    * WALL-CLOCK timestamps (os.date) on every record;
    * a structured JSONL catalog at <game>/r6/logs/logsentry.jsonl;
    * capture of the CET game log (gamelog.log), where every FTLog line from
      the redscript side ([LogSentry] ts=... sim=... game=...) lands — the
      bridge that turns the engine's invisible log stream into a real file;
    * a live overlay panel with counters.

  Authorised by the owner for this diagnostic mod (CET is normally out of
  scope for gameplay mods).
]]

local json = require("json")

local state = {
  out = nil,            -- JSONL file handle
  outPath = "",
  gamelogPath = "",
  gamelogOffset = 0,    -- how far we have read gamelog.log
  events = 0,
  bridged = 0,
  last = "",
  acc = 0,
  started = false,
}

local function gameRoot()
  if GetGamePath then
    local p = GetGamePath()
    if p and p ~= "" then
      return p
    end
  end
  return "../../" -- CET runs with CWD = bin/x64
end

local function wallClock()
  -- ISO-8601 UTC with milliseconds.
  local sec = os.time()
  local ms = math.floor((os.clock() % 1) * 1000)
  return os.date("!%Y-%m-%dT%H:%M:%S", sec) .. string.format(".%03dZ", ms)
end

local function emit(lvl, cat, ev, fields)
  fields = fields or {}
  local rec = {
    wall = wallClock(),
    lvl = lvl,
    cat = cat,
    ev = ev,
  }
  for k, v in pairs(fields) do
    rec[k] = v
  end
  state.events = state.events + 1
  state.last = ev
  if state.out then
    state.out:write(json.encode(rec) .. "\n")
    if state.events % 20 == 0 then
      state.out:flush()
    end
  end
end

-- Parse a redscript "[LogSentry] ts=... sim=... game=... lvl=... cat=... ev=... k=v ..."
-- line into a JSONL record, adding the wall-clock time of capture.
local function bridgeLine(line)
  local fields = {}
  for k, v in string.gmatch(line, "(%w+)=([^%s]+)") do
    fields[k] = v
  end
  if fields.ev then
    state.bridged = state.bridged + 1
    emit(fields.lvl or "INFO", fields.cat or "engine", fields.ev, {
      src = "redscript",
      ts = fields.ts,
      sim = fields.sim,
      game = fields.game,
    })
  end
end

local function tailGameLog()
  if not state.gamelogPath or state.gamelogPath == "" then
    return
  end
  local f = io.open(state.gamelogPath, "r")
  if not f then
    return
  end
  local size = f:seek("end")
  if size < state.gamelogOffset then
    state.gamelogOffset = 0 -- the log was rotated/recreated
  end
  if size > state.gamelogOffset then
    f:seek("set", state.gamelogOffset)
    for line in f:lines() do
      if string.find(line, "%[LogSentry%]", 1, false) then
        bridgeLine(line)
      end
    end
    state.gamelogOffset = f:seek("end")
  end
  f:close()
end

local function openCatalog()
  -- ABSOLUTE paths derived from this very file (debug.getinfo source):
  -- relative paths all fail because the CET process CWD is not bin\x64 —
  -- proven by the first session: every io.open returned nil.
  local src = debug.getinfo(1, "S").source
  if src:sub(1, 1) == "@" then
    src = src:sub(2)
  end
  -- ...\bin\x64\plugins\cyber_engine_tweaks\mods\LogSentry\init.lua
  local modDir = src:match("^(.*)[/\\][^/\\]*$") or "."
  local cetDir = modDir:match("^(.*)[/\\]mods[/\\][^/\\]*$") or modDir
  local root = modDir:match("^(.*[/\\])bin[/\\]x64") or nil

  local candidates = {}
  if root then
    table.insert(candidates, root .. "r6/logs/logsentry.jsonl")
    state.gamelogPath = root .. "bin/x64/plugins/cyber_engine_tweaks/gamelog.log"
  end
  table.insert(candidates, modDir .. "/logsentry.jsonl")
  table.insert(candidates, cetDir .. "/logsentry.jsonl")

  for _, path in ipairs(candidates) do
    local f = io.open(path, "a")
    if f then
      state.out = f
      state.outPath = path
      print("[LogSentry-Lua] catalog open: " .. path)
      break
    else
      print("[LogSentry-Lua] catalog open FAILED: " .. path)
    end
  end

  if not state.gamelogPath then
    state.gamelogPath = cetDir .. "/gamelog.log"
  end
  local gl = io.open(state.gamelogPath, "r")
  if not gl then
    print("[LogSentry-Lua] gamelog open FAILED: " .. state.gamelogPath)
  else
    gl:close()
    print("[LogSentry-Lua] gamelog: " .. state.gamelogPath)
  end

  emit("INFO", "sessao", "lua_init", {
    out = state.outPath,
    gamelog = state.gamelogPath,
    cet = true,
  })
end

-- ---------------------------------------------------------------------------
-- CET lifecycle
-- ---------------------------------------------------------------------------

registerForEvent("onInit", function()
  openCatalog()
  state.started = true
end)

registerForEvent("onShutdown", function()
  emit("INFO", "sessao", "lua_shutdown", { events = state.events, bridged = state.bridged })
  if state.out then
    state.out:flush()
    state.out:close()
    state.out = nil
  end
end)

registerForEvent("onUpdate", function(dt)
  state.acc = state.acc + dt
  if state.acc >= 1.0 then
    state.acc = 0
    tailGameLog()
    if state.out then
      state.out:flush()
    end
  end
end)

registerForEvent("onOverlayOpen", function()
  emit("INFO", "sessao", "overlay_open", {})
end)

registerForEvent("onOverlayClose", function()
  emit("INFO", "sessao", "overlay_close", {})
end)

-- Extra events only CET can see (it can observe natives too).
if Observe then
  Observe("PlayerPuppet", "OnGameAttached", function()
    emit("INFO", "sessao", "player_attached", { src = "cet" })
  end)
  Observe("ScriptedPuppet", "OnHit", function(self, evt)
    emit("INFO", "damage", "on_hit", { src = "cet" })
  end)
end

-- ---------------------------------------------------------------------------
-- Live panel: the catalog, on screen
-- ---------------------------------------------------------------------------

registerForEvent("onDraw", function()
  if not ImGui.Begin("LogSentry") then
    ImGui.End()
    return
  end
  ImGui.Text("catalog: " .. tostring(state.outPath))
  ImGui.Text(string.format("events: %d   bridged from redscript: %d", state.events, state.bridged))
  ImGui.Text("last: " .. tostring(state.last))
  ImGui.Text("gamelog: " .. tostring(state.gamelogPath))
  ImGui.End()
end)
