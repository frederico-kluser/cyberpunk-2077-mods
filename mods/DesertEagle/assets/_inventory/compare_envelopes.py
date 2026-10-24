"""Compare the JSON envelope of app components vs compiledData chunks."""

import json

path = r"C:\Users\kluse\Projects\cyberpunk-2077\mods\DesertEagle\assets\_inventory\app_json\w_handgun__tsunami_nue.app.json"
d = json.load(open(path, encoding="utf-8"))
a0 = d["Data"]["RootChunk"]["appearances"][0]["Data"]

comp = a0["components"][0]
chunk = a0["compiledData"]["Data"]["Chunks"][0]
print("component top keys:", sorted(comp.keys()))
print("chunk top keys    :", sorted(chunk.keys()))
if "Data" in comp and "Data" in chunk:
    print("component Data keys:", sorted(comp["Data"].keys())[:8])
    print("chunk Data keys    :", sorted(chunk["Data"].keys())[:8])
print("component sample:", json.dumps({k: comp[k] for k in comp if k != 'Data'}, default=str)[:200])
print("chunk sample    :", json.dumps({k: chunk[k] for k in chunk if k != 'Data'}, default=str)[:200])
