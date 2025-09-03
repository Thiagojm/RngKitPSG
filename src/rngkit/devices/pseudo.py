import secrets


def detect() -> bool:
    return True


def read_bytes(n: int) -> bytes:
    return secrets.token_bytes(n)


