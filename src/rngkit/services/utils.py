import os


def ensure_data_dir() -> str:
    """Return path to data directory and ensure it exists.

    Defaults to data/raw under the project root. Override with RNGKIT_DATA_DIR.
    """
    default_dir = os.path.join(os.getcwd(), "data", "raw")
    base = os.environ.get("RNGKIT_DATA_DIR", default_dir)
    os.makedirs(base, exist_ok=True)
    return base


def is_valid_params(bit_count: int, time_count: int) -> bool:
    if bit_count <= 0 or (bit_count % 8) != 0:
        return False
    if time_count < 1:
        return False
    return True


