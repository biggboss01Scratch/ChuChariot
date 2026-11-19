"""Render inspection stills from the original GLB. Requires NumPy and Pillow."""

import argparse
import hashlib
import json
import struct
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


def load_glb(path):
    content = path.read_bytes()
    magic, version, length = struct.unpack_from("<4sII", content)
    json_size, json_type = struct.unpack_from("<I4s", content, 12)
    if (magic, version, length, json_type) != (b"glTF", 2, len(content), b"JSON"):
        raise ValueError("Expected a GLB 2 file")
    end = 20 + json_size
    binary_size, binary_type = struct.unpack_from("<I4s", content, end)
    if binary_type != b"BIN\x00" or end + 8 + binary_size != length:
        raise ValueError("Expected a single embedded BIN chunk")
    return json.loads(content[20:end]), content[end + 8:], hashlib.sha256(content).hexdigest()


def accessor(model, binary, index):
    item = model["accessors"][index]
    view = model["bufferViews"][item["bufferView"]]
    if view["buffer"] != 0 or "sparse" in item:
        raise ValueError("This inspection script expects embedded, non-sparse geometry")
    dtype = np.dtype({5121: "u1", 5123: "<u2", 5125: "<u4", 5126: "<f4"}[item["componentType"]])
    width = {"SCALAR": 1, "VEC3": 3}[item["type"]]
    offset = view.get("byteOffset", 0) + item.get("byteOffset", 0)
    stride = view.get("byteStride", dtype.itemsize * width)
    return np.ndarray((item["count"], width), dtype=dtype, buffer=binary, offset=offset,
                      strides=(stride, dtype.itemsize))


def transform(node):
    if "matrix" in node:
        return np.array(node["matrix"]).reshape(4, 4).T
    x, y, z, w = node.get("rotation", [0, 0, 0, 1])
    result = np.eye(4)
    result[:3, :3] = np.array([
        [1 - 2*(y*y + z*z), 2*(x*y - z*w), 2*(x*z + y*w)],
        [2*(x*y + z*w), 1 - 2*(x*x + z*z), 2*(y*z - x*w)],
        [2*(x*z - y*w), 2*(y*z + x*w), 1 - 2*(x*x + y*y)],
    ]) * node.get("scale", [1, 1, 1])
    result[:3, 3] = node.get("translation", [0, 0, 0])
    return result


def geometry(model, binary):
    triangles, colors, owners = [], [], []

    def walk(node_index, parent):
        node = model["nodes"][node_index]
        matrix = parent @ transform(node)
        if "mesh" in node:
            for primitive in model["meshes"][node["mesh"]]["primitives"]:
                if primitive.get("mode", 4) != 4:
                    raise ValueError("Expected triangle primitives")
                vertices = accessor(model, binary, primitive["attributes"]["POSITION"])
                points = vertices @ matrix[:3, :3].T + matrix[:3, 3]
                indices = (accessor(model, binary, primitive["indices"]) if "indices" in primitive
                           else np.arange(len(points))).reshape(-1, 3)
                batch = points[indices]
                color = model["materials"][primitive["material"]].get("pbrMetallicRoughness", {}).get(
                    "baseColorFactor", [.65, .65, .65, 1])[:3]
                triangles.append(batch)
                colors.append(np.repeat([color], len(batch), axis=0))
                owners.append(np.full(len(batch), node_index))
        for child in node.get("children", []):
            walk(child, matrix)

    for root in model["scenes"][model.get("scene", 0)]["nodes"]:
        walk(root, np.eye(4))
    return np.concatenate(triangles), np.concatenate(colors), np.concatenate(owners)


def descendants(model, roots):
    pending = list(roots)
    result = set()
    while pending:
        index = pending.pop()
        if index not in result:
            result.add(index)
            pending.extend(model["nodes"][index].get("children", []))
    return result


def camera(direction):
    depth = np.asarray(direction, dtype=float)
    depth /= np.linalg.norm(depth)
    right = np.cross([0, 1, 0], depth)
    right /= np.linalg.norm(right)
    return np.stack((right, np.cross(depth, right), depth), axis=1)


def render(path, triangles, colors, focus=None, direction=(1.6, 0.85, 1.35)):
    width, height = 860, 560
    projected = triangles @ camera(direction)
    bounds = projected if focus is None else projected[focus]
    min_xy, max_xy = bounds[:, :, :2].min(axis=(0, 1)), bounds[:, :, :2].max(axis=(0, 1))
    offset = (min_xy + max_xy) / 2
    scale = min(np.array([width, height]) * .78 / np.maximum(max_xy - min_xy, 1e-9))
    xy = ((projected[:, :, :2] - offset) * [scale, -scale] + [width / 2, height / 2]).astype(int)
    normal = np.cross(projected[:, 1] - projected[:, 0], projected[:, 2] - projected[:, 0])
    normal /= np.maximum(np.linalg.norm(normal, axis=1, keepdims=True), 1e-12)
    brightness = .65 + .35 * np.abs(normal @ [-.35, .50, .79])
    rgb = np.clip(np.sqrt(np.clip(colors, 0, 1)) * brightness[:, None] * 255, 0, 255).astype(int)
    order = np.argsort(projected[:, :, 2].mean(axis=1))
    image = Image.new("RGB", (width, height), "#f4f5f0")
    pen = ImageDraw.Draw(image)
    if focus is not None:
        # Draw muted context first so the focused node remains identifiable through occlusion.
        rgb[~focus] = (.22 * rgb[~focus] + .78 * np.array([226, 231, 226])).astype(int)
        rgb[focus] = (brightness[focus, None] * [54, 113, 92]).astype(int)
        order = np.concatenate((order[~focus[order]], order[focus[order]]))
    for index in order:
        points = xy[index]
        if points[:, 0].max() < 0 or points[:, 0].min() >= width or points[:, 1].max() < 0 or points[:, 1].min() >= height:
            continue
        pen.polygon([tuple(point) for point in points], fill=tuple(rgb[index]))
    image.save(path)


def render_registered_views(model_path, records, dataset, output):
    model, binary, digest = load_glb(model_path)
    candidates = {item["id"]: item for item in dataset["model_mappings"]}
    versions = {item["id"]: item for item in dataset["entities"] if item["kind"] == "ModelVersion"}
    triangles, colors, owners = geometry(model, binary)
    for record in records:
        mapping = candidates[record["mapping_id"]]
        if versions[mapping["model_version_id"]]["content_sha256"] != digest:
            raise ValueError(f"Model hash changed for {mapping['id']}")
        nodes = descendants(model, mapping["node_indices"])
        focus = np.isin(owners, list(nodes))
        if not focus.any():
            raise ValueError(f"No geometry under {mapping['id']}")
        render(output / record["filename"], triangles, colors, focus)
    render(output / "model-overview.png", triangles, colors)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    data = json.loads(args.dataset.read_text(encoding="utf-8"))
    render_registered_views(args.model, [r for r in manifest["items"] if r["kind"] == "model_view"], data, args.output)
