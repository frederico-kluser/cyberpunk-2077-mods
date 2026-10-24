/*
 * Lethal Headshots — configuration.
 *
 * These are compile-time options: edit the value, save, and restart the game
 * (redscript recompiles the scripts at launch). Booleans are `true` / `false`.
 */

module LethalHeadshots.Config

/*
 * Civilians (crowd NPCs, vendors, non-combat characters) survive a headshot.
 * Default is false: every headshot kills, including civilians.
 */
public func SpareCivilians() -> Bool {
  return false;
}

/*
 * Friendly characters (allies, companions, quest contacts with a friendly
 * attitude towards V) survive a headshot.
 * Default is false: every headshot kills, including allies.
 */
public func SpareAllies() -> Bool {
  return false;
}

/*
 * Targets protected by the game (god mode, scripted invulnerability, quest
 * NPCs that must not die) also take the headshot kill.
 * Default is false: no exceptions, every headshot kills. WARNING: one-shotting
 * a quest-critical NPC can break a playthrough — set to true to spare them.
 */
public func SpareProtectedTargets() -> Bool {
  return false;
}

/*
 * Diagnostic probes for the "QUE OTA" label: two bars above the crosshair
 * (blue = a target is under the crosshair, red = over a killable head). The
 * crosshair itself also tints white/orange/red. Set to false once the label
 * is confirmed working to hide the bars (the tint stays).
 */
public func DebugProbes() -> Bool {
  return true;
}
