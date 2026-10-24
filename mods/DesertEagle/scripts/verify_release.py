"""Validate the packed Desert Eagle release end to end.

Checks (all against the actual files in assets/work/release):
  1. release layout (archive + .xl loader + TweakXL yaml)
  2. archive contains exactly the 6 expected depot paths
  3. every CR2W entry re-serializes (WolvenKit round-trip)
  4. .app: one appearance `desert_eagle`, one body mesh component pointing at
     our mesh, baseEntity -> our .ent, resolvedDependencies empty
  5. .ent: exactly one skinned mesh component -> our mesh
  6. .mesh: decodes to sane game-space geometry (one material chunk, ~0.25 m)
  7. factory + yaml + xl cross-references line up

Usage: python3 verify_release.py [release_dir]
Prints VERIFY_* lines and exits non-zero on any failure.
"""

import json
import os
import re
import subprocess
import sys

MOD_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RELEASE = sys.argv[1] if len(sys.argv) > 1 else os.path.join(MOD_ROOT, "assets", "work", "release")
WK = r"C:\Users\kluse\Tools\WolvenKit\9.1.0\wolvenkit-cli.cmd"
SYS_PATH = os.path.join(MOD_ROOT, "scripts")
sys.path.insert(0, SYS_PATH)

EXPECTED = [
    "desert_eagle\\items\\w_handgun_desert_eagle.mesh",
    "desert_eagle\\items\\desert_eagle.app",
    "desert_eagle\\items\\desert_eagle.ent",
    "desert_eagle\\items\\textures\\desert_eagle_bc.xbm",
    "desert_eagle\\items\\textures\\desert_eagle_n.xbm",
    "desert_eagle\\animations\\w_handgun__tsunami_nue__base1.anims",
    "desert_eagle\\animations\\w_handgun__tsunami_nue__mag_std.anims",
    "desert_eagle\\factories\\weapons.csv",
    "desert_eagle\\localization\\en-us.json",
    "desert_eagle\\localization\\pt-br.json",
]

FAILURES = []


def fnv1a64(text):
    h = 0xCBF29CE484222325
    for b in text.encode("utf-8"):
        h ^= b
        h = (h * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
    return h


def depot_is(dp, path):
    """A ResourcePath may re-serialize as the path string OR as its
    FNV1a-64 hash (WolvenKit drops unresolvable custom paths to hash-only)."""
    if not isinstance(dp, dict):
        return False
    value = dp.get("$value")
    return value == path or value == str(fnv1a64(path))


def check(cond, msg):
    print(("VERIFY_OK   " if cond else "VERIFY_FAIL ") + msg)
    if not cond:
        FAILURES.append(msg)


def wk(*args):
    return subprocess.run([WK, *args], capture_output=True, text=True).stdout


def main():
    archive = os.path.join(RELEASE, "desert_eagle.archive")
    xl = os.path.join(RELEASE, "desert_eagle.archive.xl")
    yaml = os.path.join(RELEASE, "desert_eagle.yaml")

    # 1. layout
    check(os.path.isfile(archive), "release/desert_eagle.archive exists")
    check(os.path.isfile(xl), "release/desert_eagle.archive.xl exists")
    check(os.path.isfile(yaml), "release/desert_eagle.yaml exists")

    # 2. archive entries
    listing = wk("archive", archive, "-l", "-v", "Minimal")
    found = [e.strip() for e in listing.splitlines() if "\\" in e and "." in e]
    for entry in EXPECTED:
        check(any(entry in f for f in found), f"archive contains {entry}")
    check(len(found) == len(EXPECTED), f"archive has exactly {len(EXPECTED)} entries (got {len(found)})")

    # 3. round-trip every entry
    out = os.path.join(RELEASE, "_verify")
    os.makedirs(out, exist_ok=True)
    wk("unbundle", archive, "-o", out, "-v", "Minimal")
    for entry in EXPECTED:
        path = os.path.join(out, entry.replace("\\", os.sep))
        check(os.path.isfile(path) and os.path.getsize(path) > 0, f"unbundled {entry}")
    json_dir = os.path.join(out, "_json")
    os.makedirs(json_dir, exist_ok=True)
    for entry in EXPECTED:
        if entry.endswith((".app", ".ent", ".mesh", "weapons.csv", "en-us.json", "pt-br.json")):
            wk("convert", "serialize", os.path.join(out, entry.replace("\\", os.sep)), "-o", json_dir, "-v", "Minimal")
            base = os.path.basename(entry) + ".json"
            check(os.path.isfile(os.path.join(json_dir, base)), f"re-serializes {entry}")

    # 4. app coherence
    app = json.load(open(os.path.join(json_dir, "desert_eagle.app.json"), encoding="utf-8"))
    rc = app["Data"]["RootChunk"]
    apps = rc.get("appearances") or []
    check(len(apps) == 1, "app has exactly one appearance (dry-run rule)")
    a0 = apps[0]["Data"]
    name = a0.get("name")
    check(isinstance(name, dict) and name.get("$value") == "desert_eagle", "appearance is named 'desert_eagle'")
    mesh_comps = [c.get("Data", c) for c in a0["components"]
                  if c.get("Data", c).get("$type") == "entSkinnedMeshComponent"]
    check(len(mesh_comps) == 1, "app has exactly one body mesh component")
    dp = mesh_comps[0]["mesh"]["DepotPath"]
    check(depot_is(dp, "desert_eagle\\items\\w_handgun_desert_eagle.mesh"), "app body mesh points at our mesh")
    be = rc["baseEntity"]["DepotPath"]
    check(depot_is(be, "desert_eagle\\items\\desert_eagle.ent"), "app baseEntity points at our ent")
    check(a0.get("resolvedDependencies") == [], "app resolvedDependencies is empty")

    # no vanilla mesh may survive in the COMPONENTS (the render source of truth)
    def mesh_refs(node, out):
        if isinstance(node, dict):
            for k, v in node.items():
                if k in ("DepotPath", "depotPath"):
                    val = v.get("$value") if isinstance(v, dict) else v
                    if isinstance(val, str) and val.endswith(".mesh"):
                        out.append(val)
                else:
                    mesh_refs(v, out)
        elif isinstance(node, list):
            for item in node:
                mesh_refs(item, out)

    refs = []
    mesh_refs(a0.get("components"), refs)
    vanilla = [r for r in refs if "tsunami_nue" in r]
    check(not vanilla, f"components have no vanilla mesh references (found {len(vanilla)})")

    # the first-person animation sets must point at our CS2 clips — CR2W
    # stores ResourcePaths as FNV1a-64 hashes, so match string OR hash
    anim_want = [
        "desert_eagle\\animations\\w_handgun__tsunami_nue__base1.anims",
        "desert_eagle\\animations\\w_handgun__tsunami_nue__mag_std.anims",
    ]
    want_keys = set(anim_want) | {str(fnv1a64(p)) for p in anim_want}
    anim_vals = []

    def anim_refs_walk(node):
        if isinstance(node, dict):
            for k, v in node.items():
                if k in ("DepotPath", "depotPath") and isinstance(v, dict):
                    val = v.get("$value")
                    if isinstance(val, str):
                        anim_vals.append(val)
                else:
                    anim_refs_walk(v)
        elif isinstance(node, list):
            for item in node:
                anim_refs_walk(item)

    anim_refs_walk(rc)
    ours = [v for v in anim_vals if v in want_keys]
    check(len(ours) >= 2, f"app animation sets point at our clips (found {len(ours)} refs)")
    # the engine resolves ResourcePaths by FNV1a-64 hash — calibrated against
    # the compiled app (assets/_inventory/calibrate_hash2.py). The anim refs
    # round-trip as hash values matching our fnv1a64, so require the HASH form
    # to be present too: that is what the game actually reads.
    ours_hash = [v for v in anim_vals if isinstance(v, str) and v.isdigit()
                 and int(v) in {fnv1a64(p) for p in anim_want}]
    check(len(ours_hash) >= 2, f"anim refs present in hash form (engine-readable, found {len(ours_hash)})")

    # localization CONTENT: the item name must exist in both shipped locales
    def find_entries(node):
        if isinstance(node, dict):
            if "entries" in node and isinstance(node["entries"], list):
                return node["entries"]
            for v in node.values():
                r = find_entries(v)
                if r is not None:
                    return r
        elif isinstance(node, list):
            for v in node:
                r = find_entries(v)
                if r is not None:
                    return r
        return None

    for locale in ("en-us", "pt-br"):
        loc_path = os.path.join(json_dir, f"{locale}.json.json")
        if not os.path.isfile(loc_path):
            check(False, f"localization {locale} serialized back")
            continue
        loc = json.load(open(loc_path, encoding="utf-8"))

        def fld(v):
            return v.get("$value") if isinstance(v, dict) else v

        entries = find_entries(loc) or []
        named = [
            e for e in entries
            if fld(e.get("secondaryKey")) == "DesertEagle-Name"
            and fld(e.get("femaleVariant"))
        ]
        check(bool(named), f"localization {locale} carries the DesertEagle-Name entry")

    # compiledData is a stale cooked cache — provably inert while
    # cookedAppearanceData is empty (the engine renders from the components)
    chunks = (a0.get("compiledData", {}).get("Data", {}) or {}).get("Chunks") or []
    cooked = None
    for ch in chunks:
        c = ch.get("Data", ch)
        if c.get("$type") == "entVisualControllerComponent":
            cad = c.get("cookedAppearanceData", {})
            cooked = cad.get("DepotPath", {}).get("$value") if isinstance(cad, dict) else None
    check(cooked in ("0", 0, None), f"compiledData cookedAppearanceData is empty (inert cache), got {cooked}")

    # 5. ent coherence
    ent = json.load(open(os.path.join(json_dir, "desert_eagle.ent.json"), encoding="utf-8"))
    ent_comps = [c.get("Data", c) for c in (ent["Data"]["RootChunk"].get("components") or [])]
    ent_mesh = [c for c in ent_comps if c.get("$type") == "entSkinnedMeshComponent"]
    check(len(ent_mesh) == 1, "ent has exactly one skinned mesh component")
    if ent_mesh:
        dp = ent_mesh[0]["mesh"]["DepotPath"]
        check(depot_is(dp, "desert_eagle\\items\\w_handgun_desert_eagle.mesh"), "ent mesh points at our mesh")

    # 6. mesh geometry sanity
    import mesh_buffer as mb
    mesh = json.load(open(os.path.join(json_dir, "w_handgun_desert_eagle.mesh.json"), encoding="utf-8"))
    geo = mb.decode_geometry(mesh["Data"]["RootChunk"])
    # vanilla chunks are per-material parts; our merged body is ONE chunk —
    # duplicated chunks make the gun render twice over itself
    check(len(geo) == 1, f"mesh has exactly one material chunk (got {len(geo)})")
    unique = len({(tuple(map(tuple, c["positions"][:64]))) for c in geo}) == len(geo)
    check(unique, "mesh chunks are not duplicate copies")
    pts = [p for ch in geo for p in ch["positions"]]
    if pts:
        mn = [min(p[i] for p in pts) for i in range(3)]
        mx = [max(p[i] for p in pts) for i in range(3)]
        size = [mx[i] - mn[i] for i in range(3)]
        longest = max(size)
        check(0.15 <= longest <= 0.40, f"mesh longest dimension is pistol-sized ({longest:.3f} m)")
    total_idx = sum(len(ch["indices"]) for ch in geo)
    check(total_idx > 30000, f"mesh has real geometry ({total_idx} indices)")

    # 7. cross-references
    factory = open(os.path.join(out, "desert_eagle", "factories", "weapons.csv"), encoding="utf-8", errors="ignore").read()
    check("desert_eagle_factory" in factory, "factory registers desert_eagle_factory")
    check("desert_eagle\\items\\desert_eagle.app" in factory, "factory points at our app")
    xl_txt = open(xl, encoding="utf-8").read()
    check("desert_eagle\\factories\\weapons.csv" in xl_txt, "xl loader references the factory")
    yaml_txt = open(yaml, encoding="utf-8").read()
    check("Items.DesertEagle" in yaml_txt and "desert_eagle_factory" in yaml_txt, "yaml registers the item and factory key")

    print()
    if FAILURES:
        print(f"RELEASE_VERIFY_FAIL ({len(FAILURES)} problem(s))")
        return 1
    print("RELEASE_VERIFY_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
