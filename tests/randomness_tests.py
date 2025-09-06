"""Basic randomness tests for BitBabbler output.

This script can read random bytes from a connected BitBabbler device (via
`bbpy`) or from a file, then compute:
- Monobit frequency test (bits)
- Runs test (Wald–Wolfowitz) on bits
- Byte distribution chi-square statistic and p-approximation
- Shannon entropy per byte
- Serial correlation coefficient (bytes)

These are sanity checks, not a substitute for full suites like NIST STS or
Dieharder. For reliable assessment, use larger samples (e.g., multiple MB).

Examples:
    # Test 1KB from connected BitBabbler device:
    uv run -m tests.randomness_tests --bytes 1024

    # Test from file with XOR folding:
    uv run -m tests.randomness_tests --bytes 2048 --fold 2

    # Test data from a binary file:
    uv run -m tests.randomness_tests --file random_data.bin

    # Test data from a hex string file:
    uv run -m tests.randomness_tests --file hex_data.txt --hex
"""

import argparse
import math
import sys
from typing import Tuple

try:
    from modules.bbpy.bitbabbler import BitBabbler
except Exception:
    BitBabbler = None  # type: ignore


def read_from_device(num_bytes: int, folds: int) -> bytes:
    if BitBabbler is None:
        raise RuntimeError("bbpy is not available to read from device")
    bb = BitBabbler.open()
    # Always go through folded path; it now supports folds=0 with chunking
    data = bb.read_entropy_folded(num_bytes, folds=folds)
    return data


def bits_from_bytes(data: bytes):
    for b in data:
        for i in range(8):
            yield (b >> (7 - i)) & 1


def monobit_test(data: bytes) -> Tuple[float, float, int, int]:
    """Return (p_value, z, ones, zeros) for monobit frequency test."""
    bits = list(bits_from_bytes(data))
    n = len(bits)
    if n == 0:
        return (0.0, 0.0, 0, 0)
    ones = sum(bits)
    zeros = n - ones
    s = abs(ones - zeros)
    # Normal approximation for binomial: z = s / sqrt(n)
    z = s / math.sqrt(n)
    # Two-sided p-value using erfc
    p = math.erfc(z / math.sqrt(2.0))
    return (p, z, ones, zeros)


def runs_test(data: bytes) -> Tuple[float, int, float, float]:
    """Return (p_value, num_runs, expected_runs, z) for bit runs test.

    Uses Wald–Wolfowitz runs test on the bit sequence.
    """
    bits = list(bits_from_bytes(data))
    n = len(bits)
    if n < 2:
        return (0.0, 0, 0.0, 0.0)
    ones = sum(bits)
    zeros = n - ones
    if ones == 0 or zeros == 0:
        return (0.0, 1, 0.0, float("inf"))
    # Count runs
    runs = 1
    for i in range(1, n):
        if bits[i] != bits[i - 1]:
            runs += 1
    # Expected runs under randomness
    expected = 1 + (2 * ones * zeros) / n
    variance = (2 * ones * zeros * (2 * ones * zeros - n)) / (n ** 2 * (n - 1))
    if variance <= 0:
        return (0.0, runs, expected, float("inf"))
    z = (runs - expected) / math.sqrt(variance)
    p = math.erfc(abs(z) / math.sqrt(2.0))
    return (p, runs, expected, z)


def byte_chi_square(data: bytes) -> Tuple[float, float]:
    """Return (chi_square, p_approx) for byte distribution over 256 bins.

    p_approx uses a normal approximation to the chi-square distribution's CDF
    for df=255; this is rough but indicative. Prefer scipy for exact p.
    """
    n = len(data)
    if n == 0:
        return (0.0, 0.0)
    counts = [0] * 256
    for b in data:
        counts[b] += 1
    expected = n / 256.0
    chi = 0.0
    for c in counts:
        diff = c - expected
        chi += (diff * diff) / expected
    # Approximate p-value using Wilson–Hilferty transform
    df = 255
    c = (chi / df) ** (1.0 / 3.0)
    mu = 1 - 2 / (9 * df)
    sigma = math.sqrt(2 / (9 * df))
    z = (c - mu) / sigma
    p = 1 - 0.5 * (1 + math.erf(z / math.sqrt(2)))
    return (chi, p)


def shannon_entropy_per_byte(data: bytes) -> float:
    if not data:
        return 0.0
    counts = [0] * 256
    for b in data:
        counts[b] += 1
    n = len(data)
    entropy = 0.0
    for c in counts:
        if c == 0:
            continue
        p = c / n
        entropy -= p * math.log2(p)
    return entropy


def serial_correlation(data: bytes) -> float:
    """Return serial correlation coefficient across adjacent bytes (circular)."""
    n = len(data)
    if n < 2:
        return 0.0
    s1 = sum(data)
    s2 = sum(b * b for b in data)
    s12 = sum(data[i] * data[(i + 1) % n] for i in range(n))
    numerator = n * s12 - s1 * s1
    denominator = n * s2 - s1 * s1
    if denominator == 0:
        return 0.0
    return numerator / denominator


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Basic randomness tests for BitBabbler output")
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--bytes", type=int, help="Read this many bytes from device")
    src.add_argument("--file", help="Read bytes from file instead of device")
    p.add_argument("--fold", type=int, default=0, help="XOR-fold count for device reads (0 = none)")
    p.add_argument("--hex", action="store_true", help="Treat file input as hex string instead of raw")
    return p.parse_args()


def main() -> int:
    try:
        args = parse_args()
        if args.file:
            with open(args.file, "rb") as f:
                data = f.read()
            if args.hex:
                data = bytes.fromhex(data.decode().strip())
        else:
            data = read_from_device(args.bytes, folds=args.fold)

        if len(data) < 1024:
            print(f"warning: small sample size ({len(data)} bytes); results may be unreliable", file=sys.stderr)

        # Tests
        p_mono, z_mono, ones, zeros = monobit_test(data)
        p_runs, runs, expected_runs, z_runs = runs_test(data)
        chi, p_chi = byte_chi_square(data)
        ent = shannon_entropy_per_byte(data)
        rho = serial_correlation(data)

        # Report
        print("Sample size:", len(data), "bytes")
        print("Shannon entropy:", f"{ent:.5f}", "/ 8.00000 bits/byte")
        print("Serial correlation:", f"{rho:.6f}")
        print()
        print("Monobit frequency:")
        print("  ones:", ones, "zeros:", zeros)
        print("  z:", f"{z_mono:.4f}", "p-value:", f"{p_mono:.6f}")
        print()
        print("Runs test:")
        print("  runs:", runs, "expected:", f"{expected_runs:.2f}")
        print("  z:", f"{z_runs:.4f}", "p-value:", f"{p_runs:.6f}")
        print()
        print("Byte chi-square:")
        print("  chi^2:", f"{chi:.2f}", "df=255", "p~:", f"{p_chi:.6f}")

        return 0
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())


