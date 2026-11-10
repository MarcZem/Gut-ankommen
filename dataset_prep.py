#!/usr/bin/env python3
"""Download and convert the Freiburg Mobility Aids RGB dataset for YOLOv8.

The legacy Freiburg site has changed over time. Pass direct archive URLs with
--images-url and --annotations-url (or FREIBURG_IMAGES_URL / FREIBURG_ANNOTATIONS_URL).
"""
from __future__ import annotations

import argparse
import os
import random
import re
import shutil
import tarfile
import urllib.request
from urllib.parse import urlparse
import zipfile
from pathlib import Path

import yaml
from tqdm import tqdm

CLASSES = ["pedestrian", "person in wheelchair", "pedestrian pushing a person in a wheelchair",
           "person using crutches", "person using a walking frame"]
ALIASES = {
    "pedestrian": 0, "person": 0, "person in wheelchair": 1, "wheelchair": 1,
    "pedestrian pushing a person in a wheelchair": 2, "pushing wheelchair": 2,
    "person using crutches": 3, "crutches": 3, "person using a walking frame": 4,
    "walking frame": 4, "walker": 4,
}
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".bmp"}
OFFICIAL_IMAGES_URL = "http://mobility-aids.informatik.uni-freiburg.de/dataset/Images_RGB.zip"
OFFICIAL_ANNOTATIONS_URL = "http://mobility-aids.informatik.uni-freiburg.de/dataset/Annotations_RGB.zip"


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "mobility-aids-yolo/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response, dest.open("wb") as out:
        total = int(response.headers.get("Content-Length", 0))
        with tqdm(total=total or None, unit="B", unit_scale=True, desc=dest.name) as bar:
            while chunk := response.read(1024 * 1024):
                out.write(chunk)
                bar.update(len(chunk))


def safe_extract(archive: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    root = destination.resolve()
    def safe(name: str) -> Path:
        target = (destination / name).resolve()
        if target != root and root not in target.parents:
            raise ValueError(f"Unsafe archive path: {name}")
        return target
    if zipfile.is_zipfile(archive):
        with zipfile.ZipFile(archive) as zf:
            for item in zf.infolist(): safe(item.filename)
            zf.extractall(destination)
    elif tarfile.is_tarfile(archive):
        with tarfile.open(archive) as tf:
            for item in tf.getmembers(): safe(item.name)
            tf.extractall(destination, filter="data")
    else:
        raise ValueError(f"Unsupported archive (expected zip or tar): {archive}")


def norm_key(key: object) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(key).lower())


def find_value(mapping: dict, names: set[str]):
    for key, value in mapping.items():
        if norm_key(key) in names:
            return value
    return None


def parse_annotation(path: Path, image_width: int, image_height: int) -> list[str]:
    try:
        with path.open(encoding="utf-8") as stream:
            doc = yaml.safe_load(stream) or {}
    except Exception as exc:
        raise ValueError(f"Could not parse {path}: {exc}") from exc
    ann = doc.get("annotation", doc) if isinstance(doc, dict) else doc
    objects = ann.get("object", ann.get("objects", [])) if isinstance(ann, dict) else []
    if isinstance(objects, dict): objects = [objects]
    rows = []
    for obj in objects or []:
        if not isinstance(obj, dict): continue
        raw_class = find_value(obj, {"name", "class", "label", "category", "classname", "type", "classid"})
        if isinstance(raw_class, int) or (isinstance(raw_class, str) and raw_class.strip().isdigit()):
            class_id = int(raw_class)
        else:
            label = str(raw_class or "").strip().lower().replace("_", " ").replace("-", " ")
            class_id = ALIASES.get(label)
        if class_id is None or not 0 <= class_id < len(CLASSES):
            continue
        box = find_value(obj, {"bndbox", "bbox", "boundingbox"}) or obj
        if not isinstance(box, dict): continue
        x1 = find_value(box, {"xmin", "x1", "left"}); y1 = find_value(box, {"ymin", "y1", "top"})
        x2 = find_value(box, {"xmax", "x2", "right"}); y2 = find_value(box, {"ymax", "y2", "bottom"})
        if None in (x1, y1, x2, y2): continue
        x1, y1, x2, y2 = map(float, (x1, y1, x2, y2))
        # If values are in [0,1], interpret them as normalized coordinates.
        if max(x1, y1, x2, y2) <= 1:
            x1 *= image_width; x2 *= image_width; y1 *= image_height; y2 *= image_height
        x1, x2 = max(0., min(x1, image_width)), max(0., min(x2, image_width))
        y1, y2 = max(0., min(y1, image_height)), max(0., min(y2, image_height))
        if x2 <= x1 or y2 <= y1: continue
        rows.append(f"{class_id} {(x1+x2)/(2*image_width):.6f} {(y1+y2)/(2*image_height):.6f} {(x2-x1)/image_width:.6f} {(y2-y1)/image_height:.6f}")
    return rows


def image_size(path: Path) -> tuple[int, int]:
    from PIL import Image
    with Image.open(path) as im: return im.size


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--images-url", default=os.getenv("FREIBURG_IMAGES_URL", OFFICIAL_IMAGES_URL))
    parser.add_argument("--annotations-url", default=os.getenv("FREIBURG_ANNOTATIONS_URL", OFFICIAL_ANNOTATIONS_URL))
    parser.add_argument("--raw-dir", type=Path, default=Path("data/freiburg_raw"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/freiburg_yolo"))
    parser.add_argument("--val-ratio", type=float, default=.2)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    if not 0 < args.val_ratio < 1: parser.error("--val-ratio must be between 0 and 1")
    args.raw_dir.mkdir(parents=True, exist_ok=True)
    archives = [(args.images_url, args.raw_dir / "rgb_images_archive"),
                (args.annotations_url, args.raw_dir / "rgb_annotations_archive")]
    for url, stem in archives:
        suffix = Path(urlparse(url).path).suffix or ".zip"
        archive = stem.with_suffix(suffix)
        if not archive.exists(): download(url, archive)
        extracted = stem.with_name(stem.name + "_extracted")
        if not extracted.exists():
            print(f"Extracting {archive} to {extracted} …")
            safe_extract(archive, extracted)
    image_root = args.raw_dir / "rgb_images_archive_extracted"
    anno_root = args.raw_dir / "rgb_annotations_archive_extracted"
    images = sorted(p for p in image_root.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_EXTS)
    annos = {p.stem: p for p in anno_root.rglob("*") if p.is_file() and p.suffix.lower() in {".yml", ".yaml"}}
    if not images: raise SystemExit(f"No RGB images found under {image_root}")
    pairs = [(p, annos[p.stem]) for p in images if p.stem in annos]
    if not pairs: raise SystemExit(f"No matching image/YAML annotation stems found ({len(images)} images, {len(annos)} annotations). Inspect the extracted layout and adapt pairing if filenames differ.")
    random.Random(args.seed).shuffle(pairs)
    cut = max(1, min(len(pairs)-1, round(len(pairs)*(1-args.val_ratio)))) if len(pairs) > 1 else 1
    splits = {"train": pairs[:cut], "val": pairs[cut:]}
    for split, items in splits.items():
        for image, annotation in tqdm(items, desc=f"Converting {split}"):
            image_out = args.output_dir / "images" / split / image.name
            label_out = args.output_dir / "labels" / split / f"{image.stem}.txt"
            image_out.parent.mkdir(parents=True, exist_ok=True); label_out.parent.mkdir(parents=True, exist_ok=True)
            if not image_out.exists(): shutil.copy2(image, image_out)
            width, height = image_size(image)
            label_out.write_text("\n".join(parse_annotation(annotation, width, height)) + "\n", encoding="utf-8")
    config = {"path": str(args.output_dir.resolve()), "train": "images/train", "val": "images/val", "names": {i: name for i, name in enumerate(CLASSES)}}
    (args.output_dir / "data.yaml").write_text(yaml.safe_dump(config, sort_keys=False, allow_unicode=True), encoding="utf-8")
    print(f"Done: {len(splits['train'])} train and {len(splits['val'])} validation images")
    print(f"YOLO dataset config: {args.output_dir / 'data.yaml'}")


if __name__ == "__main__": main()
