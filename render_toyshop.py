"""
Decoder for Broderbund's The Toy Shop (1986) .M1/.M2/... print data files.

File format:
  - Header: 8 bytes (big-endian)
    - Bytes 0-3: total data length (file size - 4)
    - Bytes 4-7: offset to vector section
  - Bitmap section: PackBits RLE compressed
    - 720 columns x 72 bands of 8 vertical pins = 720x576 pixels
    - MSB-top bit order, data stored right-to-left (flip horizontally)
    - Epson FX-80 compatible 9-pin column format (using 8 pins)
  - Vector section: fold/cut reference marks
    - 6-byte vertex records: cmd, sub, x_hi, x_lo, y_hi, y_lo
    - 10-byte shape records (cmd=0x02, sub=0x01 or 0x03): adds param1, param2

Usage:
    uv run render_toyshop.py CAROUSEL
    uv run render_toyshop.py carousel        # case-insensitive
    render-toyshop CAROUSEL                  # if installed via uv
"""
import argparse
import struct
import sys
from pathlib import Path

from PIL import Image

DATA_DIR = Path(__file__).parent / "data"
OUT_DIR = Path(__file__).parent / "out"
COLS = 720


def decode_packbits(data: bytes) -> bytes:
    """Decode PackBits-style RLE compression."""
    out = bytearray()
    i = 0
    while i < len(data):
        n = data[i]
        if n == 0x80:
            i += 1
            continue
        if n <= 127:
            count = n + 1
            i += 1
            out.extend(data[i : i + count])
            i += count
        else:
            count = 257 - n
            i += 1
            if i < len(data):
                out.extend(bytes([data[i]]) * count)
            i += 1
    return bytes(out)


def render_bitmap(decoded: bytes, cols: int = COLS) -> Image.Image:
    """Render band data: MSB=top pin, horizontally flipped, then rotated 180°."""
    num_bands = len(decoded) // cols
    height = num_bands * 8
    img = Image.new("1", (cols, height), 1)
    pixels = img.load()
    for band in range(num_bands):
        for col in range(cols):
            byte_val = decoded[band * cols + col]
            x = cols - 1 - col  # horizontal flip
            for pin in range(8):
                if (byte_val >> (7 - pin)) & 1:  # MSB = top
                    pixels[x, band * 8 + pin] = 0
    return img.rotate(180)


def render_file(path: Path, out_dir: Path, orientation: str) -> None:
    """Decode one .M? file and save a PNG in the requested orientation."""
    raw = path.read_bytes()
    vec_offset = struct.unpack(">I", raw[4:8])[0]
    decoded = decode_packbits(raw[8:vec_offset])
    img = render_bitmap(decoded)

    if orientation == "portrait":
        img = img.rotate(-90, expand=True)

    stem = path.stem.upper() + path.suffix.upper()  # e.g. CAROUSEL.M1
    out_path = out_dir / f"{stem}_{orientation}.png"
    img.save(out_path)

    print(f"  {path.name} -> {out_path.name}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Render Toy Shop .M? files to PNG images."
    )
    parser.add_argument(
        "toy_name",
        help="Toy name to render (e.g. CAROUSEL). Case-insensitive.",
    )
    parser.add_argument(
        "--orientation",
        choices=["landscape", "portrait"],
        default="landscape",
        help="Output orientation (default: landscape).",
    )
    args = parser.parse_args()

    toy = args.toy_name.upper()
    pages = sorted(DATA_DIR.glob(f"{toy}.M?"))

    if not pages:
        print(f"Error: no files matching data/{toy}.M? found.", file=sys.stderr)
        available = sorted({p.stem.upper() for p in DATA_DIR.glob("*.M?")})
        print(f"Available toys: {', '.join(available)}", file=sys.stderr)
        sys.exit(1)

    OUT_DIR.mkdir(exist_ok=True)
    print(f"Rendering {len(pages)} page(s) for {toy} ({args.orientation}):")
    for page in pages:
        render_file(page, OUT_DIR, args.orientation)


if __name__ == "__main__":
    main()
