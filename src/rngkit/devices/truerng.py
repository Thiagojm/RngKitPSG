from serial.tools import list_ports
import serial


def detect() -> bool:
    ports = list(list_ports.comports())
    for p in ports:
        if p[1].startswith("TrueRNG"):
            return True
    return False


def read_bytes(blocksize: int) -> bytes:
    ports = list(list_ports.comports())
    port = None
    for p in ports:
        if p[1].startswith("TrueRNG"):
            port = str(p[0])
            break
    if port is None:
        raise RuntimeError("TrueRNG device not found")
    ser = serial.Serial(port=port, timeout=10)
    try:
        if not ser.isOpen():
            ser.open()
        ser.setDTR(True)
        ser.flushInput()
        return ser.read(blocksize)
    finally:
        try:
            ser.close()
        except Exception:
            pass


