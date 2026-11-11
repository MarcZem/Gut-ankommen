#!/usr/bin/env python3
"""Generate the high-resolution Gut ankommen pre-registration QR code."""
import argparse
from pathlib import Path

import qrcode
from qrcode.constants import ERROR_CORRECT_H

DEFAULT_URL = "https://gut-ankommen.vercel.app/preregister"
DEFAULT_OUTPUT = Path("public/qr-code.png")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=DEFAULT_URL, help="Destination encoded in the QR code")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--box-size", type=int, default=24, help="Pixels per QR module")
    args = parser.parse_args()
    if args.box_size < 8:
        parser.error("--box-size must be at least 8 for a presentation-ready image")

    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECT_H,
        box_size=args.box_size,
        border=4,
    )
    qr.add_data(args.url)
    qr.make(fit=True)
    image = qr.make_image(fill_color="#101614", back_color="white").convert("RGB")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    image.save(args.output, format="PNG", optimize=True, dpi=(300, 300))
    print(f"QR code saved to {args.output.resolve()} ({image.width}×{image.height}px)")
    print(f"Destination: {args.url}")


if __name__ == "__main__":
    main()
