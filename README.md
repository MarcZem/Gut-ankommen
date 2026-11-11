# Freiburg Mobility Aids · YOLOv8

[![Open in Google Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/MarcZem/Gut-ankommen/blob/main/train_in_colab.ipynb)

A modular pipeline for converting the University of Freiburg's Mobility Aids RGB dataset, training YOLOv8 Nano, and trying the trained detector on a local webcam. A small static browser page provides a camera preview for the hosted prototype.

## Pre-registration

The mobile-friendly sign-up page is available at [`/preregister`](https://gut-ankommen.vercel.app/preregister). It submits email addresses directly to Web3Forms and does not use an app database. Configure `NEXT_PUBLIC_WEB3FORMS_KEY` in the Vercel project environment (or copy `.env.example` to `.env.local` for a local build). The build step injects this public Web3Forms key into the browser bundle, as required by the service. Never commit a populated `.env.local` file.

The pitch-deck QR image is [`public/qr-code.png`](public/qr-code.png). Regenerate it with `python scripts/generate_qr.py`; pass `--url` to encode a different production URL. To run a local static build, use `node scripts/build.mjs`; the generated site is written to `dist/`.

## Train in Google Colab

Open the notebook with the badge above, select **Runtime → Change runtime type → T4 GPU** when available, then run all cells. It clones this repository, installs the Python dependencies, downloads and prepares the Freiburg RGB dataset in the Colab VM, trains YOLOv8 Nano for 30 epochs, and downloads `best.pt` to your computer. Free T4 availability depends on Colab; the notebook checks for an active CUDA GPU and available disk space before starting.

After the browser download completes, put the model at `./weights/best.pt` in your local checkout and start the camera demo:

```bash
python webcam_demo.py --weights ./weights/best.pt
```

The notebook also includes an optional Google Drive copy cell. Colab VM files are temporary, so download the model or save it to Drive before ending the runtime.

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

Training defaults to 30 epochs and 640px images. It selects CUDA, Apple MPS, or CPU automatically and copies the best checkpoint to `weights/best.pt`. The webcam demo defaults to `./weights/best.pt`, draws red rectangles with class names and confidence scores around detections, and exits when you press `q` or Escape.

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
