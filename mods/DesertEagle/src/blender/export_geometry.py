"""Export the Desert Eagle geometry as geometry.json for mesh_write.py.

Runs inside Blender. Pipeline:
  1. import the CS2 model (pre-skinned, separate movable parts);
  2. retarget its vertex groups to the real Nue .rig bone names;
  3. fit the model to the Nue mesh's decoded bounding box (game space, meters);
  4. merge the parts into ONE material chunk (vanilla chunks = material parts);
  5. dump positions/normals/tangents/uvs/skin/indices per chunk.

Usage:
  blender --background --python export_geometry.py -- <nue.mesh.json> <out_geometry.json>
"""

from __future__ import annotations

import json
import math
import os
import sys

import bpy
from mathutils import Matrix, Quaternion, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "scripts"))

import mesh_buffer as mb  # noqa: E402
from de_pipeline.re_export import load_rig_json  # noqa: E402
from de_pipeline.retarget import drop_objects, retarget_bones  # noqa: E402

MODEL = os.path.join(HERE, "..", "..", "assets", "raw", "desert_eagle_cs2.glb")
RIG_JSON = os.path.join(HERE, "..", "..", "assets", "_inventory", "nue_rig.json")

BONE_MAP = {
    "GLTF_created_0_rootJoint": "barrel_plug",
    "weapon_hand_r_4": "barrel",
    "v_weapon_deagle_slide_0": "slide",
    "v_weapon_deagle_trigger_1": "weapon_trigger",
    "v_weapon_deagle_clip_2": "mag_slot",
    "v_weapon_deagle_hammer_3": "hammer",
}

# .rig order — skin indices refer to this list
RIG_ORDER = [
    "barrel_plug", "barrel", "muzzle_slot", "fx_muzzle", "weapon_trigger",
    "slide", "hammer", "slider_down", "mag_slot", "scope_slot", "pos_ironsight",
]
BONE_INDEX = {name: i for i, name in enumerate(RIG_ORDER)}


def evaluated_triangles(obj):
    """(verts world, normals world, uvs, tris) of the evaluated mesh."""
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg)
    me = ev.to_mesh()
    me.calc_loop_triangles()
    mw = ev.matrix_world.copy()
    normal_mw = mw.to_3x3().inverted().transposed()

    uv_layer = me.uv_layers.active
    verts, normals, uvs = [], [], []
    for v in me.vertices:
        verts.append((mw @ v.co).copy())
        normals.append((normal_mw @ v.normal).normalized())
        uvs.append((0.0, 0.0))
    if uv_layer is not None:
        for li, loop in enumerate(me.loops):
            uvs[loop.vertex_index] = tuple(uv_layer.data[li].uv)

    tris = [(tri.vertices[0], tri.vertices[1], tri.vertices[2]) for tri in me.loop_triangles]
    ev.to_mesh_clear()
    return verts, normals, uvs, tris


def rest_delta_matrices(rig_json_path):
    """Per-bone 4x4 delta: nue_arm_rest @ cs2_arm_rest^-1.

    The retarget only RENAMES bones — the vertices stay around the CS2 rest
    while the game rig (and the animations) live at the Nue rest in game
    space. Without this transform the mesh and the rig disagree by the
    CS2->Nue orientation (verified by scripts/verify_skin_mapping.py and
    assets/_inventory/check_spaces.py). The SAME rest-to-rest mapping the
    animation export applies is applied to the geometry here.
    """
    arm = next((o for o in bpy.data.objects if o.type == "ARMATURE"), None)
    if arm is None:
        raise RuntimeError("no armature in scene")

    def local_of(pb):
        if pb.parent is None:
            return pb.bone.matrix_local.copy()
        return pb.parent.bone.matrix_local.inverted() @ pb.bone.matrix_local

    # vertex groups are renamed to Nue names but the armature bones may keep
    # the CS2 names — map both through BONE_MAP
    cs2_local = {BONE_MAP.get(pb.name, pb.name): local_of(pb) for pb in arm.pose.bones}

    nue_local = {}
    for b in load_rig_json(rig_json_path):
        x, y, z, w = b["quat"]
        rot = Quaternion((w, x, y, z)).to_matrix().to_4x4()
        nue_local[b["name"]] = Matrix.Translation(Vector(b["pos"])) @ rot

    def chain(local, order, parents):
        out = {}
        for i, name in enumerate(order):
            if name not in local:
                continue  # the CS2 rig has only the 6 mapped bones
            p = parents[i]
            while p >= 0 and order[p] not in local:
                p = parents[p]
            out[name] = (out[order[p]] @ local[name] if p >= 0 else local[name].copy())
        return out

    # RIG_ORDER/parents mirror the .rig: barrel_plug root, barrel child, ...
    parents = [-1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 5]
    nue_arm = chain(nue_local, RIG_ORDER, parents)
    cs2_arm = chain(cs2_local, RIG_ORDER, parents)
    # The CS2 GLB splits units (object scale 0.0254 + inch bone offsets); the
    # composed world matrices end up with scale 0.0254 while translations are
    # already meters. Normalise the rotation so the per-bone delta is rigid
    # (scale 1 x 1) instead of 39x — caught by the pistol-sized bbox check.
    cs2_fixed = {}
    for n, m in cs2_arm.items():
        mw = arm.matrix_world @ m
        rot = mw.to_3x3().normalized().to_4x4()
        rot.translation = mw.to_translation()
        cs2_fixed[n] = rot
    cs2_arm = cs2_fixed
    shared = [n for n in RIG_ORDER if n in nue_arm and n in cs2_arm]
    return {name: nue_arm[name] @ cs2_arm[name].inverted() for name in shared}
def skin_of(obj, nverts):
    """(indices[4], weights[4]) per vertex from the (renamed) vertex groups."""
    out_i = [[0, 0, 0, 0] for _ in range(nverts)]
    out_w = [[1.0, 0.0, 0.0, 0.0] for _ in range(nverts)]
    for vertex in obj.data.vertices:
        entries = []
        for g in vertex.groups:
            name = obj.vertex_groups[g.group].name
            if name in BONE_INDEX and g.weight > 1e-6:
                entries.append((BONE_INDEX[name], g.weight))
        entries.sort(key=lambda e: -e[1])
        entries = entries[:4]
        total = sum(w for _, w in entries) or 1.0
        for k, (idx, w) in enumerate(entries):
            out_i[vertex.index][k] = idx
            out_w[vertex.index][k] = w / total
    return out_i, out_w


def main() -> int:
    nue_json = sys.argv[sys.argv.index("--") + 1]
    out_json = sys.argv[sys.argv.index("--") + 2]

    # target bbox = the Nue mesh's decoded geometry (game space, meters)
    rc = json.load(open(nue_json, encoding="utf-8"))["Data"]["RootChunk"]
    chunks = mb.decode_geometry(rc)
    tmin = [1e30] * 3
    tmax = [-1e30] * 3
    for ch in chunks:
        for p in ch["positions"]:
            for a in range(3):
                tmin[a] = min(tmin[a], p[a])
                tmax[a] = max(tmax[a], p[a])
    print(f"GEOM target bbox=({tmin[0]:.4f},{tmin[1]:.4f},{tmin[2]:.4f})..({tmax[0]:.4f},{tmax[1]:.4f},{tmax[2]:.4f})")

    # import + clean + retarget
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=MODEL)
    drop_objects(list(bpy.data.objects), ["Icosphere"])
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    retarget_bones(meshes, BONE_MAP)

    # rest-to-rest transform: move vertices from the CS2 rest onto the Nue
    # game-space rest (replaces the old blind "fit" that left the mesh and
    # the rig in different orientations)
    deltas = rest_delta_matrices(RIG_JSON)
    all_pts = []
    data = {}
    for obj in meshes:
        verts, normals, uvs, tris = evaluated_triangles(obj)
        data[obj.name] = (verts, normals, uvs, tris)
        all_pts.extend(verts)
    print(f"GEOM source bbox span={max(max(p[i] for p in all_pts) - min(p[i] for p in all_pts) for i in range(3)):.4f} m")

    # ONE material chunk (vanilla chunks are per-material parts, NOT LODs —
    # a duplicated chunk makes the gun render twice over itself; caught by
    # assets/_inventory/check_chunks.py)
    out_chunks = []
    positions, normals, tangents, uvs = [], [], [], []
    skin_i, skin_w, indices = [], [], []
    base = 0
    for name, (verts, ns, uvs_, tris) in data.items():
        obj = bpy.data.objects[name]
        si, sw = skin_of(obj, len(verts))
        for k, v in enumerate(verts):
            # skin-blended rest-to-rest transform (game space from here on)
            p = Vector((0.0, 0.0, 0.0))
            nrm = Vector((0.0, 0.0, 0.0))
            for j in range(4):
                w = sw[k][j]
                if w <= 0:
                    continue
                m = deltas[RIG_ORDER[si[k][j]]]
                p += w * (m @ v)
                nrm += w * (m.to_3x3() @ ns[k])
            if nrm.length < 1e-9:
                nrm = Vector((0, 0, 1))
            nrm.normalize()
            positions.append([round(p.x, 7), round(p.y, 7), round(p.z, 7)])
            normals.append([round(nrm.x, 5), round(nrm.y, 5), round(nrm.z, 5)])
            t = nrm.cross(Vector((0, 0, 1)))
            if t.length < 1e-6:
                t = Vector((1, 0, 0))
            t.normalize()
            tangents.append([round(t.x, 5), round(t.y, 5), round(t.z, 5), 1.0])
            uvs.append([round(uvs_[k][0], 5), round(uvs_[k][1], 5)])
            skin_i.append(si[k])
            skin_w.append([round(x, 5) for x in sw[k]])
        for tri in tris:
            indices.extend([tri[0] + base, tri[1] + base, tri[2] + base])
        base += len(verts)
    out_chunks.append({
        "positions": positions,
        "normals": normals,
        "tangents": tangents,
        "uvs": uvs,
        "skin_indices": skin_i,
        "skin_weights": skin_w,
        "indices": indices,
    })
    print(f"GEOM chunk0 verts={len(positions)} idx={len(indices)}")

    json.dump({"chunks": out_chunks}, open(out_json, "w", encoding="utf-8"))
    print(f"GEOM_OK {out_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
