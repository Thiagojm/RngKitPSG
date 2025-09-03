"""Command-line interface for BitBabbler Python tools.

Provides a `read` subcommand to fetch random bytes from a BitBabbler device,
optionally applying XOR folding and printing as hex or writing to a file.
"""
import argparse
import binascii
import sys
from typing import Optional

from .bitbabbler import BitBabbler


def cmd_read(args: argparse.Namespace) -> int:
    """Handle the `read` subcommand.

    Opens a BitBabbler (optionally by serial), applies bitrate/latency if
    provided, reads the requested byte count (after folding), and prints or
    writes the result.
    """
    try:
        bb = BitBabbler.open(serial=args.serial)
        if args.bitrate or args.latency:
            # re-init with custom params
            bb = BitBabbler(bb, bitrate=args.bitrate, latency_ms=args.latency)
            bb.init()
        if args.fold and args.fold > 0:
            data = bb.read_entropy_folded(args.bytes, args.fold)
        else:
            data = bb.read_entropy(args.bytes)
        if args.out:
            with open(args.out, "wb") as f:
                f.write(data if not args.hex else binascii.hexlify(data))
        else:
            if args.hex:
                print(binascii.hexlify(data).decode())
            else:
                sys.stdout.buffer.write(data)
        return 0
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        return 1


def build_argparser() -> argparse.ArgumentParser:
    """Create the top-level argument parser for the `bbpy` CLI."""
    p = argparse.ArgumentParser(prog="bbpy", description="BitBabbler Python CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("read", help="Read random bytes from BitBabbler")
    r.add_argument("--bytes", type=int, required=True, help="Number of output bytes to read (after folding)")
    r.add_argument("--fold", type=int, default=0, help="XOR-fold count (0 = none)")
    r.add_argument("--hex", action="store_true", help="Print hex instead of raw bytes")
    r.add_argument("-o", "--out", help="Output file (defaults to stdout)")
    r.add_argument("--serial", help="Match device by serial number")
    r.add_argument("--bitrate", type=int, help="Bitrate in Hz (default 2500000)")
    r.add_argument("--latency", type=int, help="FTDI latency timer in ms (1..255)")
    r.set_defaults(func=cmd_read)

    return p


def main(argv: Optional[list] = None) -> int:
    """CLI entry point for `python -m bbpy`. Returns process exit code."""
    parser = build_argparser()
    args = parser.parse_args(argv)
    return args.func(args)
