# Freiburg Mobility Aids · YOLOv8

A modular pipeline for converting the University of Freiburg's Mobility Aids RGB dataset, training YOLOv8 Nano, and trying the trained detector on a local webcam. A small static browser page provides a camera preview for the hosted prototype.

## Dataset preparation

Install Python 3.10+ and the dependencies. The script defaults to the official Freiburg `Images_RGB.zip` and `Annotations_RGB.zip` archives:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python dataset_prep.py
```

The archives are downloaded into `data/freiburg_raw/`, extracted there, and paired by image/annotation filename stem. The converter supports Freiburg's YAML structure (`annotation.object` with `name`, `bndbox`, and `annotation.size`). It writes normalized YOLO labels and `data/freiburg_yolo/data.yaml`. The 12.4 GB RGB archive needs roughly three times its compressed size free for archive, extracted images, and prepared copies; a disk-space preflight stops before a download when space is insufficient. Override the official URLs with `--images-url` / `--annotations-url` or the `FREIBURG_IMAGES_URL` / `FREIBURG_ANNOTATIONS_URL` environment variables when needed.

## Train and run

```bash
python train_yolo.py
python webcam_demo.py
```

Training defaults to 30 epochs and 640px images. It selects CUDA, Apple MPS, or CPU automatically and copies the best checkpoint to `weights/best.pt`. The camera demo draws red rectangles with class names and confidence scores around detections; press `q` or Escape to quit.

Classes, in source order:

1. pedestrian
2. person in wheelchair
3. pedestrian pushing a person in a wheelchair
4. person using crutches
5. person using a walking frame

## Browser preview and Vercel

`index.html` is a static camera-preview UI and can be served locally with any static server (camera access requires localhost or HTTPS). It does not load the PyTorch checkpoint into the browser; use `webcam_demo.py` for actual live detections. The Vercel project deploys only the static frontend, not the dataset, Python training stack, or model weights.

To deploy after connecting the GitHub repository to Vercel:

```bash
npx vercel --prod
```

The dataset and model artifacts are excluded from Git. Do not commit the multi-gigabyte source archives or trained weights.
