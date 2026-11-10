#!/usr/bin/env python3
"""Train YOLOv8 Nano on the converted Freiburg Mobility Aids dataset."""
import argparse
import shutil
from pathlib import Path


def choose_device() -> str:
    import torch
    if torch.cuda.is_available(): return "0"
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available(): return "mps"
    return "cpu"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data/freiburg_yolo/data.yaml"))
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--weights-dir", type=Path, default=Path("weights"))
    args = parser.parse_args()
    if not args.data.is_file(): raise SystemExit(f"Dataset config not found: {args.data}. Run dataset_prep.py first.")
    from ultralytics import YOLO
    device = choose_device()
    print(f"Loading yolov8n.pt; selected device: {device}")
    model = YOLO("yolov8n.pt")
    result = model.train(data=str(args.data.resolve()), epochs=args.epochs, imgsz=args.imgsz,
                         device=device, project="runs/mobility_aids", name="yolov8n", exist_ok=True)
    best = Path(result.save_dir) / "weights" / "best.pt"
    if not best.is_file(): raise SystemExit(f"Training finished but best weights were not found at {best}")
    args.weights_dir.mkdir(parents=True, exist_ok=True)
    destination = args.weights_dir / "best.pt"
    shutil.copy2(best, destination)
    print(f"Best weights saved to {destination.resolve()}")


if __name__ == "__main__": main()
