# toyshop-decoder

Decoder for **Broderbund's The Toy Shop** (1986) `.M1`/`.M2`/… print data files. Converts the original Epson FX-80 dot-matrix printer output into modern PNG images.

## Background

*The Toy Shop* shipped paper craft projects as compressed bitmap data meant to be printed on 9-pin dot-matrix printers. Each toy's pages are stored in sequentially numbered files (e.g. `CAROUSEL.M1` … `CAROUSEL.M5`). This tool decodes the PackBits-compressed column data and renders it to standard image files.

## File format

| Section | Description |
|---------|-------------|
| **Header** (8 bytes, big-endian) | Bytes 0–3: total data length (file size − 4). Bytes 4–7: offset to vector section. |
| **Bitmap section** (PackBits RLE) | 720 columns × 72 bands of 8 vertical pins = 720 × 576 pixels. MSB-top bit order, stored right-to-left. |
| **Vector section** | Fold/cut reference marks. 6-byte vertex records and 10-byte shape records. |

## Requirements

- Python ≥ 3.12
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

## Quick start

```bash
# Clone and enter the repo
git clone https://github.com/ajryan/toyshop-decoder.git
cd toyshop-decoder

# Run with uv (installs dependencies automatically)
uv run render_toyshop.py CAROUSEL

# Or install as a CLI tool
uv pip install -e .
render-toyshop CAROUSEL
```

## Usage

```
render_toyshop.py [-h] [--orientation {portrait,landscape}] toy_name
```

| Argument | Description |
|----------|-------------|
| `toy_name` | Name of the toy to render (case-insensitive). |
| `--orientation` | `portrait` (default) or `landscape`. |

Output PNGs are written to the `out/` directory.

### Examples

```bash
# Render all pages of the carousel in portrait (default)
uv run render_toyshop.py CAROUSEL

# Render the glider in landscape
uv run render_toyshop.py glider --orientation landscape
```

## Available toys

The `data/` directory contains the following toys:

BALJET · BANK · CAROUSEL · CATAPULT · CRANE · FPROP · GLIDER · HELICRAF · JETDRAG · MERCER · OILPUMP · ORACLE · SAW · SCALE · SPIRIT · STARSHIP · STEAM · SUNDIAL · TRUCK · ZOETROPE

## License

This project is licensed under the [MIT License](LICENSE).