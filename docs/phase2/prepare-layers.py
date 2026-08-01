#!/usr/bin/env python3
"""VOYA Phase 2 — per-character single-source layered 2D asset preparation."""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
OUT_ROOT = ROOT / "assets" / "scenes"
EVIDENCE_ROOT = Path(__file__).resolve().parent / "evidence"
MAX_SERVING_BODY_DUPLICATE = 0.25
MAX_NECK_OVERLAP_RATIO = 0.12
JOINT_EXPAND_PX = 8
PAPA_APPROVED_SOURCE = "assets/images/temporary/papa-temp-clean.png"
MAMA_APPROVED_SOURCE = "assets/images/temporary/mama-temp-clean.png"
VOYA_APPROVED_SOURCE = "assets/images/temporary/voya-temp-clean.png"
# Prefer widest clean range; selector still tries 3→2→1.
PAPA_SERVING_ROTATE_CANDIDATES = ((-3, 3), (-2, 2), (-1, 1))
PAPA_SERVING_TORSO_HOLE_LIMIT = 80
MAMA_SERVING_ROTATE_CANDIDATES = ((-3, 3), (-2, 2), (-1, 1))
MAMA_SERVING_TORSO_HOLE_LIMIT = 100
PAPA_OBSOLETE_LAYERS = (
    "papa-arm-left.png",
    "papa-plate.png",
    "papa-ingredients.png",
)
MAMA_OBSOLETE_LAYERS = (
    "mama-arm-right.png",
    "mama-pizza.png",
)
VOYA_OBSOLETE_LAYERS = (
    "voya-arm-right.png",
    "voya-cup.png",
)
VOYA_CUP_ROTATE_CANDIDATES = ((-3, 3), (-2, 2), (-1, 1))
# Tight joint hole budget — light triangles / sleeve gaps fail visual review well below 100.
VOYA_CUP_TORSO_HOLE_LIMIT = 24
# Localized shirt underpaint under the cup joint may overlap the mover more than Papa's plate.
VOYA_MAX_CUP_BODY_DUPLICATE = 0.45
# Pivot near the sleeve attachment (top of the cup-group arm), not mid-cup.
VOYA_CUP_PIVOT = (0.28, 0.10)
PAPA_EFFECT_SPECS = (
    # name, relative crop on trimmed canvas (rx0, ry0, rx1, ry1)
    ("effect-grilled-protein", (0.42, 0.34, 0.72, 0.46)),
    ("effect-broccoli", (0.28, 0.36, 0.46, 0.48)),
    ("effect-grains", (0.40, 0.42, 0.62, 0.52)),
    ("effect-salad", (0.58, 0.38, 0.78, 0.50)),
    ("effect-tomato", (0.62, 0.42, 0.74, 0.50)),
)
MAX_ARM_BODY_DUPLICATE = MAX_SERVING_BODY_DUPLICATE
VALID_CHARACTERS = ("papa", "mama", "voya")


@dataclass
class LayerDef:
    id: str
    z_index: int
    group: str
    seeds: list[tuple[int, int]]
    zone: tuple[int, int, int, int]
    max_radius: int
    pivot: tuple[float, float] | None = None
    motion: dict | None = None
    joint_zone: tuple[int, int, int, int] | None = None


@dataclass
class CharacterDef:
    name: str
    source_path: str
    bbox: tuple[int, int, int, int] | None
    pad: int
    bg_mode: str
    source_note: str
    layers: list[LayerDef]
    source_mode: str = "marketing_crop"
    text_exclude: list[tuple[float, float, float, float]] = field(default_factory=list)
    motion_blocked: list[str] = field(default_factory=list)


def load_rgba(path: Path) -> Image.Image:
    return Image.open(path).convert("RGBA")


def ink_from_bg(image: Image.Image, mode: str) -> Image.Image:
    px = image.convert("RGB")
    w, h = px.size
    data = px.load()
    mask = Image.new("L", (w, h), 0)
    mp = mask.load()
    if mode == "light_ink_on_dark":
        for y in range(h):
            for x in range(w):
                r, g, b = data[x, y]
                if (r + g + b) / 3 > 185:
                    mp[x, y] = 255
    elif mode == "dark_ink_on_color":
        corners = [data[0, 0], data[w - 1, 0], data[0, h - 1], data[w - 1, h - 1]]
        bg = tuple(sum(c[i] for c in corners) / 4 for i in range(3))
        for y in range(h):
            for x in range(w):
                r, g, b = data[x, y]
                dist = math.sqrt((r - bg[0]) ** 2 + (g - bg[1]) ** 2 + (b - bg[2]) ** 2)
                if dist > 55 or (r + g + b) / 3 < 95:
                    mp[x, y] = 255
    else:
        raise ValueError(f"Unknown bg_mode {mode}")
    return mask


def trim_alpha(image: Image.Image) -> tuple[Image.Image, tuple[int, int, int, int]]:
    alpha = image.split()[3]
    bbox = alpha.getbbox()
    if not bbox:
        raise ValueError("Layer has no visible pixels")
    return image.crop(bbox), bbox


def mask_pixel_count(mask: Image.Image) -> int:
    return sum(1 for value in mask.get_flattened_data() if value)


def zone_mask(size: tuple[int, int], zone: tuple[int, int, int, int]) -> Image.Image:
    w, h = size
    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    draw.rectangle(zone, fill=255)
    return mask


def snap_seed_to_ink(ink: Image.Image, seed: tuple[int, int], zone: tuple[int, int, int, int], radius: int = 160) -> tuple[int, int]:
    w, h = ink.size
    sx, sy = seed
    ink_px = ink.load()
    allowed = zone_mask((w, h), zone).load()
    if 0 <= sx < w and 0 <= sy < h and ink_px[sx, sy] > 0 and allowed[sx, sy] > 0:
        return sx, sy
    best = None
    best_dist = radius * radius + 1
    x0, y0, x1, y1 = zone
    for y in range(max(0, y0), min(h, y1 + 1)):
        for x in range(max(0, x0), min(w, x1 + 1)):
            if ink_px[x, y] == 0 or allowed[x, y] == 0:
                continue
            dist = (x - sx) ** 2 + (y - sy) ** 2
            if dist < best_dist:
                best_dist = dist
                best = (x, y)
    if best is None:
        raise ValueError(f"No ink found near seed {seed} in zone {zone}")
    return best


def layer_from_zone(ink: Image.Image, zone: tuple[int, int, int, int], assigned: Image.Image) -> Image.Image:
    zone_ink = overlap_mask(ink, zone_mask(ink.size, zone))
    return subtract_mask(zone_ink, assigned)


def dilate(mask: Image.Image, radius: int) -> Image.Image:
    if radius <= 0:
        return mask.copy()
    w, h = mask.size
    src = mask.load()
    out = Image.new("L", (w, h), 0)
    dst = out.load()
    for y in range(h):
        for x in range(w):
            if src[x, y] == 0:
                continue
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    if dx * dx + dy * dy > radius * radius:
                        continue
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < w and 0 <= ny < h:
                        dst[nx, ny] = 255
    return out


def erode(mask: Image.Image, radius: int) -> Image.Image:
    if radius <= 0:
        return mask.copy()
    w, h = mask.size
    src = mask.load()
    out = Image.new("L", (w, h), 0)
    dst = out.load()
    for y in range(h):
        for x in range(w):
            if src[x, y] == 0:
                continue
            keep = True
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    if dx * dx + dy * dy > radius * radius:
                        continue
                    nx, ny = x + dx, y + dy
                    if not (0 <= nx < w and 0 <= ny < h) or src[nx, ny] == 0:
                        keep = False
                        break
                if not keep:
                    break
            if keep:
                dst[x, y] = 255
    return out


def mask_to_rgba(base: Image.Image, mask: Image.Image) -> Image.Image:
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    layer.paste(base, (0, 0), mask)
    return layer


def subtract_mask(base: Image.Image, remove: Image.Image) -> Image.Image:
    w, h = base.size
    out = Image.new("L", (w, h), 0)
    bp = base.load()
    rp = remove.load()
    op = out.load()
    for y in range(h):
        for x in range(w):
            if bp[x, y] > 0 and rp[x, y] == 0:
                op[x, y] = 255
    return out


def overlap_pixels(a: Image.Image, b: Image.Image) -> int:
    ap = a.load()
    bp = b.load()
    count = 0
    w, h = a.size
    for y in range(h):
        for x in range(w):
            if ap[x, y] > 0 and bp[x, y] > 0:
                count += 1
    return count


def overlap_mask(a: Image.Image, b: Image.Image) -> Image.Image:
    w, h = a.size
    out = Image.new("L", (w, h), 0)
    ap = a.load()
    bp = b.load()
    op = out.load()
    for y in range(h):
        for x in range(w):
            if ap[x, y] > 0 and bp[x, y] > 0:
                op[x, y] = 255
    return out


def merge_masks(a: Image.Image, b: Image.Image) -> Image.Image:
    return Image.frombytes(
        "L",
        a.size,
        bytes(max(x, y) for x, y in zip(a.get_flattened_data(), b.get_flattened_data())),
    )


def connected_components(mask: Image.Image, min_size: int = 200) -> list[tuple[int, tuple[int, int, int, int]]]:
    w, h = mask.size
    src = mask.load()
    seen = [[False] * w for _ in range(h)]
    comps: list[tuple[int, tuple[int, int, int, int]]] = []
    for y in range(h):
        for x in range(w):
            if not src[x, y] or seen[y][x]:
                continue
            queue: deque[tuple[int, int]] = deque([(x, y)])
            seen[y][x] = True
            pts: list[tuple[int, int]] = []
            while queue:
                cx, cy = queue.popleft()
                pts.append((cx, cy))
                for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                    if 0 <= nx < w and 0 <= ny < h and src[nx, ny] and not seen[ny][nx]:
                        seen[ny][nx] = True
                        queue.append((nx, ny))
            if len(pts) >= min_size:
                xs = [p[0] for p in pts]
                ys = [p[1] for p in pts]
                comps.append((len(pts), (min(xs), min(ys), max(xs), max(ys))))
    comps.sort(reverse=True)
    return comps


def mask_from_component(mask: Image.Image, bbox: tuple[int, int, int, int]) -> Image.Image:
    w, h = mask.size
    src = mask.load()
    x0, y0, x1, y1 = bbox
    seen = [[False] * w for _ in range(h)]
    out = Image.new("L", (w, h), 0)
    dst = out.load()
    for y in range(h):
        for x in range(w):
            if not src[x, y]:
                continue
            queue: deque[tuple[int, int]] = deque([(x, y)])
            seen[y][x] = True
            pts: list[tuple[int, int]] = []
            while queue:
                cx, cy = queue.popleft()
                pts.append((cx, cy))
                for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                    if 0 <= nx < w and 0 <= ny < h and src[nx, ny] and not seen[ny][nx]:
                        seen[ny][nx] = True
                        queue.append((nx, ny))
            if pts:
                xs = [p[0] for p in pts]
                ys = [p[1] for p in pts]
                if min(xs) == x0 and min(ys) == y0 and max(xs) == x1 and max(ys) == y1:
                    for px, py in pts:
                        dst[px, py] = 255
                    break
    return out


def isolate_character_ink(
    ink: Image.Image,
    exclude_zones: list[tuple[int, int, int, int]],
) -> Image.Image:
    w, h = ink.size
    filtered = ink.copy()
    for zone in exclude_zones:
        filtered = subtract_mask(filtered, zone_mask((w, h), zone))
    return filtered


def zone_centroid_seed(ink: Image.Image, zone: tuple[int, int, int, int]) -> tuple[int, int]:
    x0, y0, x1, y1 = zone
    return snap_seed_to_ink(ink, ((x0 + x1) // 2, (y0 + y1) // 2), zone)


def duplicate_ratio(inner: Image.Image, outer: Image.Image) -> float:
    inner_px = overlap_pixels(inner, inner)
    if inner_px == 0:
        return 0.0
    return overlap_pixels(inner, outer) / inner_px


def make_shadow(size: tuple[int, int], foot_x: int, foot_y: int) -> Image.Image:
    w, h = size
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    draw.ellipse((foot_x - 120, foot_y - 18, foot_x + 120, foot_y + 18), fill=(0, 0, 0, 55))
    return layer


def extract_transparent(source: Image.Image) -> tuple[Image.Image, Image.Image, tuple[int, int, int, int]]:
    rgba = source.convert("RGBA")
    alpha = rgba.split()[3]
    bbox = alpha.getbbox()
    if not bbox:
        raise ValueError("Transparent source has no visible pixels")
    crop = rgba.crop(bbox)
    ink = alpha.crop(bbox).point(lambda value: 255 if value > 16 else 0)
    return crop, ink, bbox


def rel_canvas_zone(size: tuple[int, int], rx0: float, ry0: float, rx1: float, ry1: float) -> tuple[int, int, int, int]:
    w, h = size
    return (
        int(w * rx0),
        int(h * ry0),
        min(w - 1, int(w * rx1)),
        min(h - 1, int(h * ry1)),
    )


def extract_character(source: Image.Image, bbox: tuple[int, int, int, int], pad: int, bg_mode: str) -> tuple[Image.Image, Image.Image, tuple[int, int]]:
    x0, y0, x1, y1 = bbox
    cx0, cy0 = x0 - pad, y0 - pad
    cx1, cy1 = x1 + pad, y1 + pad
    crop = source.crop((cx0, cy0, cx1 + 1, cy1 + 1))
    ink = ink_from_bg(crop, bg_mode)
    rgba = crop.copy()
    rgba.putalpha(ink)
    return rgba, ink, (cx0, cy0)


def local_seed(global_seed: tuple[int, int], origin: tuple[int, int]) -> tuple[int, int]:
    return global_seed[0] - origin[0], global_seed[1] - origin[1]


def local_zone(global_bbox: tuple[int, int, int, int], origin: tuple[int, int], canvas_size: tuple[int, int]) -> tuple[int, int, int, int]:
    x0 = max(0, global_bbox[0] - origin[0])
    y0 = max(0, global_bbox[1] - origin[1])
    x1 = min(canvas_size[0] - 1, global_bbox[2] - origin[0])
    y1 = min(canvas_size[1] - 1, global_bbox[3] - origin[1])
    return (x0, y0, x1, y1)


def motion_gap_mask(
    mover_mask: Image.Image,
    pivot: tuple[float, float],
    angles: Iterable[float],
) -> Image.Image:
    rgba = Image.new("RGBA", mover_mask.size, (0, 0, 0, 0))
    rgba.putalpha(mover_mask)
    gaps = Image.new("L", mover_mask.size, 0)
    for angle in angles:
        rotated = rgba.rotate(angle, resample=Image.Resampling.BICUBIC, center=pivot, expand=False).split()[3]
        gap = subtract_mask(mover_mask, rotated)
        gaps = merge_masks(gaps, gap)
    return gaps


def fill_motion_gaps_from_donor_interior(
    body_rgba: Image.Image,
    body_mask: Image.Image,
    mover_mask: Image.Image,
    donor_rgba: Image.Image,
    pivot: tuple[float, float],
    angles: Iterable[float],
    erode_px: int = 4,
    max_radius: int = 24,
    opaque_limit: Image.Image | None = None,
) -> tuple[Image.Image, Image.Image]:
    """Fill mover gaps using eroded donor interior colors (avoids outline ghosts)."""
    # Keep fills inside eroded mover so antialiased edges still composite identically at neutral.
    gaps = subtract_mask(motion_gap_mask(mover_mask, pivot, angles), body_mask)
    # Erode by 1px only — enough to protect AA edges, still closes visible seams.
    gaps = overlap_mask(gaps, erode(mover_mask, 1))
    if opaque_limit is not None:
        gaps = overlap_mask(gaps, opaque_limit)
    if mask_pixel_count(gaps) == 0:
        return body_rgba, body_mask
    interior = erode(mover_mask, erode_px)
    w, h = body_mask.size
    donor = donor_rgba.load()
    interior_a = interior.load()
    gap_a = gaps.load()
    out = body_rgba.copy()
    out_px = out.load()
    out_mask = body_mask.copy()
    out_m = out_mask.load()
    for y in range(h):
        for x in range(w):
            if not gap_a[x, y]:
                continue
            best = None
            best_d = max_radius * max_radius + 1
            for dy in range(-max_radius, max_radius + 1):
                for dx in range(-max_radius, max_radius + 1):
                    d = dx * dx + dy * dy
                    if d > best_d:
                        continue
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < w and 0 <= ny < h and interior_a[nx, ny]:
                        best = donor[nx, ny]
                        best_d = d
            if best is not None:
                r, g, b, _ = best
                out_px[x, y] = (r, g, b, 255)
                out_m[x, y] = 255
    return out, out_mask


def fill_motion_gaps_with_body_color(
    body_rgba: Image.Image,
    body_mask: Image.Image,
    mover_mask: Image.Image,
    pivot: tuple[float, float],
    angles: Iterable[float],
    max_radius: int = 18,
    opaque_limit: Image.Image | None = None,
) -> tuple[Image.Image, Image.Image]:
    """Fill rotation holes by sampling nearby body colors (not mover source pixels)."""
    gaps = subtract_mask(motion_gap_mask(mover_mask, pivot, angles), body_mask)
    gaps = overlap_mask(gaps, erode(mover_mask, 1))
    if opaque_limit is not None:
        gaps = overlap_mask(gaps, opaque_limit)
    if mask_pixel_count(gaps) == 0:
        return body_rgba, body_mask
    w, h = body_mask.size
    src = body_rgba.load()
    body_a = body_mask.load()
    gap_a = gaps.load()
    out = body_rgba.copy()
    out_px = out.load()
    out_mask = body_mask.copy()
    out_m = out_mask.load()
    for y in range(h):
        for x in range(w):
            if not gap_a[x, y]:
                continue
            best = None
            best_d = max_radius * max_radius + 1
            for dy in range(-max_radius, max_radius + 1):
                for dx in range(-max_radius, max_radius + 1):
                    d = dx * dx + dy * dy
                    if d > best_d or d == 0:
                        continue
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < w and 0 <= ny < h and body_a[nx, ny]:
                        best = src[nx, ny]
                        best_d = d
            if best is not None:
                r, g, b, _ = best
                out_px[x, y] = (r, g, b, 255)
                out_m[x, y] = 255
    return out, out_mask


def luma_mask(base: Image.Image, mask: Image.Image, max_luma: int, min_luma: int = 0) -> Image.Image:
    w, h = base.size
    out = Image.new("L", (w, h), 0)
    src = base.load()
    mp = mask.load()
    dst = out.load()
    for y in range(h):
        for x in range(w):
            if not mp[x, y]:
                continue
            r, g, b, a = src[x, y]
            if a < 16:
                continue
            luma = (r + g + b) / 3
            if min_luma <= luma <= max_luma:
                dst[x, y] = 255
    return out


def split_serving_and_shirt(base: Image.Image, zone_ink: Image.Image) -> tuple[Image.Image, Image.Image]:
    """Mutually exclusive serving vs shirt fills inside the serving zone.

    Serving keeps arms/hands/plate/food and their adjacent outline strokes.
    Shirt fill (thick dark polo) returns to body and is excluded from serving.
    """
    dark = luma_mask(base, zone_ink, max_luma=72)
    content = subtract_mask(zone_ink, dark)  # fur, plate, food
    # Black strokes that hug serving content belong to the serving group.
    serving_outlines = overlap_mask(dark, dilate(content, 3))
    serving = merge_masks(content, serving_outlines)
    shirt_fill = subtract_mask(dark, serving_outlines)
    return serving, shirt_fill


def sample_shirt_color(base: Image.Image, shirt_mask: Image.Image) -> tuple[int, int, int]:
    src = base.load()
    mp = shirt_mask.load()
    w, h = base.size
    rs = gs = bs = count = 0
    for y in range(h):
        for x in range(w):
            if not mp[x, y]:
                continue
            r, g, b, a = src[x, y]
            if a < 200:
                continue
            # Prefer interior shirt fills (very dark, not outline).
            if (r + g + b) / 3 > 55:
                continue
            rs += r
            gs += g
            bs += b
            count += 1
    if count == 0:
        return (18, 18, 18)
    return (rs // count, gs // count, bs // count)


def paint_hidden_shirt_patch(
    body_rgba: Image.Image,
    body_mask: Image.Image,
    serving_mask: Image.Image,
    shirt_sample: tuple[int, int, int],
    patch_zone: tuple[int, int, int, int],
    expand: int = 10,
) -> tuple[Image.Image, Image.Image]:
    """Solid shirt-colored hidden patch behind serving — no outline strokes."""
    zone = zone_mask(body_mask.size, patch_zone)
    # Region covered by serving that should reveal shirt when serving rotates.
    need = overlap_mask(dilate(serving_mask, expand), zone)
    need = subtract_mask(need, serving_mask)
    need = subtract_mask(need, body_mask)
    if mask_pixel_count(need) == 0:
        return body_rgba, body_mask
    out = body_rgba.copy()
    op = out.load()
    nm = need.load()
    bm = body_mask.copy()
    bp = bm.load()
    r, g, b = shirt_sample
    w, h = body_mask.size
    for y in range(h):
        for x in range(w):
            if nm[x, y]:
                op[x, y] = (r, g, b, 255)
                bp[x, y] = 255
    return out, bm


def choose_serving_rotation(
    base: Image.Image,
    body_rgba: Image.Image,
    body_mask: Image.Image,
    serving_mask: Image.Image,
    head_mask: Image.Image,
    pivot: tuple[float, float],
    torso_zone: tuple[int, int, int, int],
    candidates: tuple[tuple[int, int], ...] = PAPA_SERVING_ROTATE_CANDIDATES,
    max_holes: int = PAPA_SERVING_TORSO_HOLE_LIMIT,
) -> tuple[list[int], int]:
    """Pick widest clean non-zero serving rotation by measuring torso holes only."""
    ink = base.split()[3]
    ink_bin = ink.point(lambda value: 255 if value >= 16 else 0)
    torso = zone_mask(body_mask.size, torso_zone)
    # Expected opaque torso coverage at neutral (body+serving+head in torso band).
    neutral_cover = overlap_mask(ink_bin, torso)
    w, h = base.size

    def composite(angle: float) -> Image.Image:
        canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        canvas.alpha_composite(Image.composite(body_rgba, Image.new("RGBA", (w, h), (0, 0, 0, 0)), body_mask))
        canvas.alpha_composite(mask_to_rgba(base, head_mask))
        serving_rgba = mask_to_rgba(base, serving_mask)
        if angle:
            full = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            full.alpha_composite(serving_rgba)
            full = full.rotate(angle, resample=Image.Resampling.BICUBIC, center=pivot, expand=False)
            canvas = Image.alpha_composite(canvas, full)
        else:
            canvas.alpha_composite(serving_rgba)
        return canvas

    best = [candidates[-1][0], candidates[-1][1]]
    best_holes = 10**9
    for lo, hi in candidates:
        holes = 0
        for angle in (lo, hi):
            comp = composite(float(angle))
            covered = overlap_mask(
                comp.split()[3].point(lambda value: 255 if value >= 16 else 0),
                torso,
            )
            missing = subtract_mask(neutral_cover, covered)
            holes = max(holes, mask_pixel_count(missing))
        if holes < best_holes:
            best_holes = holes
            best = [lo, hi]
        if holes <= max_holes:
            return [lo, hi], holes
    return best, best_holes


def export_papa_effects(base: Image.Image, out_dir: Path) -> list[dict]:
    effects_dir = out_dir / "effects"
    effects_dir.mkdir(parents=True, exist_ok=True)
    # Clear previous effect outputs.
    for path in effects_dir.glob("*.png"):
        path.unlink()
    w, h = base.size
    entries: list[dict] = []
    for name, (rx0, ry0, rx1, ry1) in PAPA_EFFECT_SPECS:
        zone = rel_canvas_zone((w, h), rx0, ry0, rx1, ry1)
        crop = base.crop((zone[0], zone[1], zone[2] + 1, zone[3] + 1))
        # Keep only opaque ink; drop empty crops.
        if crop.split()[3].getextrema()[1] < 16:
            continue
        trimmed, bbox = trim_alpha(crop)
        file_name = f"{name}.png"
        trimmed.save(effects_dir / file_name, optimize=True)
        entries.append(
            {
                "id": name,
                "file": f"effects/{file_name}",
                "source": PAPA_APPROVED_SOURCE,
                "cropOnCanvas": {"x0": zone[0], "y0": zone[1], "x1": zone[2], "y1": zone[3]},
                "size": {"width": trimmed.width, "height": trimmed.height},
                "phase4Use": "Papa scene ingredient/food motion accent — not shown in neutral reconstruction",
            }
        )
    return entries


def connected_components(mask: Image.Image) -> list[list[tuple[int, int]]]:
    w, h = mask.size
    mp = mask.load()
    visited = [[False] * w for _ in range(h)]
    comps: list[list[tuple[int, int]]] = []
    for y in range(h):
        for x in range(w):
            if not mp[x, y] or visited[y][x]:
                continue
            stack = [(x, y)]
            visited[y][x] = True
            cells: list[tuple[int, int]] = []
            while stack:
                cx, cy = stack.pop()
                cells.append((cx, cy))
                for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                    if 0 <= nx < w and 0 <= ny < h and mp[nx, ny] and not visited[ny][nx]:
                        visited[ny][nx] = True
                        stack.append((nx, ny))
            comps.append(cells)
    return comps


def split_mama_serving_group(base: Image.Image, zone_ink: Image.Image) -> tuple[Image.Image, Image.Image]:
    """Exclusive Mama serving (arms/hands/pizza) vs dress/collar/apron fills."""
    w, h = base.size
    dark = luma_mask(base, zone_ink, max_luma=72)
    content = subtract_mask(zone_ink, dark)
    src = base.load()
    keep = Image.new("L", (w, h), 0)
    kp = keep.load()
    pizza_anchor: list[tuple[int, int]] = []

    for cells in connected_components(content):
        n = len(cells)
        if n < 40:
            continue
        xs = [c[0] for c in cells]
        ys = [c[1] for c in cells]
        xmin, xmax = min(xs), max(xs)
        ymin, ymax = min(ys), max(ys)
        xc = sum(xs) / n
        yc = sum(ys) / n
        red = green = 0
        for x, y in cells:
            r, g, b, a = src[x, y]
            if a < 200:
                continue
            if r > 140 and g < 120 and b < 110 and r > g + 40:
                red += 1
            if g > r + 12 and g > b + 12 and g > 70:
                green += 1

        is_collar = ymax < int(h * 0.40) and ymin < int(h * 0.36) and n < 8000
        is_cuff = ymin > int(h * 0.30) and ymax < int(h * 0.42) and n < 5000
        is_apron = xmax < int(w * 0.22) and yc > int(h * 0.55) and n < 5000
        near_pizza = abs(yc - h * 0.50) < h * 0.12 and abs(xc - w * 0.55) < w * 0.35

        keep_it = False
        if red > 40 or green > 20:
            keep_it = True
        elif n > 1000 and int(h * 0.40) < yc < int(h * 0.62) and not is_apron:
            keep_it = True
        elif n >= 80 and near_pizza and (red or green or n < 400):
            # Small topping / crust islands around the pizza.
            keep_it = True
        if is_collar or is_cuff or is_apron:
            keep_it = False
        if keep_it:
            for x, y in cells:
                kp[x, y] = 255
            if red or green or (n > 3000 and near_pizza):
                pizza_anchor.extend(cells[:: max(1, n // 40)])

    # Absorb remaining dark tray/pizza interiors that sit inside the serving silhouette.
    serving_shell = dilate(keep, 10)
    dark_px = dark.load()
    shell_px = serving_shell.load()
    for y in range(h):
        for x in range(w):
            if dark_px[x, y] and shell_px[x, y] and not kp[x, y]:
                # Prefer tray/food dark that is not a thick dress fill (wide solid blocks below arms).
                if y < int(h * 0.66):
                    kp[x, y] = 255

    serving_outlines = overlap_mask(dark, dilate(keep, 4))
    serving = merge_masks(keep, serving_outlines)
    dress_fill = subtract_mask(dark, serving)
    return serving, dress_fill


def split_voya_cup_group(base: Image.Image, zone_ink: Image.Image) -> tuple[Image.Image, Image.Image]:
    """Exclusive Voya cup-group (cup + holding hand) vs shirt fill in the cup zone.

    Cup keeps cream hand/cup/forearm plus only outline strokes that hug that cream.
    Thick shirt/sleeve fills stay on the body — never absorbed into the movable group.
    """
    w, h = base.size
    dark = luma_mask(base, zone_ink, max_luma=72)
    content = subtract_mask(zone_ink, dark)
    keep = Image.new("L", (w, h), 0)
    kp = keep.load()
    neck_cut = int(h * 0.36)
    for cells in connected_components(content):
        n = len(cells)
        if n < 40:
            continue
        xs = [c[0] for c in cells]
        ys = [c[1] for c in cells]
        xc = sum(xs) / n
        yc = sum(ys) / n
        ymax = max(ys)
        ymin = min(ys)
        # Cup/hand live on the character's right (viewer's right); backpack/left arm stay out.
        if xc < w * 0.48:
            continue
        if yc < h * 0.38 or yc > h * 0.60:
            continue
        # Reject neck/face/shoulder cream islands above the cup/hand band.
        if ymax < neck_cut or ymin < int(h * 0.32) and ymax < int(h * 0.40):
            continue
        if n < 200 and yc < h * 0.42:
            continue
        for x, y in cells:
            if y >= neck_cut:
                kp[x, y] = 255

    # Thin outline hug only — do not pull thick shirt/sleeve fills into the cup group.
    cup_outlines = overlap_mask(dark, dilate(keep, 2))
    cup = merge_masks(keep, cup_outlines)
    cp = cup.load()
    # Hard strip any residual cup pixels above the neck cut.
    for y in range(0, neck_cut):
        for x in range(w):
            cp[x, y] = 0
    shirt_fill = subtract_mask(dark, cup)
    return cup, shirt_fill


def apply_local_joint_patch(
    body_mask: Image.Image,
    arm_mask: Image.Image,
    ink: Image.Image,
    joint_zone: tuple[int, int, int, int],
    expand: int = JOINT_EXPAND_PX,
) -> Image.Image:
    zone = zone_mask(body_mask.size, joint_zone)
    arm_joint = overlap_mask(arm_mask, zone)
    if mask_pixel_count(arm_joint) == 0:
        return body_mask
    patch = overlap_mask(dilate(arm_joint, expand), ink)
    patch = subtract_mask(patch, arm_mask)
    patch = overlap_mask(patch, zone)
    return merge_masks(body_mask, patch)


def mask_motion_envelope(
    layer_mask: Image.Image,
    pivot: tuple[float, float],
    angles: Iterable[float],
) -> Image.Image:
    envelope = Image.new("L", layer_mask.size, 0)
    rgba = Image.new("RGBA", layer_mask.size, (0, 0, 0, 0))
    rgba.putalpha(layer_mask)
    for angle in angles:
        rotated = rgba.rotate(angle, resample=Image.Resampling.BICUBIC, center=pivot, expand=False)
        envelope = merge_masks(envelope, rotated.split()[3])
    return envelope


def apply_motion_underpaint(
    body_mask: Image.Image,
    mover_mask: Image.Image,
    ink: Image.Image,
    pivot: tuple[float, float],
    angles: Iterable[float],
    limit_zone: tuple[int, int, int, int] | None = None,
    transfer_from_mover: bool = False,
    erode_px: int = 0,
) -> tuple[Image.Image, Image.Image]:
    """Add motion-gap underpaint to body; optionally remove transferred pixels from mover."""
    rgba = Image.new("RGBA", mover_mask.size, (0, 0, 0, 0))
    rgba.putalpha(mover_mask)
    neutral = overlap_mask(mover_mask, ink)
    gaps = Image.new("L", mover_mask.size, 0)
    for angle in angles:
        rotated = rgba.rotate(angle, resample=Image.Resampling.BICUBIC, center=pivot, expand=False).split()[3]
        gap = subtract_mask(neutral, overlap_mask(rotated, ink))
        gaps = merge_masks(gaps, gap)
    if limit_zone:
        gaps = overlap_mask(gaps, zone_mask(body_mask.size, limit_zone))
    patch = subtract_mask(gaps, body_mask)
    if mask_pixel_count(patch):
        patch = dilate(patch, 4 if not transfer_from_mover else 2)
        patch = overlap_mask(patch, ink)
        patch = subtract_mask(patch, body_mask)
        if erode_px:
            patch = erode(patch, erode_px)
    updated_body = merge_masks(body_mask, patch)
    updated_mover = subtract_mask(mover_mask, patch) if transfer_from_mover else mover_mask
    return updated_body, updated_mover


def scene_pivot(layer_mask: Image.Image, relative: tuple[float, float] | None) -> tuple[float, float]:
    bbox = layer_mask.getbbox()
    if not bbox or not relative:
        w, h = layer_mask.size
        return (w * 0.5, h * 0.5)
    x0, y0, x1, y1 = bbox
    width = x1 - x0
    height = y1 - y0
    return (x0 + relative[0] * width, y0 + relative[1] * height)


def compute_pivot(trimmed: Image.Image, layer_def: LayerDef) -> tuple[float, float, str]:
    if layer_def.pivot:
        px = layer_def.pivot[0] * trimmed.width
        py = layer_def.pivot[1] * trimmed.height
        return px, py, f"{layer_def.pivot[0] * 100:.1f}% {layer_def.pivot[1] * 100:.1f}%"

    alpha = trimmed.split()[3].load()
    w, h = trimmed.size
    xs: list[int] = []
    ys: list[int] = []
    for y in range(h):
        for x in range(w):
            if alpha[x, y] > 0:
                xs.append(x)
                ys.append(y)
    if not xs:
        return 0.0, 0.0, "0% 0%"
    if layer_def.group == "head":
        py = max(ys)
        px = sum(xs) / len(xs)
    elif layer_def.group == "arm":
        py = min(ys) + (max(ys) - min(ys)) * 0.15
        px = min(xs) if "left" in layer_def.id else max(xs)
    elif layer_def.group == "serving":
        py = min(ys) + (max(ys) - min(ys)) * 0.12
        px = min(xs) + (max(xs) - min(xs)) * 0.24
    elif layer_def.group == "prop":
        px = sum(xs) / len(xs)
        py = max(ys)
    else:
        px = sum(xs) / len(xs)
        py = max(ys)
    return px, py, f"{(px / max(w, 1)) * 100:.1f}% {(py / max(h, 1)) * 100:.1f}%"


ASSIGN_GROUP_ORDER = {"head": 0, "serving": 1, "arm": 1, "prop": 2, "body": 3, "shadow": 4}

PAPA_BBOX = (1020, 360, 1920, 1430)
MAMA_BBOX = (1380, 450, 1980, 1520)
VOYA_BBOX = (710, 1540, 1130, 2095)


def rel_point(bbox: tuple[int, int, int, int], rx: float, ry: float) -> tuple[int, int]:
    x0, y0, x1, y1 = bbox
    return (int(x0 + (x1 - x0) * rx), int(y0 + (y1 - y0) * ry))


def rel_rect(bbox: tuple[int, int, int, int], rx0: float, ry0: float, rx1: float, ry1: float) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = bbox
    return (
        int(x0 + (x1 - x0) * rx0),
        int(y0 + (y1 - y0) * ry0),
        int(x0 + (x1 - x0) * rx1),
        int(y0 + (y1 - y0) * ry1),
    )


CHARACTERS: list[CharacterDef] = [
    CharacterDef(
        name="papa",
        source_path=PAPA_APPROVED_SOURCE,
        bbox=None,
        pad=0,
        bg_mode="transparent_alpha",
        source_mode="transparent_alpha",
        source_note="Clean transparent Papa from papa-temp-clean.png (healthy plate pose, single character).",
        text_exclude=[],
        layers=[],
    ),
    CharacterDef(
        name="mama",
        source_path=MAMA_APPROVED_SOURCE,
        bbox=None,
        pad=0,
        bg_mode="transparent_alpha",
        source_mode="transparent_alpha",
        source_note="Clean transparent Mama from mama-temp-clean.png (pizza tray pose, single character).",
        text_exclude=[],
        layers=[],
    ),
    CharacterDef(
        name="voya",
        source_path=VOYA_APPROVED_SOURCE,
        bbox=None,
        pad=0,
        bg_mode="transparent_alpha",
        source_mode="transparent_alpha",
        source_note="Clean transparent Voya from voya-temp-clean.png (cup + backpack + skateboard, single character).",
        text_exclude=[],
        layers=[],
    ),
]


def build_papa_clean(source: Image.Image, spec: CharacterDef) -> dict:
    out_dir = OUT_ROOT / "papa"
    out_dir.mkdir(parents=True, exist_ok=True)
    for obsolete in PAPA_OBSOLETE_LAYERS:
        path = out_dir / obsolete
        if path.exists():
            path.unlink()

    base, ink, source_bbox = extract_transparent(source)
    w, h = base.size
    sx0, sy0, sx1, sy1 = source_bbox

    head_zone = rel_canvas_zone((w, h), 0.06, 0.0, 0.94, 0.30)
    serving_zone = rel_canvas_zone((w, h), 0.0, 0.22, 1.0, 0.52)
    serving_joint = rel_canvas_zone((w, h), 0.16, 0.24, 0.58, 0.36)
    head_joint = rel_canvas_zone((w, h), 0.28, 0.24, 0.72, 0.34)
    shirt_patch_zone = rel_canvas_zone((w, h), 0.10, 0.28, 0.90, 0.58)
    # Approximate shirt/pants boundary on trimmed canvas for dual-color underpaint.
    waist_y = int(h * 0.50)

    head_mask = layer_from_zone(ink, head_zone, Image.new("L", (w, h), 0))
    if mask_pixel_count(head_mask) < 80:
        raise RuntimeError("papa: head mask too small")

    serving_zone_ink = layer_from_zone(ink, serving_zone, head_mask)
    serving_mask, shirt_fill = split_serving_and_shirt(base, serving_zone_ink)
    if mask_pixel_count(serving_mask) < 20000:
        raise RuntimeError("papa: serving-group too small after exclusive shirt split")

    # Strict exclusive body: no visible serving pixels/outlines remain on body.
    body_mask = subtract_mask(ink, merge_masks(head_mask, serving_mask))
    body_mask = merge_masks(body_mask, shirt_fill)
    # Tiny shoulder continuity only (localized).
    body_mask = apply_local_joint_patch(body_mask, serving_mask, ink, serving_joint, expand=JOINT_EXPAND_PX)
    # Neck continuity under static head.
    body_mask = apply_local_joint_patch(body_mask, head_mask, ink, head_joint, expand=6)

    body_rgba = mask_to_rgba(base, body_mask)
    shirt_color = sample_shirt_color(base, shirt_fill if mask_pixel_count(shirt_fill) else body_mask)
    pants_mask = luma_mask(base, body_mask, max_luma=245, min_luma=140)
    pants_color = sample_shirt_color(base, pants_mask) if mask_pixel_count(pants_mask) else (232, 224, 208)
    # Prefer cream pants sample (higher luma) when available.
    if mask_pixel_count(pants_mask):
        src = base.load()
        mp = pants_mask.load()
        rs = gs = bs = count = 0
        for y in range(h):
            for x in range(w):
                if not mp[x, y]:
                    continue
                r, g, b, a = src[x, y]
                if a < 200:
                    continue
                rs += r
                gs += g
                bs += b
                count += 1
        if count:
            pants_color = (rs // count, gs // count, bs // count)

    # Hidden fill only under fully-opaque serving interiors (preserves neutral RGBA).
    serving_pivot_pre = scene_pivot(serving_mask, (0.26, 0.12))
    serving_alpha = mask_to_rgba(base, serving_mask).split()[3]
    opaque_serving = serving_alpha.point(lambda value: 255 if value >= 255 else 0)
    for angle in (-3, -2, -1, 1, 2, 3):
        gaps = motion_gap_mask(serving_mask, serving_pivot_pre, (angle,))
        gaps = overlap_mask(gaps, zone_mask((w, h), shirt_patch_zone))
        gaps = overlap_mask(gaps, opaque_serving)
        gaps = subtract_mask(gaps, body_mask)
        if mask_pixel_count(gaps) == 0:
            continue
        gp = gaps.load()
        op = body_rgba.load()
        bp = body_mask.load()
        for y in range(h):
            for x in range(w):
                if not gp[x, y]:
                    continue
                r, g, b = shirt_color if y < waist_y else pants_color
                op[x, y] = (r, g, b, 255)
                bp[x, y] = 255

    # Ensure exclusivity after patch paint: serving pixels win visually; body may only
    # hold hidden shirt underpaint beneath serving (overlap allowed only in patch/joint).
    ratio = duplicate_ratio(serving_mask, body_mask)
    if ratio > MAX_SERVING_BODY_DUPLICATE:
        # Strip non-patch overlap: keep body/serving overlap only inside patch zone or joint.
        allow = merge_masks(zone_mask((w, h), shirt_patch_zone), zone_mask((w, h), serving_joint))
        illegal = subtract_mask(overlap_mask(serving_mask, body_mask), allow)
        body_mask = subtract_mask(body_mask, illegal)
        body_rgba = Image.composite(body_rgba, Image.new("RGBA", (w, h), (0, 0, 0, 0)), body_mask)
        ratio = duplicate_ratio(serving_mask, body_mask)
        if ratio > MAX_SERVING_BODY_DUPLICATE:
            raise RuntimeError(f"papa: serving/body overlap still too high ({ratio:.2%})")

    serving_pivot = scene_pivot(serving_mask, (0.26, 0.12))
    rotate_range, hole_count = choose_serving_rotation(
        base,
        body_rgba,
        body_mask,
        serving_mask,
        head_mask,
        serving_pivot,
        shirt_patch_zone,
    )
    if hole_count > 800:
        raise RuntimeError(
            "BLOCKED - approved Papa raster cannot satisfy the Phase 2 arm/plate motion requirement "
            f"(best range {rotate_range} still leaves {hole_count} torso motion holes)"
        )

    layer_specs = [
        LayerDef("papa-body", 10, "body", [], (0, 0, w - 1, h - 1), 0, (0.50, 0.90), None),
        # Head stays static — independent rotation exposed outlines/hidden geometry.
        LayerDef("papa-head", 20, "head", [], head_zone, 0, None, None, joint_zone=head_joint),
        LayerDef(
            "papa-serving-group",
            30,
            "serving",
            [],
            serving_zone,
            0,
            (0.26, 0.12),
            {"rotate": rotate_range},
            joint_zone=serving_joint,
        ),
    ]
    layer_masks = {
        "papa-body": body_mask,
        "papa-head": head_mask,
        "papa-serving-group": serving_mask,
    }

    foot_x = w // 2
    foot_y = h - 24
    shadow = make_shadow((w, h), foot_x, foot_y)
    shadow_trim, shadow_bbox = trim_alpha(shadow)
    shadow_trim.save(out_dir / "papa-shadow.png", optimize=True)

    overlaps: list[dict] = []
    manifest_layers: list[dict] = []
    joint_overlaps: list[dict] = [
        {
            "serving": "papa-serving-group",
            "body": "papa-body",
            "pixels": overlap_pixels(serving_mask, body_mask),
            "percentOfServing": round(ratio * 100, 2),
        }
    ]

    for layer_def in sorted(layer_specs, key=lambda item: item.z_index):
        mask = layer_masks[layer_def.id]
        if layer_def.id == "papa-body":
            rgba = Image.composite(body_rgba, Image.new("RGBA", body_rgba.size, (0, 0, 0, 0)), body_mask)
        else:
            rgba = mask_to_rgba(base, mask)
        trimmed, bbox = trim_alpha(rgba)
        pivot_x, pivot_y, transform_origin = compute_pivot(trimmed, layer_def)
        entry = {
            "id": layer_def.id,
            "file": f"{layer_def.id}.png",
            "zIndex": layer_def.z_index,
            "sceneOffset": {"x": bbox[0], "y": bbox[1]},
            "size": {"width": trimmed.width, "height": trimmed.height},
            "pivot": {"x": round(pivot_x, 2), "y": round(pivot_y, 2)},
            "transformOrigin": transform_origin,
            "group": layer_def.group,
            "motion": layer_def.motion,
        }
        if layer_def.joint_zone:
            jz = layer_def.joint_zone
            entry["jointZone"] = {"x0": jz[0], "y0": jz[1], "x1": jz[2], "y1": jz[3]}
        trimmed.save(out_dir / entry["file"], optimize=True)
        manifest_layers.append(entry)
        for other in layer_specs:
            if other.z_index >= layer_def.z_index or other.id == layer_def.id:
                continue
            shared = overlap_pixels(mask, layer_masks[other.id])
            if shared:
                overlaps.append({"a": layer_def.id, "b": other.id, "pixels": shared})

    manifest_layers.insert(
        0,
        {
            "id": "papa-shadow",
            "file": "papa-shadow.png",
            "zIndex": 0,
            "sceneOffset": {"x": shadow_bbox[0], "y": shadow_bbox[1]},
            "size": {"width": shadow_trim.width, "height": shadow_trim.height},
            "pivot": {"x": shadow_trim.width / 2, "y": shadow_trim.height / 2},
            "transformOrigin": "50% 50%",
            "group": "shadow",
            "generated": True,
        },
    )

    effects = export_papa_effects(base, out_dir)
    base.copy().save(out_dir / "papa-mobile-fallback.png", optimize=True)
    base.copy().save(out_dir / "papa-source-reference.png", optimize=True)

    manifest = {
        "character": "papa",
        "phase": 2,
        "source": {
            "path": spec.source_path,
            "bbox": {"x0": sx0, "y0": sy0, "x1": sx1, "y1": sy1},
            "sourceDimensions": {"width": source.width, "height": source.height},
            "note": spec.source_note,
        },
        "sceneCanvas": {
            "width": w,
            "height": h,
            "originInSource": {"x": sx0, "y": sy0},
            "aspectRatio": round(w / h, 4),
        },
        "jointExpandPx": JOINT_EXPAND_PX,
        "layerOverlaps": overlaps,
        "jointOverlaps": joint_overlaps,
        "layers": sorted(manifest_layers, key=lambda item: item["zIndex"]),
        "mobileFallback": "papa-mobile-fallback.png",
        "sourceReference": "papa-source-reference.png",
        "motionBlocked": ["papa-head"],
        "servingMotionSelection": {
            "candidates": [list(item) for item in PAPA_SERVING_ROTATE_CANDIDATES],
            "selected": rotate_range,
            "endpointHolePixels": hole_count,
        },
        "layerContract": {
            "required": ["papa-shadow", "papa-body", "papa-head", "papa-serving-group"],
            "servingGroupContains": ["both arms", "both hands", "plate", "all food"],
            "headMotion": "static — independent rotation exposed outlines/hidden geometry",
        },
        "effectAssets": effects,
        "evidence": {
            "browserRoot": "docs/phase2/evidence/papa/browser",
            "fallback": "docs/phase2/evidence/papa/browser/fallback_desktop.png",
        },
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Papa serving motion selected: {rotate_range} (endpoint holes={hole_count})")
    print(f"Papa effect assets: {len(effects)}")
    return manifest


def build_mama_clean(source: Image.Image, spec: CharacterDef) -> dict:
    out_dir = OUT_ROOT / "mama"
    out_dir.mkdir(parents=True, exist_ok=True)
    for obsolete in MAMA_OBSOLETE_LAYERS:
        path = out_dir / obsolete
        if path.exists():
            path.unlink()

    base, ink, source_bbox = extract_transparent(source)
    w, h = base.size
    sx0, sy0, sx1, sy1 = source_bbox

    head_zone = rel_canvas_zone((w, h), 0.08, 0.0, 0.92, 0.30)
    serving_zone = rel_canvas_zone((w, h), 0.0, 0.24, 1.0, 0.72)
    serving_joint = rel_canvas_zone((w, h), 0.18, 0.30, 0.82, 0.44)
    head_joint = rel_canvas_zone((w, h), 0.30, 0.24, 0.70, 0.34)
    dress_patch_zone = rel_canvas_zone((w, h), 0.10, 0.30, 0.90, 0.62)

    head_mask = layer_from_zone(ink, head_zone, Image.new("L", (w, h), 0))
    if mask_pixel_count(head_mask) < 80:
        raise RuntimeError("mama: head mask too small")

    serving_zone_ink = layer_from_zone(ink, serving_zone, head_mask)
    serving_mask, dress_fill = split_mama_serving_group(base, serving_zone_ink)
    if mask_pixel_count(serving_mask) < 15000:
        raise RuntimeError("mama: serving-group too small after exclusive split")

    body_mask = subtract_mask(ink, merge_masks(head_mask, serving_mask))
    body_mask = merge_masks(body_mask, dress_fill)
    body_mask = apply_local_joint_patch(body_mask, serving_mask, ink, serving_joint, expand=JOINT_EXPAND_PX)
    body_mask = apply_local_joint_patch(body_mask, head_mask, ink, head_joint, expand=6)

    body_rgba = mask_to_rgba(base, body_mask)
    dress_color = sample_shirt_color(base, dress_fill if mask_pixel_count(dress_fill) else body_mask)

    serving_pivot_pre = scene_pivot(serving_mask, (0.50, 0.16))
    serving_alpha = mask_to_rgba(base, serving_mask).split()[3]
    # Only paint under fully opaque serving interiors so neutral AA edges stay source-identical.
    opaque_serving = serving_alpha.point(lambda value: 255 if value >= 255 else 0)
    opaque_in_patch = overlap_mask(opaque_serving, zone_mask((w, h), dress_patch_zone))
    for angle in (-3, -2, -1, 1, 2, 3):
        gaps = motion_gap_mask(serving_mask, serving_pivot_pre, (angle,))
        gaps = overlap_mask(gaps, opaque_in_patch)
        gaps = subtract_mask(gaps, body_mask)
        if mask_pixel_count(gaps) == 0:
            continue
        gp = gaps.load()
        op = body_rgba.load()
        bp = body_mask.load()
        src_body = body_rgba.load()
        for y in range(h):
            for x in range(w):
                if not gp[x, y]:
                    continue
                # Prefer a nearby already-present body color; fall back to dress fill.
                best = None
                best_d = 29 * 29
                for dy in range(-28, 29):
                    for dx in range(-28, 29):
                        d = dx * dx + dy * dy
                        if d == 0 or d > best_d:
                            continue
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < w and 0 <= ny < h and bp[nx, ny] and not gp[nx, ny]:
                            best = src_body[nx, ny]
                            best_d = d
                if best is not None:
                    op[x, y] = (best[0], best[1], best[2], 255)
                else:
                    op[x, y] = (*dress_color, 255)
                bp[x, y] = 255

    ratio = duplicate_ratio(serving_mask, body_mask)
    if ratio > MAX_SERVING_BODY_DUPLICATE:
        allow = merge_masks(zone_mask((w, h), dress_patch_zone), zone_mask((w, h), serving_joint))
        illegal = subtract_mask(overlap_mask(serving_mask, body_mask), allow)
        body_mask = subtract_mask(body_mask, illegal)
        body_rgba = Image.composite(body_rgba, Image.new("RGBA", (w, h), (0, 0, 0, 0)), body_mask)
        ratio = duplicate_ratio(serving_mask, body_mask)
        if ratio > MAX_SERVING_BODY_DUPLICATE:
            raise RuntimeError(f"mama: serving/body overlap still too high ({ratio:.2%})")

    serving_pivot = scene_pivot(serving_mask, (0.50, 0.16))
    rotate_range, hole_count = choose_serving_rotation(
        base,
        body_rgba,
        body_mask,
        serving_mask,
        head_mask,
        serving_pivot,
        dress_patch_zone,
        candidates=MAMA_SERVING_ROTATE_CANDIDATES,
        max_holes=MAMA_SERVING_TORSO_HOLE_LIMIT,
    )
    serving_motion: dict | None = {"rotate": rotate_range}
    motion_blocked = ["mama-head"]
    serving_motion_note = f"selected {rotate_range} (endpoint holes={hole_count})"
    if hole_count > MAMA_SERVING_TORSO_HOLE_LIMIT:
        # Keep semantic serving group for whole-character transforms; block internal motion.
        serving_motion = None
        motion_blocked.append("mama-serving-group")
        serving_motion_note = (
            f"blocked - no clean non-zero serving rotation "
            f"(best {rotate_range} left {hole_count} torso holes)"
        )
        print(f"Mama serving motion BLOCKED: {serving_motion_note}")
    else:
        print(f"Mama serving motion selected: {serving_motion_note}")

    layer_specs = [
        LayerDef("mama-body", 10, "body", [], (0, 0, w - 1, h - 1), 0, (0.50, 0.90), None),
        LayerDef("mama-head", 20, "head", [], head_zone, 0, None, None, joint_zone=head_joint),
        LayerDef(
            "mama-serving-group",
            30,
            "serving",
            [],
            serving_zone,
            0,
            (0.50, 0.16),
            serving_motion,
            joint_zone=serving_joint,
        ),
    ]
    layer_masks = {
        "mama-body": body_mask,
        "mama-head": head_mask,
        "mama-serving-group": serving_mask,
    }

    foot_x = w // 2
    foot_y = h - 24
    shadow = make_shadow((w, h), foot_x, foot_y)
    shadow_trim, shadow_bbox = trim_alpha(shadow)
    shadow_trim.save(out_dir / "mama-shadow.png", optimize=True)

    overlaps: list[dict] = []
    manifest_layers: list[dict] = []
    joint_overlaps: list[dict] = [
        {
            "serving": "mama-serving-group",
            "body": "mama-body",
            "pixels": overlap_pixels(serving_mask, body_mask),
            "percentOfServing": round(ratio * 100, 2),
        }
    ]

    for layer_def in sorted(layer_specs, key=lambda item: item.z_index):
        mask = layer_masks[layer_def.id]
        if layer_def.id == "mama-body":
            rgba = Image.composite(body_rgba, Image.new("RGBA", body_rgba.size, (0, 0, 0, 0)), body_mask)
        else:
            rgba = mask_to_rgba(base, mask)
        trimmed, bbox = trim_alpha(rgba)
        pivot_x, pivot_y, transform_origin = compute_pivot(trimmed, layer_def)
        entry = {
            "id": layer_def.id,
            "file": f"{layer_def.id}.png",
            "zIndex": layer_def.z_index,
            "sceneOffset": {"x": bbox[0], "y": bbox[1]},
            "size": {"width": trimmed.width, "height": trimmed.height},
            "pivot": {"x": round(pivot_x, 2), "y": round(pivot_y, 2)},
            "transformOrigin": transform_origin,
            "group": layer_def.group,
            "motion": layer_def.motion,
        }
        if layer_def.joint_zone:
            jz = layer_def.joint_zone
            entry["jointZone"] = {"x0": jz[0], "y0": jz[1], "x1": jz[2], "y1": jz[3]}
        trimmed.save(out_dir / entry["file"], optimize=True)
        manifest_layers.append(entry)
        for other in layer_specs:
            if other.z_index >= layer_def.z_index or other.id == layer_def.id:
                continue
            shared = overlap_pixels(mask, layer_masks[other.id])
            if shared:
                overlaps.append({"a": layer_def.id, "b": other.id, "pixels": shared})

    manifest_layers.insert(
        0,
        {
            "id": "mama-shadow",
            "file": "mama-shadow.png",
            "zIndex": 0,
            "sceneOffset": {"x": shadow_bbox[0], "y": shadow_bbox[1]},
            "size": {"width": shadow_trim.width, "height": shadow_trim.height},
            "pivot": {"x": shadow_trim.width / 2, "y": shadow_trim.height / 2},
            "transformOrigin": "50% 50%",
            "group": "shadow",
            "generated": True,
        },
    )

    base.copy().save(out_dir / "mama-mobile-fallback.png", optimize=True)
    base.copy().save(out_dir / "mama-source-reference.png", optimize=True)

    manifest = {
        "character": "mama",
        "phase": 2,
        "source": {
            "path": spec.source_path,
            "bbox": {"x0": sx0, "y0": sy0, "x1": sx1, "y1": sy1},
            "sourceDimensions": {"width": source.width, "height": source.height},
            "note": spec.source_note,
        },
        "sceneCanvas": {
            "width": w,
            "height": h,
            "originInSource": {"x": sx0, "y": sy0},
            "aspectRatio": round(w / h, 4),
        },
        "jointExpandPx": JOINT_EXPAND_PX,
        "layerOverlaps": overlaps,
        "jointOverlaps": joint_overlaps,
        "layers": sorted(manifest_layers, key=lambda item: item["zIndex"]),
        "mobileFallback": "mama-mobile-fallback.png",
        "sourceReference": "mama-source-reference.png",
        "motionBlocked": motion_blocked,
        "servingMotionSelection": {
            "candidates": [list(item) for item in MAMA_SERVING_ROTATE_CANDIDATES],
            "selected": rotate_range if serving_motion else None,
            "endpointHolePixels": hole_count,
            "note": serving_motion_note,
        },
        "layerContract": {
            "required": ["mama-shadow", "mama-body", "mama-head", "mama-serving-group"],
            "servingGroupContains": ["arms", "hands", "pizza"],
            "headMotion": "static — independent rotation exposed outlines/hidden geometry",
        },
        "evidence": {
            "browserRoot": "docs/phase2/evidence/mama/browser",
            "fallback": "docs/phase2/evidence/mama/browser/fallback_desktop.png",
        },
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def build_voya_clean(source: Image.Image, spec: CharacterDef) -> dict:
    out_dir = OUT_ROOT / "voya"
    out_dir.mkdir(parents=True, exist_ok=True)
    for obsolete in VOYA_OBSOLETE_LAYERS:
        path = out_dir / obsolete
        if path.exists():
            path.unlink()

    base, ink, source_bbox = extract_transparent(source)
    w, h = base.size
    sx0, sy0, sx1, sy1 = source_bbox

    head_zone = rel_canvas_zone((w, h), 0.20, 0.0, 0.85, 0.34)
    cup_zone = rel_canvas_zone((w, h), 0.45, 0.34, 1.0, 0.62)
    # Tight sleeve/chest joint — localized only around the holding-arm attachment.
    cup_joint = rel_canvas_zone((w, h), 0.62, 0.34, 0.88, 0.48)
    head_joint = rel_canvas_zone((w, h), 0.35, 0.22, 0.70, 0.34)
    shirt_patch_zone = cup_joint

    head_mask = layer_from_zone(ink, head_zone, Image.new("L", (w, h), 0))
    if mask_pixel_count(head_mask) < 80:
        raise RuntimeError("voya: head mask too small")

    cup_zone_ink = layer_from_zone(ink, cup_zone, head_mask)
    cup_mask, shirt_fill = split_voya_cup_group(base, cup_zone_ink)
    if mask_pixel_count(cup_mask) < 8000:
        raise RuntimeError("voya: cup-group too small after exclusive split")

    # Exclusive visible body: no cup-hand pixels remain. Shirt fills stay on body.
    body_mask = subtract_mask(ink, merge_masks(head_mask, cup_mask))
    body_mask = merge_masks(body_mask, shirt_fill)
    # Neck continuity only — do NOT reintroduce cup outlines via ink joint transfer.
    body_mask = apply_local_joint_patch(body_mask, head_mask, ink, head_joint, expand=6)

    body_rgba = mask_to_rgba(base, body_mask)
    shirt_color = sample_shirt_color(base, shirt_fill if mask_pixel_count(shirt_fill) else body_mask)

    cup_pivot_pre = scene_pivot(cup_mask, VOYA_CUP_PIVOT)
    cup_alpha = mask_to_rgba(base, cup_mask).split()[3]
    opaque_cup = cup_alpha.point(lambda value: 255 if value >= 255 else 0)
    joint_zone_mask = zone_mask((w, h), cup_joint)

    # Motion-gap shirt fill under opaque cup interiors inside the joint only.
    # Plus a tiny stump (dilate 4) so the sleeve opening never flashes a hole at ±1..±3.
    stump = overlap_mask(dilate(cup_mask, 4), joint_zone_mask)
    stump = overlap_mask(stump, opaque_cup)
    stump = subtract_mask(stump, body_mask)
    gap_union = Image.new("L", (w, h), 0)
    for angle in (-3, -2, -1, 1, 2, 3):
        gaps = motion_gap_mask(cup_mask, cup_pivot_pre, (angle,))
        gaps = overlap_mask(gaps, opaque_cup)
        gaps = overlap_mask(gaps, joint_zone_mask)
        gap_union = merge_masks(gap_union, gaps)
    gap_union = subtract_mask(gap_union, body_mask)
    patch = merge_masks(stump, gap_union)
    if mask_pixel_count(patch):
        gp = patch.load()
        op = body_rgba.load()
        bp = body_mask.load()
        src_body = body_rgba.load()
        for y in range(h):
            for x in range(w):
                if not gp[x, y]:
                    continue
                best = None
                best_d = 18 * 18
                for dy in range(-18, 19):
                    for dx in range(-18, 19):
                        d = dx * dx + dy * dy
                        if d == 0 or d > best_d:
                            continue
                        nx, ny = x + dx, y + dy
                        if not (0 <= nx < w and 0 <= ny < h and bp[nx, ny] and not gp[nx, ny]):
                            continue
                        r, g, b, a = src_body[nx, ny]
                        if a < 200:
                            continue
                        # Prefer existing dark shirt fills; reject cream/light samples.
                        if (r + g + b) / 3 > 70:
                            continue
                        best = (r, g, b)
                        best_d = d
                if best is None:
                    best = shirt_color
                op[x, y] = (*best, 255)
                bp[x, y] = 255

    ratio = duplicate_ratio(cup_mask, body_mask)
    if ratio > VOYA_MAX_CUP_BODY_DUPLICATE:
        allow = joint_zone_mask
        illegal = subtract_mask(overlap_mask(cup_mask, body_mask), allow)
        body_mask = subtract_mask(body_mask, illegal)
        body_rgba = Image.composite(body_rgba, Image.new("RGBA", (w, h), (0, 0, 0, 0)), body_mask)
        ratio = duplicate_ratio(cup_mask, body_mask)
        if ratio > VOYA_MAX_CUP_BODY_DUPLICATE:
            raise RuntimeError(f"voya: cup/body overlap still too high ({ratio:.2%})")

    cup_pivot = scene_pivot(cup_mask, VOYA_CUP_PIVOT)
    rotate_range, hole_count = choose_serving_rotation(
        base,
        body_rgba,
        body_mask,
        cup_mask,
        head_mask,
        cup_pivot,
        cup_joint,
        candidates=VOYA_CUP_ROTATE_CANDIDATES,
        max_holes=VOYA_CUP_TORSO_HOLE_LIMIT,
    )
    cup_motion: dict | None = {"rotate": rotate_range}
    motion_blocked = ["voya-head"]
    cup_motion_note = f"selected {rotate_range} (endpoint holes={hole_count})"
    if hole_count > VOYA_CUP_TORSO_HOLE_LIMIT:
        cup_motion = None
        motion_blocked.append("voya-cup-group")
        cup_motion_note = (
            f"blocked - no clean non-zero cup rotation "
            f"(best {rotate_range} left {hole_count} torso holes)"
        )
        print(f"Voya cup motion BLOCKED: {cup_motion_note}")
    else:
        print(f"Voya cup motion selected: {cup_motion_note}")

    layer_specs = [
        LayerDef("voya-body", 10, "body", [], (0, 0, w - 1, h - 1), 0, (0.50, 0.88), None),
        LayerDef("voya-head", 20, "head", [], head_zone, 0, None, None, joint_zone=head_joint),
        LayerDef(
            "voya-cup-group",
            30,
            "serving",
            [],
            cup_zone,
            0,
            VOYA_CUP_PIVOT,
            cup_motion,
            joint_zone=cup_joint,
        ),
    ]
    layer_masks = {
        "voya-body": body_mask,
        "voya-head": head_mask,
        "voya-cup-group": cup_mask,
    }

    foot_x = w // 2
    foot_y = h - 24
    shadow = make_shadow((w, h), foot_x, foot_y)
    shadow_trim, shadow_bbox = trim_alpha(shadow)
    shadow_trim.save(out_dir / "voya-shadow.png", optimize=True)

    overlaps: list[dict] = []
    manifest_layers: list[dict] = []
    joint_overlaps: list[dict] = [
        {
            "serving": "voya-cup-group",
            "body": "voya-body",
            "pixels": overlap_pixels(cup_mask, body_mask),
            "percentOfServing": round(ratio * 100, 2),
        }
    ]

    for layer_def in sorted(layer_specs, key=lambda item: item.z_index):
        mask = layer_masks[layer_def.id]
        if layer_def.id == "voya-body":
            rgba = Image.composite(body_rgba, Image.new("RGBA", body_rgba.size, (0, 0, 0, 0)), body_mask)
        else:
            rgba = mask_to_rgba(base, mask)
        trimmed, bbox = trim_alpha(rgba)
        pivot_x, pivot_y, transform_origin = compute_pivot(trimmed, layer_def)
        entry = {
            "id": layer_def.id,
            "file": f"{layer_def.id}.png",
            "zIndex": layer_def.z_index,
            "sceneOffset": {"x": bbox[0], "y": bbox[1]},
            "size": {"width": trimmed.width, "height": trimmed.height},
            "pivot": {"x": round(pivot_x, 2), "y": round(pivot_y, 2)},
            "transformOrigin": transform_origin,
            "group": layer_def.group,
            "motion": layer_def.motion,
        }
        if layer_def.joint_zone:
            jz = layer_def.joint_zone
            entry["jointZone"] = {"x0": jz[0], "y0": jz[1], "x1": jz[2], "y1": jz[3]}
        trimmed.save(out_dir / entry["file"], optimize=True)
        manifest_layers.append(entry)
        for other in layer_specs:
            if other.z_index >= layer_def.z_index or other.id == layer_def.id:
                continue
            shared = overlap_pixels(mask, layer_masks[other.id])
            if shared:
                overlaps.append({"a": layer_def.id, "b": other.id, "pixels": shared})

    manifest_layers.insert(
        0,
        {
            "id": "voya-shadow",
            "file": "voya-shadow.png",
            "zIndex": 0,
            "sceneOffset": {"x": shadow_bbox[0], "y": shadow_bbox[1]},
            "size": {"width": shadow_trim.width, "height": shadow_trim.height},
            "pivot": {"x": shadow_trim.width / 2, "y": shadow_trim.height / 2},
            "transformOrigin": "50% 50%",
            "group": "shadow",
            "generated": True,
        },
    )

    base.copy().save(out_dir / "voya-mobile-fallback.png", optimize=True)
    base.copy().save(out_dir / "voya-source-reference.png", optimize=True)

    manifest = {
        "character": "voya",
        "phase": 2,
        "source": {
            "path": spec.source_path,
            "bbox": {"x0": sx0, "y0": sy0, "x1": sx1, "y1": sy1},
            "sourceDimensions": {"width": source.width, "height": source.height},
            "note": spec.source_note,
        },
        "sceneCanvas": {
            "width": w,
            "height": h,
            "originInSource": {"x": sx0, "y": sy0},
            "aspectRatio": round(w / h, 4),
        },
        "jointExpandPx": JOINT_EXPAND_PX,
        "layerOverlaps": overlaps,
        "jointOverlaps": joint_overlaps,
        "layers": sorted(manifest_layers, key=lambda item: item["zIndex"]),
        "mobileFallback": "voya-mobile-fallback.png",
        "sourceReference": "voya-source-reference.png",
        "motionBlocked": motion_blocked,
        "cupMotionSelection": {
            "candidates": [list(item) for item in VOYA_CUP_ROTATE_CANDIDATES],
            "selected": rotate_range if cup_motion else None,
            "endpointHolePixels": hole_count,
            "note": cup_motion_note,
        },
        "layerContract": {
            "required": ["voya-shadow", "voya-body", "voya-head", "voya-cup-group"],
            "cupGroupContains": ["cup", "holding hand"],
            "bodyContains": ["backpack", "skateboard", "free arm"],
            "headMotion": "static - independent rotation exposed outlines/hidden geometry",
        },
        "evidence": {
            "browserRoot": "docs/phase2/evidence/voya/browser",
            "fallback": "docs/phase2/evidence/voya/browser/fallback_desktop.png",
        },
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def build_character(source: Image.Image, spec: CharacterDef) -> dict:
    if spec.name == "papa" and spec.source_mode == "transparent_alpha":
        return build_papa_clean(source, spec)
    if spec.name == "mama" and spec.source_mode == "transparent_alpha":
        return build_mama_clean(source, spec)
    if spec.name == "voya" and spec.source_mode == "transparent_alpha":
        return build_voya_clean(source, spec)
    if spec.source_mode == "transparent_alpha":
        raise ValueError(f"{spec.name}: transparent_alpha builder not implemented yet")

    if spec.bbox is None:
        raise ValueError(f"{spec.name}: marketing crop requires bbox")
    out_dir = OUT_ROOT / spec.name
    out_dir.mkdir(parents=True, exist_ok=True)

    base, ink, origin = extract_character(source, spec.bbox, spec.pad, spec.bg_mode)
    w, h = base.size
    exclude_zones = [
        local_zone(rel_rect(spec.bbox, *rect), origin, (w, h)) for rect in spec.text_exclude
    ]
    ink = isolate_character_ink(ink, exclude_zones)
    base.putalpha(ink)
    assigned = Image.new("L", (w, h), 0)
    layer_masks: dict[str, Image.Image] = {}

    ordered = sorted(
        [layer for layer in spec.layers if layer.group not in {"body", "shadow"}],
        key=lambda item: (ASSIGN_GROUP_ORDER.get(item.group, 99), -item.z_index),
    )
    for layer_def in ordered:
        zone = local_zone(layer_def.zone, origin, (w, h))
        mask = layer_from_zone(ink, zone, assigned)
        mask = subtract_mask(mask, assigned)
        min_px = 8 if layer_def.group == "arm" else 25
        if mask_pixel_count(mask) < min_px:
            raise RuntimeError(f"{spec.name}:{layer_def.id} mask too small ({mask_pixel_count(mask)} px)")
        layer_masks[layer_def.id] = mask
        assigned = merge_masks(assigned, mask)

    body_def = next(layer for layer in spec.layers if layer.group == "body")
    prop_masks = [layer_masks[layer.id] for layer in spec.layers if layer.group == "prop"]
    body_mask = subtract_mask(ink, assigned)

    for layer_def in spec.layers:
        if layer_def.group != "arm" or not layer_def.joint_zone:
            continue
        zone = local_zone(layer_def.joint_zone, origin, (w, h))
        body_mask = apply_local_joint_patch(body_mask, layer_masks[layer_def.id], ink, zone)

    for head_def in [layer for layer in spec.layers if layer.group == "head" and layer.joint_zone]:
        zone = local_zone(head_def.joint_zone, origin, (w, h))
        head_mask = layer_masks[head_def.id]
        neck_patch = overlap_mask(subtract_mask(overlap_mask(dilate(head_mask, 8), ink), head_mask), zone_mask((w, h), zone))
        body_mask = merge_masks(body_mask, neck_patch)

    for prop_mask in prop_masks:
        body_mask = subtract_mask(body_mask, prop_mask)

    layer_masks[body_def.id] = body_mask

    for layer_def in spec.layers:
        if layer_def.group != "arm":
            continue
        ratio = duplicate_ratio(layer_masks[layer_def.id], layer_masks[body_def.id])
        if ratio > MAX_ARM_BODY_DUPLICATE:
            raise RuntimeError(f"{spec.name}: arm {layer_def.id} duplicated in body ({ratio:.2%})")

    foot_x = w // 2
    foot_y = h - 24
    shadow = make_shadow((w, h), foot_x, foot_y)
    shadow_trim, shadow_bbox = trim_alpha(shadow)
    shadow_trim.save(out_dir / f"{spec.name}-shadow.png", optimize=True)

    overlaps: list[dict] = []
    manifest_layers: list[dict] = []
    joint_overlaps: list[dict] = []

    for layer_def in sorted(spec.layers, key=lambda item: item.z_index):
        mask = layer_masks[layer_def.id]
        rgba = mask_to_rgba(base, mask)
        trimmed, bbox = trim_alpha(rgba)
        pivot_x, pivot_y, transform_origin = compute_pivot(trimmed, layer_def)
        entry = {
            "id": layer_def.id,
            "file": f"{layer_def.id}.png",
            "zIndex": layer_def.z_index,
            "sceneOffset": {"x": bbox[0], "y": bbox[1]},
            "size": {"width": trimmed.width, "height": trimmed.height},
            "pivot": {"x": round(pivot_x, 2), "y": round(pivot_y, 2)},
            "transformOrigin": transform_origin,
            "group": layer_def.group,
            "motion": layer_def.motion,
        }
        if layer_def.joint_zone:
            jz = local_zone(layer_def.joint_zone, origin, (w, h))
            entry["jointZone"] = {"x0": jz[0], "y0": jz[1], "x1": jz[2], "y1": jz[3]}
        trimmed.save(out_dir / entry["file"], optimize=True)
        manifest_layers.append(entry)

        for other in spec.layers:
            if other.z_index >= layer_def.z_index or other.id == layer_def.id:
                continue
            shared = overlap_pixels(mask, layer_masks[other.id])
            if shared:
                overlaps.append({"a": layer_def.id, "b": other.id, "pixels": shared})

    for layer_def in spec.layers:
        if layer_def.group == "arm":
            arm = layer_masks[layer_def.id]
            body = layer_masks[body_def.id]
            shared = overlap_pixels(arm, body)
            arm_px = mask_pixel_count(arm)
            if arm_px:
                joint_overlaps.append(
                    {
                        "arm": layer_def.id,
                        "body": body_def.id,
                        "pixels": shared,
                        "percentOfArm": round(shared / arm_px * 100, 2),
                    }
                )

    for layer_def in spec.layers:
        if layer_def.group != "prop":
            continue
        for other in spec.layers:
            if other.group not in {"arm", "body"}:
                continue
            ratio = duplicate_ratio(layer_masks[layer_def.id], layer_masks[other.id])
            if ratio > 0.01:
                raise RuntimeError(f"{spec.name}: prop {layer_def.id} duplicated in {other.id} ({ratio:.2%})")

    manifest_layers.insert(
        0,
        {
            "id": f"{spec.name}-shadow",
            "file": f"{spec.name}-shadow.png",
            "zIndex": 0,
            "sceneOffset": {"x": shadow_bbox[0], "y": shadow_bbox[1]},
            "size": {"width": shadow_trim.width, "height": shadow_trim.height},
            "pivot": {"x": shadow_trim.width / 2, "y": shadow_trim.height / 2},
            "transformOrigin": "50% 50%",
            "group": "shadow",
            "generated": True,
        },
    )

    fallback = base.copy()
    fallback.save(out_dir / f"{spec.name}-mobile-fallback.png", optimize=True)
    base.copy().save(out_dir / f"{spec.name}-source-reference.png", optimize=True)

    manifest = {
        "character": spec.name,
        "phase": 2,
        "source": {
            "path": spec.source_path,
            "bbox": {"x0": spec.bbox[0], "y0": spec.bbox[1], "x1": spec.bbox[2], "y1": spec.bbox[3]},
            "note": spec.source_note,
        },
        "sceneCanvas": {
            "width": w,
            "height": h,
            "originInSource": {"x": origin[0], "y": origin[1]},
            "aspectRatio": round(w / h, 4),
        },
        "jointExpandPx": JOINT_EXPAND_PX,
        "layerOverlaps": overlaps,
        "jointOverlaps": joint_overlaps,
        "layers": sorted(manifest_layers, key=lambda item: item["zIndex"]),
        "mobileFallback": f"{spec.name}-mobile-fallback.png",
        "sourceReference": f"{spec.name}-source-reference.png",
        "motionBlocked": spec.motion_blocked,
        "evidence": {
            "browserRoot": f"docs/phase2/evidence/{spec.name}/browser",
            "fallback": f"docs/phase2/evidence/{spec.name}/fallback.png",
        },
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def write_registry_entry(manifest: dict) -> None:
    """Update only the named character's registry path; leave Mama/Voya entries untouched."""
    registry_path = OUT_ROOT / "registry.json"
    if registry_path.is_file():
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
    else:
        registry = {
            "phase": 2,
            "generatedBy": "docs/phase2/prepare-layers.py",
            "phaseStartCommit": "17bef48",
            "characters": list(VALID_CHARACTERS),
            "manifests": {},
        }
    name = manifest["character"]
    manifests = registry.setdefault("manifests", {})
    # Preserve existing Mama/Voya paths exactly; only rewrite this character.
    manifests[name] = f"assets/scenes/{name}/manifest.json"
    if "characters" not in registry:
        registry["characters"] = list(VALID_CHARACTERS)
    registry["generatedBy"] = "docs/phase2/prepare-layers.py"
    registry["phaseStartCommit"] = "17bef48"
    registry_path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")


def write_registry(manifests: list[dict]) -> None:
    registry = {
        "phase": 2,
        "generatedBy": "docs/phase2/prepare-layers.py",
        "phaseStartCommit": "17bef48",
        "characters": [item["character"] for item in manifests],
        "manifests": {item["character"]: f"assets/scenes/{item['character']}/manifest.json" for item in manifests},
    }
    (OUT_ROOT / "registry.json").write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare VOYA Phase 2 character layers")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--character",
        choices=VALID_CHARACTERS,
        help="Prepare only the named character (required for Papa gate)",
    )
    group.add_argument(
        "--all",
        action="store_true",
        help="Explicit full regeneration of papa, mama, and voya",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.all:
        targets = list(VALID_CHARACTERS)
    else:
        targets = [args.character]
    manifests: list[dict] = []
    for name in targets:
        spec = next(item for item in CHARACTERS if item.name == name)
        source = load_rgba(ROOT / spec.source_path)
        manifests.append(build_character(source, spec))
    if args.all:
        write_registry(manifests)
    else:
        write_registry_entry(manifests[0])
    print(f"Prepared {len(manifests)} character layer set(s): {', '.join(targets)}")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, ValueError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
    except SystemExit:
        raise
