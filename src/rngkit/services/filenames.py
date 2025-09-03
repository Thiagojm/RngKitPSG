import re
from datetime import datetime
from typing import Optional


def format_capture_name(device: str, bits: int, interval: int, folds: Optional[int] = None) -> str:
    """Return canonical filename stem for a capture.

    Example: 20201011T142208_bitb_s2048_i1_f0
    """
    ts = datetime.now().strftime("%Y%m%dT%H%M%S")
    name = f"{ts}_{device}_s{bits}_i{interval}"
    if device == "bitb" and folds is not None:
        name += f"_f{folds}"
    return name


def parse_bits(name: str) -> int:
    m = re.search(r"_s(\d+)_", name)
    if not m:
        raise ValueError("bits not found in name")
    return int(m.group(1))


def parse_interval(name: str) -> int:
    m = re.search(r"_i(\d+)", name)
    if not m:
        raise ValueError("interval not found in name")
    return int(m.group(1))


