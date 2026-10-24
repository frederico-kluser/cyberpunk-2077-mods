"""Compare the render buffers of two mesh JSONs: sizes and where zeros start."""

import base64
import json
import sys

sys.path.insert(0, r"C:\Users\kluse\Projects\cyberpunk-2077\mods\DesertEagle\scripts")
import mesh_buffer as mb  # noqa: E402


def stats(path):
    rc = json.load(open(path, encoding="utf-8"))["Data"]["RootChunk"]
    blob = mb.find_render_resource(rc)
    rb = mb.find_node_with_key(rc, "BufferId")
    raw = base64.b64decode(rb["Bytes"])
    zero_start = None
    for i in range(len(raw) - 1, -1, -1):
        if raw[i] != 0:
            zero_start = i + 1
            break
    print(f"{path}")
    print(f"  bytes={len(raw)} vertexBufferSize={blob['vertexBufferSize']} indexBufferOffset={blob['indexBufferOffset']} indexBufferSize={blob['indexBufferSize']}")
    print(f"  trailing_zeros_start={zero_start}")
    print(f"  Flags={rb.get('Flags')} BufferId={rb.get('BufferId')}")
    return raw


a = stats(sys.argv[1])
b = stats(sys.argv[2])
print("same_length:", len(a) == len(b))
print("head_equal:", a[:1000] == b[:1000])
