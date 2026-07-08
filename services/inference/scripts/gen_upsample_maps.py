"""Generate clean fsaverage5 -> fsaverage7 upsample maps from the GLB meshes.

The demo's own ``*-upsample.bin`` files are a custom interleaved format
(mixed indices + weights, opaque header). Rather than reverse-engineer
that, we build our own: for every high-res vertex (163,842/hemi,
fsaverage7) find the nearest coarse vertex (10,242/hemi, fsaverage5) by
3-D position. fsaverage5 is a nested subset of fsaverage7, so the first
10,242 map to themselves (distance 0) and the rest take their nearest
coarse value. Output is a flat uint32 index array per hemisphere that the
renderer uses to expand a (20484,) activation onto the dense mesh.
"""

import json
import struct
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

PUBLIC = Path(__file__).resolve().parents[3] / "apps" / "web" / "public"
MODELS = PUBLIC / "models"
OUT_DIR = PUBLIC / "brain-upsample-maps"


def read_glb_positions(path: Path) -> np.ndarray:
    data = path.read_bytes()
    if data[:4] != b"glTF":
        raise ValueError(f"{path} is not a GLB")
    json_len = struct.unpack("<I", data[12:16])[0]
    gltf = json.loads(data[20 : 20 + json_len])
    bin_start = 20 + json_len + 8  # skip JSON chunk + BIN chunk header
    bin_data = data[bin_start:]

    primitive = gltf["meshes"][0]["primitives"][0]
    accessor = gltf["accessors"][primitive["attributes"]["POSITION"]]
    view = gltf["bufferViews"][accessor["bufferView"]]
    offset = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
    count = accessor["count"]
    floats = np.frombuffer(bin_data, dtype=np.float32, count=count * 3, offset=offset)
    return floats.reshape(count, 3)


def build_map(coarse_glb: Path, high_glb: Path, out_path: Path) -> None:
    coarse = read_glb_positions(coarse_glb)
    high = read_glb_positions(high_glb)
    tree = cKDTree(coarse)
    _, nearest = tree.query(high, k=1)
    nearest = nearest.astype(np.uint32)
    out_path.write_bytes(nearest.tobytes())
    print(
        f"{out_path.name}: {len(coarse)} -> {len(high)} verts, "
        f"max idx {int(nearest.max())}, {out_path.stat().st_size} bytes"
    )


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    build_map(
        MODELS / "brain-left-hemisphere.glb",
        MODELS / "brain-left-hemishpere-high.glb",
        OUT_DIR / "fsaverage5-to-high-left.bin",
    )
    build_map(
        MODELS / "brain-right-hemisphere.glb",
        MODELS / "brain-right-hemisphere-high.glb",
        OUT_DIR / "fsaverage5-to-high-right.bin",
    )


if __name__ == "__main__":
    main()
