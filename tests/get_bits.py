"""Read a configurable number of bits from a BitBabbler device.

This script opens the first available BitBabbler (auto-detected by the bbpy
module) and prints the random value as:
- hex
- int (decimal)
- bin (zero-padded to the requested bit length)

Use --bits/-b to choose the bit length (must be a multiple of 8) and
--folds/-f to apply XOR folding before output.

Examples:
    # Read default 2048 bits (256 bytes) from device:
    uv run -m tests.get_bits

    # Read 1024 bits with short options:
    uv run -m tests.get_bits -b 1024

    # Read 4096 bits with 3-fold XOR:
    uv run -m tests.get_bits --bits 4096 --folds 3

    # Read 512 bits with 2-fold XOR:
    uv run -m tests.get_bits -b 512 -f 2
"""
import sys
import argparse

from modules.bbpy.bitbabbler import BitBabbler


def parse_args() -> argparse.Namespace:
    """Build and parse CLI arguments for bit length and folds."""
    parser = argparse.ArgumentParser(
        description="Read entropy from BitBabbler and print as hex and binary."
    )
    parser.add_argument(
        "-b",
        "--bits",
        type=int,
        default=2048,
        help="Number of bits to read (must be a positive multiple of 8). Default: 2048",
    )
    parser.add_argument(
        "-f",
        "--folds",
        type=int,
        default=0,
        help="Number of folds to apply (>= 0). Default: 0",
    )
    return parser.parse_args()


def main() -> int:
    """Entry point for the get_bits script.

    Returns 0 on success, 1 on error.
    """
    try:
        args = parse_args()
        bits = args.bits
        folds = args.folds

        if bits <= 0 or bits % 8 != 0:
            raise ValueError("bits must be a positive multiple of 8")
        if folds < 0:
            raise ValueError("folds must be >= 0")

        num_bytes = bits // 8

        bb = BitBabbler.open()
        data = bb.read_entropy_folded(num_bytes, folds=folds)

        # Print as hex
        print("hex:", data.hex())

        # Print as N-bit binary number (zero-padded)
        n = int.from_bytes(data, byteorder="big", signed=False)
        print("int:", n)
        print("bin:", format(n, f"0{bits}b"))
        return 0
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
