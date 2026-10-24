"""Round-trip validation: import each generated .re with the official REDmod
plugin reader and report bones/frames."""

import glob
import os
import sys

import bpy

out_dir = sys.argv[sys.argv.index("--") + 1]
paths = sorted(glob.glob(os.path.join(out_dir, "*.re")))
paths = [p for p in paths if "_template" not in p]

ok = 0
for path in paths:
    try:
        # NOTE: no read_factory_settings here — it resets preferences and
        # unregisters the add-on operators. Just clear the scene.
        for obj in list(bpy.data.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.ops.import_file.re(filepath=path)
        objs = [o.name for o in bpy.data.objects]
        actions = [(a.name, len(a.fcurves) if hasattr(a, "fcurves") else "?") for a in bpy.data.actions]
        bones_obj = bpy.data.objects.get("Bones")
        n_children = len(bones_obj.children) if bones_obj else 0
        print(f"RE_IMPORT_OK {os.path.basename(path)} objects={len(objs)} bone_children={n_children} actions={actions}")
        ok += 1
    except Exception as exc:
        print(f"RE_IMPORT_FAIL {os.path.basename(path)}: {exc}")

print(f"RE_IMPORT_DONE {ok}/{len(paths)}")
