"""
Decoder for Broderbund's The Toy Shop .M1 data files.

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

Output is rotated 180 degrees to correct orientation.
"""
import os
import struct
import sys
from PIL import Image, ImageDraw

INPUT_FILE = os.path.join("data", "CAROUSEL.M1")


def decode_packbits(data):
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
            out.extend(data[i:i + count])
            i += count
        else:
            count = 257 - n
            i += 1
            if i < len(data):
                out.extend(bytes([data[i]]) * count)
            i += 1
    return bytes(out)


def render_bitmap(decoded, cols=720):
    """Render band data: MSB=top pin, horizontally flipped."""
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
    return img


def parse_vectors(data):
    """Parse vector/annotation section."""
    entries = []
    i = 0
    while i + 6 <= len(data):
        cmd = data[i]
        sub = data[i + 1]
        x = struct.unpack(">H", data[i+2:i+4])[0]
        y = struct.unpack(">H", data[i+4:i+6])[0]

        if cmd == 0x02 and sub in (0x01, 0x03) and i + 10 <= len(data):
            p1 = struct.unpack(">H", data[i+6:i+8])[0]
            p2 = struct.unpack(">H", data[i+8:i+10])[0]
            entries.append({"cmd": cmd, "sub": sub, "x": x, "y": y,
                            "p1": p1, "p2": p2})
            i += 10
        else:
            entries.append({"cmd": cmd, "sub": sub, "x": x, "y": y})
            i += 6

        # Check for terminator
        if i + 4 <= len(data) and data[i:i+4] == b'\x00\x00\x00\x00':
            break

    return entries


def main():
    with open(INPUT_FILE, "rb") as f:
        raw = f.read()

    OUTPUT_FOLDER = "out"

    total_len = struct.unpack(">I", raw[0:4])[0]
    vec_offset = struct.unpack(">I", raw[4:8])[0]

    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    # Decode bitmap
    decoded = decode_packbits(raw[8:vec_offset])
    img = render_bitmap(decoded)

    # Rotate 180 degrees to correct orientation
    img = img.rotate(180)

    # Save landscape version
    img.save(os.path.join(OUTPUT_FOLDER, "carousel_landscape.png"))
    print(f"Saved {os.path.join(OUTPUT_FOLDER, 'carousel_landscape.png')} (720x576)")

    # Save portrait version (rotated 90 CW for Letter paper)
    img_portrait = img.rotate(-90, expand=True)
    img_portrait.save(os.path.join(OUTPUT_FOLDER, "carousel_portrait.png"))
    print(f"Saved {os.path.join(OUTPUT_FOLDER, 'carousel_portrait.png')} (576x720)")

    # Save 2x scaled versions
    img_2x = img.resize((1440, 1152), Image.NEAREST)
    img_2x.save(os.path.join(OUTPUT_FOLDER, "carousel_landscape_2x.png"))
    print(f"Saved {os.path.join(OUTPUT_FOLDER, 'carousel_landscape_2x.png')} (1440x1152)")

    img_portrait_2x = img_portrait.resize((1152, 1440), Image.NEAREST)
    img_portrait_2x.save(os.path.join(OUTPUT_FOLDER, "carousel_portrait_2x.png"))
    print(f"Saved {os.path.join(OUTPUT_FOLDER, 'carousel_portrait_2x.png')} (1152x1440)")

    # Parse and display vector section info
    vectors = parse_vectors(raw[vec_offset:])
    print(f"\nVector section: {len(vectors)} entries at offset 0x{vec_offset:04X}")
    for v in vectors:
        extra = f" params=({v['p1']},{v['p2']})" if 'p1' in v else ""
        print(f"  cmd=0x{v['cmd']:02X} sub=0x{v['sub']:02X} "
              f"x={v['x']:4d} y={v['y']:4d}{extra}")

    print(f"\n=== Format Summary ===")
    print(f"File: {INPUT_FILE} ({len(raw)} bytes)")
    print(f"Compression: PackBits RLE ({len(raw[8:vec_offset])} -> {len(decoded)} bytes)")
    print(f"Bitmap: 720 x 576 px (720 cols x 72 bands x 8 pins)")
    print(f"  Orientation: landscape, mirrored (flip-H to correct)")
    print(f"  Bit order: MSB = top pin in each column byte")
    print(f"  Target: Epson FX-80 compatible dot-matrix printer")
    print(f"  ~10\" x 8\" at 72 DPI (US Letter landscape)")
    print(f"Vector overlay: {len(vectors)} reference mark entries")


if __name__ == "__main__":
    main()
