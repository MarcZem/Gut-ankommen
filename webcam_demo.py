#!/usr/bin/env python3
"""Run live mobility-aid detection using the laptop's default camera."""
import argparse
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO


def draw_detections(frame: np.ndarray, result) -> np.ndarray:
    """Draw every predicted box in Freiburg-style red with its class and score."""
    annotated = frame.copy()
    if result.boxes is None:
        return annotated
    height, width = annotated.shape[:2]
    thickness = max(2, round(min(width, height) / 300))
    font_scale = max(.45, min(width, height) / 1000)
    for box in result.boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
        class_id = int(box.cls[0].item())
        confidence = float(box.conf[0].item())
        class_name = result.names.get(class_id, str(class_id))
        label = f"{class_name} {confidence:.2f}"
        x1, x2 = max(0, x1), min(width - 1, x2)
        y1, y2 = max(0, y1), min(height - 1, y2)
        cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 0, 255), thickness)
        (label_width, label_height), baseline = cv2.getTextSize(
            label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness
        )
        top = max(0, y1 - label_height - baseline - 8)
        cv2.rectangle(annotated, (x1, top), (min(width - 1, x1 + label_width + 8), y1), (0, 0, 255), -1)
        cv2.putText(annotated, label, (x1 + 4, max(label_height, y1 - baseline - 4)),
                    cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), thickness, cv2.LINE_AA)
    return annotated


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--weights", type=Path, default=Path("./weights/best.pt"))
    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument("--conf", type=float, default=.35)
    parser.add_argument("--imgsz", type=int, default=640)
    args = parser.parse_args()
    if not args.weights.is_file(): raise SystemExit(f"Weights not found: {args.weights}. Train a model first.")
    model = YOLO(str(args.weights))
    camera = cv2.VideoCapture(args.camera)
    if not camera.isOpened(): raise SystemExit(f"Could not open camera {args.camera}; check camera permissions.")
    print("Live detection started. Press q or Esc to quit.")
    try:
        while True:
            ok, frame = camera.read()
            if not ok:
                print("Camera frame read failed; stopping.")
                break
            result = model.predict(frame, imgsz=args.imgsz, conf=args.conf, verbose=False)[0]
            cv2.imshow("Freiburg Mobility Aids — YOLOv8", draw_detections(frame, result))
            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), 27): break
    finally:
        camera.release()
        cv2.destroyAllWindows()


if __name__ == "__main__": main()
