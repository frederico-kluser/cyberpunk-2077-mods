/*
 * Lethal Headshots — configuration.
 *
 * These are compile-time options: edit the value, save, and restart the game
 * (redscript recompiles the scripts at launch). Booleans are `true` / `false`.
 */

module LethalHeadshots.Config

/*
 * Civilians (crowd NPCs, vendors, non-combat characters) survive a headshot.
 * Set to false if you want every headshot to kill, no matter who it hits.
 */
public func SpareCivilians() -> Bool {
  return true;
}

/*
 * Friendly characters (allies, companions, quest contacts with a friendly
 * attitude towards V) survive a headshot.
 */
public func SpareAllies() -> Bool {
  return true;
}

/*
 * Targets protected by the game (god mode, scripted invulnerability, quest
 * NPCs that must not die) survive a headshot. Keep this on unless you know
 * exactly what you are doing: killing protected NPCs can break quests.
 */
public func SpareProtectedTargets() -> Bool {
  return true;
}
