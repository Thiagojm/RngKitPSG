# BitBabbler Python Tools

Python utilities for reading true random data from BitBabbler USB devices (FTDI-based), mirroring the C++ tools.

## Features
- Opens the BitBabbler device over libusb and puts the FTDI into MPSSE mode
- Reads raw entropy bytes efficiently with chunking
- Optional XOR folding (same as C++ `FoldBytes`) to post-process data
- Simple CLI and importable Python API
- Auto-detects BitBabbler devices by VID:PID and by USB descriptor strings

## Requirements
- Python (tested with 3.8+)
- `pyusb` (installed via `requirements.txt` or `pyproject.toml`)
- libusb-1.0 runtime available at runtime
  - Windows: `libusb-1.0.dll` present in project root or `bbpy/`, or on `PATH`
  - Linux/macOS: system `libusb-1.0` (or `libusb-1.0.0.dylib` on macOS)
- Windows driver: device must be bound to a libusb-compatible driver (WinUSB/libusbK)
  - Use Zadig to switch the BitBabbler device from FTDI VCP to WinUSB (recommended)

## Install

Using `uv`:
```bash
uv pip install -r requirements.txt
```

Using `pip` directly:
```bash
pip install -r requirements.txt
```

## Quick start

Read 1024 bytes and print as hex:
```bash
uv run -m bbpy read --bytes 1024 --hex
# or
python -m bbpy read --bytes 1024 --hex
```

Write raw bytes to a file:
```bash
python -m bbpy read --bytes 4096 -o rng.bin
```

Specify fold and custom FTDI parameters:
```bash
python -m bbpy read --bytes 4096 --fold 2 --bitrate 2500000 --latency 3
```

Select a specific device by serial:
```bash
python -m bbpy read --bytes 1024 --serial YOUR_SERIAL
```

## Programmatic API

```python
from bbpy.bitbabbler import BitBabbler

# Open the first BitBabbler
bb = BitBabbler.open()

# Read 4096 raw bytes (no folding)
data = bb.read_entropy(4096)

# Read 2048 bytes after folding twice (reads 8192 raw bytes internally)
folded = bb.read_entropy_folded(2048, folds=2)
```

## Bits example script

`get_bits.py` reads a configurable number of bits (default 2048) with optional folding, and prints the value in hex, decimal, and zero-padded binary.

Examples:
```bash
# Default: 2048 bits, 0 folds
python get_bits.py

# Custom: 1024 bits, 2 folds
python get_bits.py -b 1024 -f 2
```

Notes:
- `--bits/-b` must be a positive multiple of 8 (e.g., 256, 1024, 2048).
- `--folds/-f` must be a non-negative integer.

## Randomness tests

`randomness_tests.py` runs quick statistical checks (Shannon entropy, serial correlation, monobit, runs, and byte chi-square) on data from the device or a file.

Examples:
```bash
# From device: 1 MiB sample, no folding
python randomness_tests.py --bytes 1048576

# From device with folding
python randomness_tests.py --bytes 1048576 --fold 2

# From file (raw bytes)
python randomness_tests.py --file rng.bin

# From file (hex-encoded text)
python randomness_tests.py --file rng.hex --hex
```

## Folding

Folding reduces the output length by XOR-combining halves repeatedly (like C++ `FoldBytes`):
- `fold = 1` → output length = input length / 2
- `fold = 2` → output length = input length / 4
- In the CLI: `--bytes` is the final output length after folding. The tool handles reading the necessary raw length (up to 65536 per read, automatically chunked).

## Troubleshooting

- error: No backend available
  - Ensure `libusb-1.0` is available:
    - Windows: keep `libusb-1.0.dll` in the project root or `bbpy/`, or add to `PATH`
    - The code auto-loads from those locations
- error: Failed to initialize BitBabbler (MPSSE sync)
  - Unplug/replug the device and retry
  - Ensure Windows driver is WinUSB/libusbK (use Zadig)
  - Try a lower latency: `--latency 3`
  - If multiple FTDI devices are connected, specify `--serial`
- Permission denied (Linux/macOS)
  - Add appropriate udev rules (Linux) or run with sufficient permissions

## Notes
- Vendor/Product IDs: 0x0403 / 0x7840
- The Python layer mirrors the FTDI/MPSSE sequence from the C++ implementation (`include/bit-babbler/ftdi-device.h` and `include/bit-babbler/secret-source.h`).
- The default bitrate is ~2.5 MHz; you can override with `--bitrate`.
