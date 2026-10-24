"""Run every codec test in one command (use Blender's python: needs numpy).

  python scripts/run_tests.py

Covers:
  - BCn texture codec         (test_bcn.py)        -> BCN_TEST_OK
  - anim key Compressed codec (test_anims_write.py) -> ANIMS_CODEC_TEST_OK
  - package verification      (verify_release.py)   -> RELEASE_VERIFY_OK
"""

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MOD_ROOT = os.path.dirname(HERE)
WORK = os.path.join(MOD_ROOT, "assets", "work")

TESTS = [
    ("bcn texture codec", [sys.executable, os.path.join(HERE, "test_bcn.py")], "BCN_TEST_OK"),
    (
        "anim key codec (compressed)",
        [
            sys.executable, os.path.join(HERE, "test_anims_write.py"),
            os.path.join(MOD_ROOT, "assets", "_inventory", "anims_json", "w_handgun__tsunami_nue__base1.anims.json"),
            os.path.join(WORK, "anims_test"),
        ],
        "ANIMS_CODEC_TEST_OK",
    ),
    (
        "release package verification",
        [sys.executable, os.path.join(HERE, "verify_release.py")],
        "RELEASE_VERIFY_OK",
    ),
    (
        "shipped mesh content (vs source geometry)",
        [
            sys.executable, os.path.join(HERE, "verify_mesh_content.py"),
            os.path.join(WORK, "mesh_test", "bin", "desert_eagle.mesh"),
            os.path.join(WORK, "de_geometry.json"),
        ],
        "MESH_CONTENT_VERIFY_OK",
    ),
    (
        "all 13 animation clips (motion + frame counts)",
        [
            sys.executable, os.path.join(HERE, "verify_anims_clips.py"),
            os.path.join(WORK, "anims_final", "bin"),
            os.path.join(MOD_ROOT, "assets", "_inventory", "anims_json"),
            os.path.join(WORK, "anims_final", "verify"),
        ],
        "ANIMS_CLIPS_VERIFY_OK",
    ),
    (
        "grip root alignment (A @ rest in every clip)",
        [
            sys.executable, os.path.join(HERE, "verify_root_align.py"),
            os.path.join(WORK, "anims_final"),
        ],
        "ROOT_ALIGN_VERIFY_OK",
    ),
]


def main():
    failures = 0
    for name, cmd, marker in TESTS:
        print(f"\n=== {name} ===")
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, cwd=HERE, timeout=600)
            out = res.stdout + res.stderr
        except Exception as exc:  # noqa: BLE001
            print(f"[FAIL] {name}: {exc}")
            failures += 1
            continue
        ok = marker in out and res.returncode == 0
        for line in out.splitlines():
            if line.strip():
                print("  " + line[:160])
        print(f"[{'OK' if ok else 'FAIL'}] {name} (marker {marker})")
        if not ok:
            failures += 1

    print(f"\nRUN_TESTS_{'OK' if failures == 0 else 'FAIL'} ({len(TESTS) - failures}/{len(TESTS)} passed)")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
