#!/usr/bin/env python3
"""Strict Phase 2 verification — exits non-zero on failure."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageStat

ROOT = Path(__file__).resolve().parents[2]
SCENES = ROOT / "assets" / "scenes"
PHASE2 = Path(__file__).resolve().parent
BASELINE_PATH = PHASE2 / ".papa-gate-baseline.json"
PHASE_START = "17bef48"
PRODUCTION_FILES = ["index.html", "style.css", "script.js"]
PAPA_APPROVED_SOURCE = "assets/images/temporary/papa-temp-clean.png"
MAMA_APPROVED_SOURCE = "assets/images/temporary/mama-temp-clean.png"
VOYA_APPROVED_SOURCE = "assets/images/temporary/voya-temp-clean.png"
PAPA_APPROVED_BASELINE_PATH = PHASE2 / ".papa-approved-baseline.json"
MAMA_APPROVED_BASELINE_PATH = PHASE2 / ".mama-approved-baseline.json"
VOYA_APPROVED_BASELINE_PATH = PHASE2 / ".voya-approved-baseline.json"
HOUSE_APPROVED_SOURCE = "assets/images/temporary/house-temp-clean.png"
PAPA_REQUIRED_LAYERS = ("papa-shadow", "papa-body", "papa-head", "papa-serving-group")
MAMA_REQUIRED_LAYERS = ("mama-shadow", "mama-body", "mama-head", "mama-serving-group")
VOYA_REQUIRED_LAYERS = ("voya-shadow", "voya-body", "voya-head", "voya-cup-group")
PAPA_OBSOLETE_LAYERS = ("papa-arm-left", "papa-plate", "papa-ingredients")
MAMA_OBSOLETE_LAYERS = ("mama-arm-right", "mama-pizza")
VOYA_OBSOLETE_LAYERS = ("voya-arm-right", "voya-cup")
PAPA_ALLOWED_FILES = {
    "manifest.json",
    "papa-shadow.png",
    "papa-body.png",
    "papa-head.png",
    "papa-serving-group.png",
    "papa-mobile-fallback.png",
    "papa-source-reference.png",
}
MAMA_ALLOWED_FILES = {
    "manifest.json",
    "mama-shadow.png",
    "mama-body.png",
    "mama-head.png",
    "mama-serving-group.png",
    "mama-mobile-fallback.png",
    "mama-source-reference.png",
}
VOYA_ALLOWED_FILES = {
    "manifest.json",
    "voya-shadow.png",
    "voya-body.png",
    "voya-head.png",
    "voya-cup-group.png",
    "voya-mobile-fallback.png",
    "voya-source-reference.png",
}
# Localized shirt underpaint under serving may overlap in the patch/joint only.
MAX_SERVING_BODY_DUPLICATE_RATIO = 0.25
# Voya cup joint keeps a localized shirt stump under the opaque mover.
MAX_VOYA_CUP_BODY_DUPLICATE_RATIO = 0.45
MAX_HEAD_BODY_NECK_RATIO = 0.15
# Neutral layers are direct masks from the approved source. Tiny RGB deltas can remain
# where motion underpaint sits under antialiased mover edges (alpha unchanged).
MAX_NEUTRAL_RGB_MEAN = 0.0
MAX_NEUTRAL_RGB_MAX = 0.0
MAX_NEUTRAL_ALPHA_MEAN = 0.0
MAX_NEUTRAL_ALPHA_MAX = 0.0
MAX_NEUTRAL_DIFF_PIXELS = 0
# Fallback vs reduced-motion browser captures should be identical (same render path).
MAX_FALLBACK_RM_DIFF_PIXELS = 0
VIEWPORT_SIZES = {"desktop": (1440, 900), "mobile": (390, 844)}
VALID_CHARACTERS = ("papa", "mama", "voya")
FORBIDDEN_PATHS = [
    PHASE2 / "__pycache__",
    PHASE2 / "_tmp_mama_debug",
    PHASE2 / "_tmp_voya_debug",
    PHASE2 / "_house-fit-preview.html",
]


class VerificationError(Exception):
    pass


def fail(message: str) -> None:
    raise VerificationError(message)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def snapshot_character_dir(char_dir: Path) -> dict[str, str]:
    if not char_dir.is_dir():
        return {}
    return {
        str(path.relative_to(char_dir)).replace("\\", "/"): sha256_file(path)
        for path in sorted(char_dir.rglob("*"))
        if path.is_file()
    }


def alpha_mask(image: Image.Image, threshold: int = 16) -> Image.Image:
    return image.split()[3].point(lambda value: 255 if value > threshold else 0)


def load_rgba(path: Path) -> Image.Image:
    return Image.open(path).convert("RGBA")


def mask_pixels(mask: Image.Image) -> int:
    return sum(1 for value in mask.get_flattened_data() if value)


def overlap_count(a: Image.Image, b: Image.Image) -> int:
    if a.size != b.size:
        b = b.resize(a.size)
    ap = alpha_mask(a).load()
    bp = alpha_mask(b).load()
    w, h = a.size
    return sum(1 for y in range(h) for x in range(w) if ap[x, y] and bp[x, y])


def duplicate_ratio(inner: Image.Image, outer: Image.Image) -> float:
    inner_count = mask_pixels(alpha_mask(inner))
    if inner_count == 0:
        return 0.0
    return overlap_count(inner, outer) / inner_count


def place_layer(canvas_size: tuple[int, int], layer_img: Image.Image, offset: dict) -> Image.Image:
    placed = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
    placed.alpha_composite(layer_img, (offset["x"], offset["y"]))
    return placed


def composite_layers(manifest: dict, char_dir: Path, include_shadow: bool = False) -> Image.Image:
    canvas = Image.new("RGBA", (manifest["sceneCanvas"]["width"], manifest["sceneCanvas"]["height"]), (0, 0, 0, 0))
    for layer in sorted(manifest["layers"], key=lambda item: item["zIndex"]):
        if layer.get("group") == "shadow" and not include_shadow:
            continue
        img = load_rgba(char_dir / layer["file"])
        canvas.alpha_composite(img, (layer["sceneOffset"]["x"], layer["sceneOffset"]["y"]))
    return canvas


def overlap_in_zone(a: Image.Image, b: Image.Image, zone: dict | None) -> int:
    if not zone:
        return overlap_count(a, b)
    x0, y0, x1, y1 = zone["x0"], zone["y0"], zone["x1"], zone["y1"]
    cropped_a = a.crop((x0, y0, x1 + 1, y1 + 1))
    cropped_b = b.crop((x0, y0, x1 + 1, y1 + 1))
    return overlap_count(cropped_a, cropped_b)


def git_unchanged(paths: list[Path]) -> None:
    for path in paths:
        result = subprocess.run(
            [
                "git",
                "-c",
                f"safe.directory={ROOT.as_posix()}",
                "diff",
                "--quiet",
                PHASE_START,
                "--",
                str(path.relative_to(ROOT)).replace("\\", "/"),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            fail(f"Production file changed since {PHASE_START}: {path.relative_to(ROOT)}")


def check_encoding(path: Path) -> None:
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        fail(f"Invalid UTF-8 in {path.relative_to(ROOT)}: {error}")
    if "\ufffd" in text:
        fail(f"Replacement character / mojibake in {path.relative_to(ROOT)}")
    if re.search(r"^<<<<<<< |^=======|^>>>>>>> ", text, re.MULTILINE):
        fail(f"Conflict markers in {path.relative_to(ROOT)}")
    if re.search(r"(?:^|\s)(?:#|//)\s*TODO\b", text, re.IGNORECASE | re.MULTILINE):
        fail(f"TODO placeholder found in {path.relative_to(ROOT)}")
    for index, line in enumerate(text.splitlines(), start=1):
        if line.rstrip("\n") != line.rstrip("\n").rstrip(" \t"):
            fail(f"Trailing whitespace in {path.relative_to(ROOT)}:{index}")


def check_no_temp_artifacts() -> None:
    for path in FORBIDDEN_PATHS:
        if path.exists():
            fail(f"Temporary artifact present: {path.relative_to(ROOT)}")
    for pyc in PHASE2.rglob("*.pyc"):
        fail(f"Bytecode artifact present: {pyc.relative_to(ROOT)}")


def load_persisted_baseline() -> dict:
    if not BASELINE_PATH.is_file():
        fail(f"Missing persisted baseline: {BASELINE_PATH.relative_to(ROOT)}")
    try:
        baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        fail(f"Malformed baseline JSON: {error}")
    for name in ("mama", "voya"):
        if name not in baseline or not isinstance(baseline[name], dict) or not baseline[name]:
            fail(f"Baseline incomplete: missing {name} hashes")
        expected_files = set(baseline[name].keys())
        if "manifest.json" not in expected_files:
            fail(f"Baseline incomplete: {name} missing manifest.json")
    return baseline


def verify_protected_baseline(baseline: dict) -> None:
    for name in ("mama", "voya"):
        current = snapshot_character_dir(SCENES / name)
        expected = baseline[name]
        if current != expected:
            missing = sorted(set(expected) - set(current))
            extra = sorted(set(current) - set(expected))
            changed = sorted(k for k in expected if k in current and expected[k] != current[k])
            fail(
                f"{name}: outputs diverge from persisted baseline "
                f"(changed={changed[:5]}, missing={missing[:5]}, extra={extra[:5]})"
            )
        evidence_dir = PHASE2 / "evidence" / name
        if evidence_dir.is_dir():
            # Evidence may exist from prior work; Papa-scoped runs must not rewrite it.
            # Hash protection applies to scene outputs via baseline; evidence touch is blocked
            # by prepare/capture scoping. If evidence exists, require non-empty PNGs only when
            # verifying that character.
            pass

    registry_path = SCENES / "registry.json"
    if not registry_path.is_file():
        fail("Missing assets/scenes/registry.json")
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    for name in ("mama", "voya"):
        rel = registry.get("manifests", {}).get(name)
        if rel != f"assets/scenes/{name}/manifest.json":
            fail(f"Registry Mama/Voya path altered for {name}: {rel}")
        manifest_path = ROOT / rel
        if not manifest_path.is_file():
            fail(f"Registry points to missing manifest: {rel}")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("character") != name:
            fail(f"Manifest character mismatch for {name}")


def rgba_compare_full(a: Image.Image, b: Image.Image) -> dict:
    if a.size != b.size:
        fail(f"RGBA size mismatch {a.size} vs {b.size}")
    a = a.convert("RGBA")
    b = b.convert("RGBA")
    ar, ag, ab, aa = a.split()
    br, bg, bb, ba = b.split()
    dr = ImageChops.difference(ar, br)
    dg = ImageChops.difference(ag, bg)
    db = ImageChops.difference(ab, bb)
    da = ImageChops.difference(aa, ba)
    rgb_diff = ImageChops.add(ImageChops.add(dr, dg), db)
    rgb_stat = ImageStat.Stat(rgb_diff)
    alpha_stat = ImageStat.Stat(da)
    # Count any channel difference including alpha-only.
    diff_mask = ImageChops.lighter(ImageChops.lighter(ImageChops.lighter(dr, dg), db), da)
    differing = sum(1 for value in diff_mask.get_flattened_data() if value)
    return {
        "rgbMean": float(rgb_stat.mean[0]),
        "rgbMax": float(rgb_stat.extrema[0][1]),
        "alphaMean": float(alpha_stat.mean[0]),
        "alphaMax": float(alpha_stat.extrema[0][1]),
        "differingPixels": differing,
        "totalPixels": a.width * a.height,
    }


def verify_papa_source_rgba(manifest: dict, char_dir: Path, char_result: dict) -> None:
    source_meta = manifest["source"]
    if source_meta["path"] != PAPA_APPROVED_SOURCE:
        fail(f"papa: approved source must be {PAPA_APPROVED_SOURCE}")
    source_file = ROOT / PAPA_APPROVED_SOURCE
    if not source_file.is_file():
        fail(f"papa: missing approved source {PAPA_APPROVED_SOURCE}")

    source_img = load_rgba(source_file)
    bbox = source_meta["bbox"]
    cropped = source_img.crop((bbox["x0"], bbox["y0"], bbox["x1"] + 1, bbox["y1"] + 1))
    # Trim to alpha bbox to match generator extract_transparent behavior.
    alpha = cropped.split()[3]
    trim_box = alpha.getbbox()
    if not trim_box:
        fail("papa: approved source crop has no opaque pixels")
    approved = cropped.crop(trim_box)

    composite = composite_layers(manifest, char_dir, include_shadow=False)
    if composite.size != approved.size:
        fail(f"papa: composite size {composite.size} != approved trim {approved.size}")

    stats = rgba_compare_full(composite, approved)
    char_result["neutralSourceCompare"] = {
        "source": PAPA_APPROVED_SOURCE,
        "bbox": bbox,
        "approvedTrimSize": {"width": approved.width, "height": approved.height},
        **stats,
        "tolerance": {
            "rgbMean": MAX_NEUTRAL_RGB_MEAN,
            "rgbMax": MAX_NEUTRAL_RGB_MAX,
            "alphaMean": MAX_NEUTRAL_ALPHA_MEAN,
            "alphaMax": MAX_NEUTRAL_ALPHA_MAX,
            "differingPixels": MAX_NEUTRAL_DIFF_PIXELS,
            "note": "Zero tolerance: neutral composite must match the approved source crop exactly (RGBA including alpha).",
        },
    }
    if stats["rgbMean"] > MAX_NEUTRAL_RGB_MEAN or stats["rgbMax"] > MAX_NEUTRAL_RGB_MAX:
        fail(f"papa: neutral RGB differs from approved source (mean={stats['rgbMean']}, max={stats['rgbMax']})")
    if stats["alphaMean"] > MAX_NEUTRAL_ALPHA_MEAN or stats["alphaMax"] > MAX_NEUTRAL_ALPHA_MAX:
        fail(f"papa: neutral alpha differs from approved source (mean={stats['alphaMean']}, max={stats['alphaMax']})")
    if stats["differingPixels"] > MAX_NEUTRAL_DIFF_PIXELS:
        fail(f"papa: neutral differs from approved source by {stats['differingPixels']} pixels")


def verify_papa_layer_contract(manifest: dict, char_dir: Path) -> None:
    layer_ids = [layer["id"] for layer in manifest["layers"]]
    if tuple(layer_ids) != PAPA_REQUIRED_LAYERS and set(layer_ids) != set(PAPA_REQUIRED_LAYERS):
        # Exact set required; order by zIndex may vary but ids must match exactly.
        if set(layer_ids) != set(PAPA_REQUIRED_LAYERS) or len(layer_ids) != len(PAPA_REQUIRED_LAYERS):
            fail(f"papa: layer contract mismatch: {layer_ids}")
    for required in PAPA_REQUIRED_LAYERS:
        if required not in layer_ids:
            fail(f"papa: missing required layer {required}")
    for obsolete in PAPA_OBSOLETE_LAYERS:
        if obsolete in layer_ids or (char_dir / f"{obsolete}.png").is_file():
            fail(f"papa: obsolete layer still present: {obsolete}")

    on_disk = {path.name for path in char_dir.iterdir() if path.is_file()}
    extra = sorted(on_disk - PAPA_ALLOWED_FILES)
    missing = sorted(PAPA_ALLOWED_FILES - on_disk)
    if extra:
        fail(f"papa: unexpected files in scene dir: {extra}")
    if missing:
        fail(f"papa: missing required files: {missing}")
    effects_dir = char_dir / "effects"
    if effects_dir.is_dir():
        effect_pngs = list(effects_dir.glob("*.png"))
        if len(effect_pngs) < 4:
            fail(f"papa: expected at least 4 effect sprites, found {len(effect_pngs)}")
        for path in effect_pngs:
            if path.stat().st_size < 100:
                fail(f"papa: empty effect sprite {path.name}")
    else:
        fail("papa: missing effects/ directory for Phase 4 food accents")

    for layer in manifest["layers"]:
        path = char_dir / layer["file"]
        if not path.is_file():
            fail(f"papa: manifest file missing on disk: {layer['file']}")
        if layer["file"] != f"{layer['id']}.png":
            fail(f"papa: layer file name mismatch for {layer['id']}")


def png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        fail(f"Invalid PNG header: {path.relative_to(ROOT)}")
    width, height = struct.unpack(">II", data[16:24])
    return width, height


def evidence_is_blank(image: Image.Image) -> bool:
    # Checkerboard/beige stage still has variance; blank means nearly uniform.
    extrema = image.convert("L").getextrema()
    if extrema[0] == extrema[1]:
        return True
    # Also reject fully-transparent captures.
    alpha = image.split()[3] if image.mode == "RGBA" else None
    if alpha is not None and alpha.getextrema() == (0, 0):
        return True
    # Require some darker ink-like pixels (Papa outlines are near-black).
    hist = image.convert("L").histogram()
    dark = sum(hist[:40])
    return dark < 200


def verify_papa_evidence(manifest: dict, char_result: dict) -> None:
    browser_root = PHASE2 / "evidence" / "papa" / "browser"
    if not browser_root.is_dir():
        fail("Missing Papa browser evidence directory")

    required = [
        "neutral_reconstruction_desktop.png",
        "neutral_reconstruction_mobile.png",
        "fallback_desktop.png",
        "fallback_mobile.png",
        "reduced_motion_desktop.png",
        "reduced_motion_mobile.png",
        "papa-head_static_desktop.png",
        "papa-head_static_mobile.png",
        "papa-serving-group_min_desktop.png",
        "papa-serving-group_max_desktop.png",
        "papa-serving-group_min_mobile.png",
        "papa-serving-group_max_mobile.png",
        "combined_min_desktop.png",
        "combined_max_desktop.png",
        "combined_min_mobile.png",
        "combined_max_mobile.png",
    ]
    missing = [name for name in required if not (browser_root / name).is_file()]
    if missing:
        fail(f"papa: missing evidence files: {missing}")

    content_checks = []
    for name in required:
        path = browser_root / name
        if path.stat().st_size < 32:
            fail(f"papa: evidence file empty/too small: {name}")
        width, height = png_size(path)
        viewport = "desktop" if name.endswith("_desktop.png") else "mobile"
        expected = VIEWPORT_SIZES[viewport]
        if (width, height) != expected:
            fail(f"papa: evidence {name} size {width}x{height} != {expected[0]}x{expected[1]}")
        if path.stat().st_size < 1000:
            fail(f"papa: evidence file empty/too small: {name}")
        image = load_rgba(path)
        if evidence_is_blank(image):
            fail(f"papa: evidence appears blank / no Papa ink: {name}")
        content_checks.append({"file": name, "width": width, "height": height, "bytes": path.stat().st_size})

    # Fallback must equal reduced-motion (same layered neutral render path).
    for viewport in ("desktop", "mobile"):
        fb = load_rgba(browser_root / f"fallback_{viewport}.png")
        rm = load_rgba(browser_root / f"reduced_motion_{viewport}.png")
        stats = rgba_compare_full(fb, rm)
        if stats["differingPixels"] > MAX_FALLBACK_RM_DIFF_PIXELS:
            fail(
                f"papa: fallback vs reduced-motion differ on {viewport} "
                f"by {stats['differingPixels']} pixels (tolerance {MAX_FALLBACK_RM_DIFF_PIXELS})"
            )
        char_result.setdefault("fallbackReducedMotion", {})[viewport] = stats

    # Generation fingerprint: store hash of current serving-group layer into check notes.
    serving_hash = sha256_file(SCENES / "papa" / "papa-serving-group.png")[:16]
    char_result["evidenceGenerationFingerprint"] = serving_hash
    char_result["browserEvidence"] = {
        "root": str(browser_root.relative_to(ROOT)).replace("\\", "/"),
        "requiredCount": len(required),
        "checks": content_checks,
    }


def verify_papa_semantics(manifest: dict, char_dir: Path, char_result: dict) -> None:
    canvas_w = manifest["sceneCanvas"]["width"]
    canvas_h = manifest["sceneCanvas"]["height"]
    placed = {
        layer["id"]: place_layer((canvas_w, canvas_h), load_rgba(char_dir / layer["file"]), layer["sceneOffset"])
        for layer in manifest["layers"]
        if layer.get("group") != "shadow"
    }

    serving_id = "papa-serving-group"
    body_id = "papa-body"
    head_id = "papa-head"
    ratio = duplicate_ratio(placed[serving_id], placed[body_id])
    char_result["servingBodyDuplicateRatio"] = round(ratio, 6)
    if ratio >= 0.99:
        fail(f"papa: serving-group is 100% duplicated in body ({ratio:.2%})")
    if ratio > MAX_SERVING_BODY_DUPLICATE_RATIO:
        fail(f"papa: serving-group/body overlap exceeds underpaint tolerance ({ratio:.2%})")

    head_ratio = duplicate_ratio(placed[head_id], placed[body_id])
    char_result["headBodyDuplicateRatio"] = round(head_ratio, 6)
    if head_ratio > MAX_HEAD_BODY_NECK_RATIO:
        fail(f"papa: head/body overlap exceeds neck zone tolerance ({head_ratio:.2%})")

    # Serving group must be substantial (arms+plate+food); body must not be empty.
    if mask_pixels(alpha_mask(placed[serving_id])) < 20000:
        fail("papa: serving-group mask too small to contain arms/plate/food")
    if mask_pixels(alpha_mask(placed[body_id])) < 20000:
        fail("papa: body mask too small")

    for layer in manifest["layers"]:
        motion = layer.get("motion")
        if layer["id"] == "papa-head":
            if motion not in (None, {}):
                fail(f"papa: head must remain static (motion blocked), got {motion}")
        if layer["id"] == "papa-serving-group":
            if not motion or not motion.get("rotate") or motion["rotate"][0] >= 0 or motion["rotate"][1] <= 0:
                fail(f"papa: serving-group motion must be a non-zero ± range, got {motion}")
            if abs(motion["rotate"][0]) > 3 or abs(motion["rotate"][1]) > 3:
                fail(f"papa: serving-group rotation exceeds ±3°, got {motion}")
        offset = layer["sceneOffset"]
        size = layer["size"]
        if offset["x"] < 0 or offset["y"] < 0:
            fail(f"{layer['id']} negative offset")
        if offset["x"] + size["width"] > canvas_w or offset["y"] + size["height"] > canvas_h:
            fail(f"{layer['id']} exceeds scene canvas")
        pivot = layer.get("pivot")
        if not pivot or pivot["x"] < 0 or pivot["y"] < 0:
            fail(f"{layer['id']} invalid pivot")
        if not layer.get("transformOrigin"):
            fail(f"{layer['id']} missing transformOrigin")


def verify_approved_source_basics(name: str, source_rel: str, char_result: dict) -> Image.Image:
    source_file = ROOT / source_rel
    if not source_file.is_file():
        fail(f"{name}: missing approved source {source_rel}")
    source_img = load_rgba(source_file)
    char_result["sourceDimensions"] = {"width": source_img.width, "height": source_img.height}
    if source_img.split()[3].getextrema()[0] >= 255:
        fail(f"{name}: approved source lacks transparency")
    magenta = 0
    px = source_img.load()
    for y in range(source_img.height):
        for x in range(source_img.width):
            r, g, b, a = px[x, y]
            if a > 16 and r > 240 and b > 240 and g < 50:
                magenta += 1
    char_result["magentaPixels"] = magenta
    if magenta:
        fail(f"{name}: approved source contains magenta residue ({magenta}px)")
    return source_img


def verify_source_rgba(name: str, approved_source: str, manifest: dict, char_dir: Path, char_result: dict) -> None:
    source_meta = manifest["source"]
    if source_meta["path"] != approved_source:
        fail(f"{name}: approved source must be {approved_source}")
    source_img = load_rgba(ROOT / approved_source)
    bbox = source_meta["bbox"]
    cropped = source_img.crop((bbox["x0"], bbox["y0"], bbox["x1"] + 1, bbox["y1"] + 1))
    alpha = cropped.split()[3]
    trim_box = alpha.getbbox()
    if not trim_box:
        fail(f"{name}: approved source crop has no opaque pixels")
    approved = cropped.crop(trim_box)
    composite = composite_layers(manifest, char_dir, include_shadow=False)
    if composite.size != approved.size:
        fail(f"{name}: composite size {composite.size} != approved trim {approved.size}")
    stats = rgba_compare_full(composite, approved)
    char_result["neutralSourceCompare"] = {
        "source": approved_source,
        "bbox": bbox,
        "approvedTrimSize": {"width": approved.width, "height": approved.height},
        **stats,
        "tolerance": {
            "rgbMean": MAX_NEUTRAL_RGB_MEAN,
            "rgbMax": MAX_NEUTRAL_RGB_MAX,
            "alphaMean": MAX_NEUTRAL_ALPHA_MEAN,
            "alphaMax": MAX_NEUTRAL_ALPHA_MAX,
            "differingPixels": MAX_NEUTRAL_DIFF_PIXELS,
            "note": "Zero tolerance: neutral composite must match the approved source crop exactly (RGBA including alpha).",
        },
    }
    if stats["rgbMean"] > MAX_NEUTRAL_RGB_MEAN or stats["rgbMax"] > MAX_NEUTRAL_RGB_MAX:
        fail(f"{name}: neutral RGB differs from approved source (mean={stats['rgbMean']}, max={stats['rgbMax']})")
    if stats["alphaMean"] > MAX_NEUTRAL_ALPHA_MEAN or stats["alphaMax"] > MAX_NEUTRAL_ALPHA_MAX:
        fail(f"{name}: neutral alpha differs from approved source (mean={stats['alphaMean']}, max={stats['alphaMax']})")
    if stats["differingPixels"] > MAX_NEUTRAL_DIFF_PIXELS:
        fail(f"{name}: neutral differs from approved source by {stats['differingPixels']} pixels")


def verify_layer_contract(
    name: str,
    manifest: dict,
    char_dir: Path,
    required_layers: tuple[str, ...],
    obsolete_layers: tuple[str, ...],
    allowed_files: set[str],
    require_effects: bool = False,
) -> None:
    layer_ids = [layer["id"] for layer in manifest["layers"]]
    if set(layer_ids) != set(required_layers) or len(layer_ids) != len(required_layers):
        fail(f"{name}: layer contract mismatch: {layer_ids}")
    for obsolete in obsolete_layers:
        if obsolete in layer_ids or (char_dir / f"{obsolete}.png").is_file():
            fail(f"{name}: obsolete layer still present: {obsolete}")
    on_disk = {path.name for path in char_dir.iterdir() if path.is_file()}
    extra = sorted(on_disk - allowed_files)
    missing = sorted(allowed_files - on_disk)
    if extra:
        fail(f"{name}: unexpected files in scene dir: {extra}")
    if missing:
        fail(f"{name}: missing required files: {missing}")
    if require_effects:
        effects_dir = char_dir / "effects"
        if not effects_dir.is_dir():
            fail(f"{name}: missing effects/ directory")
        effect_pngs = list(effects_dir.glob("*.png"))
        if len(effect_pngs) < 4:
            fail(f"{name}: expected at least 4 effect sprites, found {len(effect_pngs)}")
    for layer in manifest["layers"]:
        path = char_dir / layer["file"]
        if not path.is_file():
            fail(f"{name}: manifest file missing on disk: {layer['file']}")
        if layer["file"] != f"{layer['id']}.png":
            fail(f"{name}: layer file name mismatch for {layer['id']}")


def verify_serving_semantics(
    name: str,
    manifest: dict,
    char_dir: Path,
    char_result: dict,
    serving_id: str,
    require_nonzero_serving: bool,
) -> None:
    canvas_w = manifest["sceneCanvas"]["width"]
    canvas_h = manifest["sceneCanvas"]["height"]
    placed = {
        layer["id"]: place_layer((canvas_w, canvas_h), load_rgba(char_dir / layer["file"]), layer["sceneOffset"])
        for layer in manifest["layers"]
        if layer.get("group") != "shadow"
    }
    body_id = f"{name}-body"
    head_id = f"{name}-head"
    ratio = duplicate_ratio(placed[serving_id], placed[body_id])
    char_result["servingBodyDuplicateRatio"] = round(ratio, 6)
    if ratio >= 0.99:
        fail(f"{name}: serving group is 100% duplicated in body ({ratio:.2%})")
    max_dup = MAX_VOYA_CUP_BODY_DUPLICATE_RATIO if name == "voya" else MAX_SERVING_BODY_DUPLICATE_RATIO
    if ratio > max_dup:
        fail(f"{name}: serving/body overlap exceeds underpaint tolerance ({ratio:.2%})")
    head_ratio = duplicate_ratio(placed[head_id], placed[body_id])
    char_result["headBodyDuplicateRatio"] = round(head_ratio, 6)
    if head_ratio > MAX_HEAD_BODY_NECK_RATIO:
        fail(f"{name}: head/body overlap exceeds neck zone tolerance ({head_ratio:.2%})")
    if mask_pixels(alpha_mask(placed[serving_id])) < 10000:
        fail(f"{name}: serving/cup group mask too small")
    if mask_pixels(alpha_mask(placed[body_id])) < 20000:
        fail(f"{name}: body mask too small")

    for layer in manifest["layers"]:
        motion = layer.get("motion")
        if layer["id"] == head_id and motion not in (None, {}):
            fail(f"{name}: head must remain static (motion blocked), got {motion}")
        if layer["id"] == serving_id:
            blocked = serving_id in (manifest.get("motionBlocked") or [])
            if require_nonzero_serving and not blocked:
                if not motion or not motion.get("rotate") or motion["rotate"][0] >= 0 or motion["rotate"][1] <= 0:
                    fail(f"{name}: serving motion must be a non-zero ± range, got {motion}")
                if abs(motion["rotate"][0]) > 3 or abs(motion["rotate"][1]) > 3:
                    fail(f"{name}: serving rotation exceeds ±3°, got {motion}")
            elif blocked and motion not in (None, {}):
                fail(f"{name}: serving motion listed as blocked but motion={motion}")
        offset = layer["sceneOffset"]
        size = layer["size"]
        if offset["x"] < 0 or offset["y"] < 0:
            fail(f"{layer['id']} negative offset")
        if offset["x"] + size["width"] > canvas_w or offset["y"] + size["height"] > canvas_h:
            fail(f"{layer['id']} exceeds scene canvas")
        pivot = layer.get("pivot")
        if not pivot or pivot["x"] < 0 or pivot["y"] < 0:
            fail(f"{layer['id']} invalid pivot")
        if not layer.get("transformOrigin"):
            fail(f"{layer['id']} missing transformOrigin")


def verify_browser_evidence(name: str, manifest: dict, char_result: dict, serving_id: str) -> None:
    browser_root = PHASE2 / "evidence" / name / "browser"
    if not browser_root.is_dir():
        fail(f"Missing {name} browser evidence directory")
    required = [
        "neutral_reconstruction_desktop.png",
        "neutral_reconstruction_mobile.png",
        "fallback_desktop.png",
        "fallback_mobile.png",
        "reduced_motion_desktop.png",
        "reduced_motion_mobile.png",
        f"{name}-head_static_desktop.png",
        f"{name}-head_static_mobile.png",
        "combined_min_desktop.png",
        "combined_max_desktop.png",
        "combined_min_mobile.png",
        "combined_max_mobile.png",
    ]
    serving_layer = next((layer for layer in manifest["layers"] if layer["id"] == serving_id), None)
    if serving_layer and serving_layer.get("motion"):
        required.extend(
            [
                f"{serving_id}_min_desktop.png",
                f"{serving_id}_max_desktop.png",
                f"{serving_id}_min_mobile.png",
                f"{serving_id}_max_mobile.png",
            ]
        )
    missing = [item for item in required if not (browser_root / item).is_file()]
    if missing:
        fail(f"{name}: missing evidence files: {missing}")

    content_checks = []
    for item in required:
        path = browser_root / item
        if path.stat().st_size < 32:
            fail(f"{name}: evidence file empty/too small: {item}")
        width, height = png_size(path)
        viewport = "desktop" if item.endswith("_desktop.png") else "mobile"
        expected = VIEWPORT_SIZES[viewport]
        if (width, height) != expected:
            fail(f"{name}: evidence {item} size {width}x{height} != {expected[0]}x{expected[1]}")
        if path.stat().st_size < 1000:
            fail(f"{name}: evidence file empty/too small: {item}")
        image = load_rgba(path)
        if evidence_is_blank(image):
            fail(f"{name}: evidence appears blank / no ink: {item}")
        content_checks.append({"file": item, "width": width, "height": height, "bytes": path.stat().st_size})

    for viewport in ("desktop", "mobile"):
        fb = load_rgba(browser_root / f"fallback_{viewport}.png")
        rm = load_rgba(browser_root / f"reduced_motion_{viewport}.png")
        stats = rgba_compare_full(fb, rm)
        if stats["differingPixels"] > MAX_FALLBACK_RM_DIFF_PIXELS:
            fail(
                f"{name}: fallback vs reduced-motion differ on {viewport} "
                f"by {stats['differingPixels']} pixels"
            )
        char_result.setdefault("fallbackReducedMotion", {})[viewport] = stats

    fingerprint_file = SCENES / name / f"{serving_id}.png"
    if fingerprint_file.is_file():
        char_result["evidenceGenerationFingerprint"] = sha256_file(fingerprint_file)[:16]
    char_result["browserEvidence"] = {
        "root": str(browser_root.relative_to(ROOT)).replace("\\", "/"),
        "requiredCount": len(required),
        "checks": content_checks,
    }


def verify_baseline_snapshot(path: Path, character: str) -> None:
    if not path.is_file():
        fail(f"Missing approved baseline: {path.relative_to(ROOT)}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        fail(f"Malformed baseline {path.name}: {error}")
    expected = payload.get(character)
    if not isinstance(expected, dict) or not expected:
        fail(f"Baseline {path.name} missing {character} hashes")
    current = snapshot_character_dir(SCENES / character)
    if current != expected:
        changed = sorted(k for k in expected if k in current and expected[k] != current[k])
        missing = sorted(set(expected) - set(current))
        extra = sorted(set(current) - set(expected))
        fail(
            f"{character}: diverges from approved baseline {path.name} "
            f"(changed={changed[:5]}, missing={missing[:5]}, extra={extra[:5]})"
        )


def verify_character_papa(results: dict) -> None:
    char_dir = SCENES / "papa"
    manifest_path = char_dir / "manifest.json"
    if not manifest_path.is_file():
        fail("Missing Papa manifest")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("character") != "papa":
        fail("Papa manifest character field invalid")
    char_result: dict = {"layers": {}, "jointOverlaps": manifest.get("jointOverlaps", [])}
    verify_approved_source_basics("papa", PAPA_APPROVED_SOURCE, char_result)
    verify_layer_contract(
        "papa",
        manifest,
        char_dir,
        PAPA_REQUIRED_LAYERS,
        PAPA_OBSOLETE_LAYERS,
        PAPA_ALLOWED_FILES,
        require_effects=True,
    )
    for layer in manifest["layers"]:
        image = load_rgba(char_dir / layer["file"])
        expected = layer["size"]
        if image.width != expected["width"] or image.height != expected["height"]:
            fail(f"{layer['id']} dimension mismatch")
        char_result["layers"][layer["id"]] = {
            "group": layer.get("group"),
            "size": expected,
            "offset": layer["sceneOffset"],
            "motion": layer.get("motion"),
            "pivot": layer.get("pivot"),
            "transformOrigin": layer.get("transformOrigin"),
        }
    verify_source_rgba("papa", PAPA_APPROVED_SOURCE, manifest, char_dir, char_result)
    verify_serving_semantics("papa", manifest, char_dir, char_result, "papa-serving-group", True)
    verify_browser_evidence("papa", manifest, char_result, "papa-serving-group")
    results["characters"]["papa"] = char_result


def verify_house(results: dict) -> None:
    house_dir = SCENES / "house"
    manifest_path = house_dir / "manifest.json"
    if not manifest_path.is_file():
        fail("Missing House manifest")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("type") != "static-2d-background":
        fail("house: must be a static-2d-background asset")
    if manifest.get("source", {}).get("path") != HOUSE_APPROVED_SOURCE:
        fail(f"house: approved source must be {HOUSE_APPROVED_SOURCE}")
    if manifest.get("validation", {}).get("splitIntoLayers"):
        fail("house: must not be split into fake 3D / layer pieces")
    if manifest.get("validation", {}).get("rasterBrandingText"):
        fail("house: must not include rasterized branding text")

    static_path = house_dir / manifest["file"]
    if not static_path.is_file():
        fail("house: missing house-static.png")
    source = load_rgba(ROOT / HOUSE_APPROVED_SOURCE)
    static = load_rgba(static_path)
    if static.size != source.size:
        fail(f"house: static size {static.size} != source {source.size}")
    stats = rgba_compare_full(static, source)
    if stats["differingPixels"]:
        fail(f"house: static asset differs from approved source by {stats['differingPixels']} pixels")

    magenta = 0
    px = source.load()
    for y in range(source.height):
        for x in range(source.width):
            r, g, b, a = px[x, y]
            if a > 16 and r > 240 and b > 240 and g < 50:
                magenta += 1
    if magenta:
        fail(f"house: magenta residue ({magenta}px)")
    if source.split()[3].getextrema()[0] >= 255:
        fail("house: approved source lacks transparency")

    browser_root = PHASE2 / "evidence" / "house" / "browser"
    required = ["house_fit_desktop.png", "house_fit_mobile.png"]
    missing = [name for name in required if not (browser_root / name).is_file()]
    if missing:
        fail(f"house: missing evidence files: {missing}")
    checks = []
    for name in required:
        path = browser_root / name
        width, height = png_size(path)
        expected = VIEWPORT_SIZES["desktop" if "desktop" in name else "mobile"]
        if (width, height) != expected:
            fail(f"house: evidence {name} size {width}x{height} != {expected}")
        image = load_rgba(path)
        extrema = image.convert("L").getextrema()
        if extrema[0] == extrema[1] or path.stat().st_size < 1000:
            fail(f"house: evidence appears blank: {name}")
        # House art is pastel; require visible outline/structure variance rather than near-black ink count.
        hist = image.convert("L").histogram()
        if sum(hist[:90]) < 80:
            fail(f"house: evidence lacks structure/ink: {name}")
        checks.append({"file": name, "width": width, "height": height, "bytes": path.stat().st_size})

    results["house"] = {
        "source": HOUSE_APPROVED_SOURCE,
        "size": {"width": source.width, "height": source.height},
        "magentaPixels": magenta,
        "staticMatchesSource": True,
        "browserEvidence": {"root": str(browser_root.relative_to(ROOT)).replace("\\", "/"), "checks": checks},
    }


def verify_character_voya(results: dict) -> None:
    char_dir = SCENES / "voya"
    manifest_path = char_dir / "manifest.json"
    if not manifest_path.is_file():
        fail("Missing Voya manifest")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("character") != "voya":
        fail("Voya manifest character field invalid")
    char_result: dict = {"layers": {}, "jointOverlaps": manifest.get("jointOverlaps", [])}
    verify_approved_source_basics("voya", VOYA_APPROVED_SOURCE, char_result)
    verify_layer_contract(
        "voya",
        manifest,
        char_dir,
        VOYA_REQUIRED_LAYERS,
        VOYA_OBSOLETE_LAYERS,
        VOYA_ALLOWED_FILES,
        require_effects=False,
    )
    for layer in manifest["layers"]:
        image = load_rgba(char_dir / layer["file"])
        expected = layer["size"]
        if image.width != expected["width"] or image.height != expected["height"]:
            fail(f"{layer['id']} dimension mismatch")
        char_result["layers"][layer["id"]] = {
            "group": layer.get("group"),
            "size": expected,
            "offset": layer["sceneOffset"],
            "motion": layer.get("motion"),
            "pivot": layer.get("pivot"),
            "transformOrigin": layer.get("transformOrigin"),
        }
    verify_source_rgba("voya", VOYA_APPROVED_SOURCE, manifest, char_dir, char_result)
    require_motion = "voya-cup-group" not in (manifest.get("motionBlocked") or [])
    verify_serving_semantics("voya", manifest, char_dir, char_result, "voya-cup-group", require_motion)
    verify_browser_evidence("voya", manifest, char_result, "voya-cup-group")
    results["characters"]["voya"] = char_result


def verify_character_mama(results: dict) -> None:
    char_dir = SCENES / "mama"
    manifest_path = char_dir / "manifest.json"
    if not manifest_path.is_file():
        fail("Missing Mama manifest")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("character") != "mama":
        fail("Mama manifest character field invalid")
    char_result: dict = {"layers": {}, "jointOverlaps": manifest.get("jointOverlaps", [])}
    verify_approved_source_basics("mama", MAMA_APPROVED_SOURCE, char_result)
    verify_layer_contract(
        "mama",
        manifest,
        char_dir,
        MAMA_REQUIRED_LAYERS,
        MAMA_OBSOLETE_LAYERS,
        MAMA_ALLOWED_FILES,
        require_effects=False,
    )
    for layer in manifest["layers"]:
        image = load_rgba(char_dir / layer["file"])
        expected = layer["size"]
        if image.width != expected["width"] or image.height != expected["height"]:
            fail(f"{layer['id']} dimension mismatch")
        char_result["layers"][layer["id"]] = {
            "group": layer.get("group"),
            "size": expected,
            "offset": layer["sceneOffset"],
            "motion": layer.get("motion"),
            "pivot": layer.get("pivot"),
            "transformOrigin": layer.get("transformOrigin"),
        }
    verify_source_rgba("mama", MAMA_APPROVED_SOURCE, manifest, char_dir, char_result)
    require_motion = "mama-serving-group" not in (manifest.get("motionBlocked") or [])
    verify_serving_semantics("mama", manifest, char_dir, char_result, "mama-serving-group", require_motion)
    verify_browser_evidence("mama", manifest, char_result, "mama-serving-group")
    results["characters"]["mama"] = char_result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify VOYA Phase 2 outputs")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--character", choices=VALID_CHARACTERS, help="Verify only the named character")
    group.add_argument("--all", action="store_true", help="Verify papa, mama, voya, and house")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    scope = "all" if args.all else args.character
    results = {
        "phaseStartCommit": PHASE_START,
        "characters": {},
        "productionUntouched": True,
        "passed": False,
        "scope": scope,
        "baselinePath": str(BASELINE_PATH.relative_to(ROOT)).replace("\\", "/"),
    }
    try:
        check_no_temp_artifacts()
        git_unchanged([ROOT / path for path in PRODUCTION_FILES])
        for rel in [
            "docs/phase2/PHASE_2_LAYER_PREP.md",
            "docs/phase2/prepare-layers.py",
            "docs/phase2/verify-phase2.py",
            "docs/phase2/reassembly-preview.html",
            "docs/phase2/capture-evidence.mjs",
        ]:
            path = ROOT / rel
            if path.is_file():
                check_encoding(path)

        if scope == "papa":
            # After Mama/Voya gates complete, protect siblings via approved baselines.
            if MAMA_APPROVED_BASELINE_PATH.is_file() and VOYA_APPROVED_BASELINE_PATH.is_file():
                verify_baseline_snapshot(MAMA_APPROVED_BASELINE_PATH, "mama")
                verify_baseline_snapshot(VOYA_APPROVED_BASELINE_PATH, "voya")
            else:
                baseline = load_persisted_baseline()
                verify_protected_baseline(baseline)
            verify_character_papa(results)
        elif scope == "mama":
            verify_baseline_snapshot(PAPA_APPROVED_BASELINE_PATH, "papa")
            if VOYA_APPROVED_BASELINE_PATH.is_file():
                verify_baseline_snapshot(VOYA_APPROVED_BASELINE_PATH, "voya")
            else:
                baseline = load_persisted_baseline()
                current_voya = snapshot_character_dir(SCENES / "voya")
                if current_voya != baseline["voya"]:
                    fail("voya: outputs diverge from persisted Papa-gate baseline during Mama gate")
            verify_character_mama(results)
        elif scope == "voya":
            verify_baseline_snapshot(PAPA_APPROVED_BASELINE_PATH, "papa")
            verify_baseline_snapshot(MAMA_APPROVED_BASELINE_PATH, "mama")
            verify_character_voya(results)
        else:
            verify_character_papa(results)
            verify_character_mama(results)
            verify_character_voya(results)
            verify_house(results)
            verify_baseline_snapshot(PAPA_APPROVED_BASELINE_PATH, "papa")
            verify_baseline_snapshot(MAMA_APPROVED_BASELINE_PATH, "mama")
            verify_baseline_snapshot(VOYA_APPROVED_BASELINE_PATH, "voya")
            # Registry paths must resolve for all prepared assets.
            registry = json.loads((SCENES / "registry.json").read_text(encoding="utf-8"))
            for name in ("papa", "mama", "voya", "house"):
                key = "staticAssets" if name == "house" else "manifests"
                rel = registry.get(key if name == "house" else "manifests", {}).get(name)
                if name == "house":
                    rel = registry.get("staticAssets", {}).get("house") or registry.get("manifests", {}).get("house")
                if not rel:
                    fail(f"registry missing path for {name}")
                if not (ROOT / rel).is_file():
                    fail(f"registry path missing on disk for {name}: {rel}")

        results["passed"] = True
        print(json.dumps(results, indent=2))
        return 0
    except VerificationError as error:
        results["error"] = str(error)
        print(json.dumps(results, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
