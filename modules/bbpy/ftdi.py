import os
import time
from typing import Optional, Tuple

# Try to select libusb1 backend explicitly before importing usb.core
from usb.backend import libusb1 as _libusb1

_backend = None
# Try common locations for libusb-1.0 on Windows: project root and bbpy/
_candidates = [
    os.path.join(os.getcwd(), "libusb-1.0.dll"),
    os.path.join(os.path.dirname(__file__), "libusb-1.0.dll"),
]
for _path in _candidates:
    if os.path.exists(_path):
        try:
            _backend = _libusb1.get_backend(find_library=lambda x: _path)
            break
        except Exception:
            _backend = None
if _backend is None:
    # fallback to system
    try:
        _backend = _libusb1.get_backend()
    except Exception:
        _backend = None

import usb.core
import usb.util


FTDI_VENDOR_ID = 0x0403


# FTDI control requests
FTDI_SIO_RESET = 0x00
FTDI_SIO_SET_FLOW_CTRL = 0x02
FTDI_SIO_SET_BAUD_RATE = 0x03  # unused here, MPSSE uses divisor instead
FTDI_SIO_SET_DATA = 0x04       # unused
FTDI_SIO_GET_MODEM_STATUS = 0x05
FTDI_SIO_SET_EVENT_CHAR = 0x06
FTDI_SIO_SET_ERROR_CHAR = 0x07
FTDI_SIO_SET_LATENCY_TIMER = 0x09
FTDI_SIO_GET_LATENCY_TIMER = 0x0A
FTDI_SIO_SET_BITMODE = 0x0B


# FTDI reset values
FTDI_SIO_RESET_SIO = 0
FTDI_SIO_RESET_PURGE_RX = 1
FTDI_SIO_RESET_PURGE_TX = 2


# FTDI flow control
FLOW_NONE = 0x0000
FLOW_RTS_CTS = 0x0100
FLOW_DTR_DSR = 0x0200
FLOW_XON_OFF = 0x0400


# FTDI bitmodes
BITMODE_RESET = 0x0000
BITMODE_MPSSE = 0x0200


# MPSSE commands
MPSSE_DATA_BYTE_IN_POS_MSB = 0x20
MPSSE_DATA_BYTE_IN_NEG_MSB = 0x24
MPSSE_DATA_BYTE_IN_POS_LSB = 0x28
MPSSE_DATA_BYTE_IN_NEG_LSB = 0x2C

MPSSE_SET_DATABITS_LOW = 0x80
MPSSE_SET_DATABITS_HIGH = 0x82
MPSSE_LOOPBACK = 0x84
MPSSE_NO_LOOPBACK = 0x85
MPSSE_SET_CLK_DIVISOR = 0x86
MPSSE_SEND_IMMEDIATE = 0x87

MPSSE_NO_CLK_DIV5 = 0x8A
MPSSE_NO_3PHASE_CLK = 0x8D
MPSSE_NO_ADAPTIVE_CLK = 0x97


class FTDIDevice:
    """Minimal FTDI/libusb wrapper to drive FT232H in MPSSE mode with PyUSB."""

    def __init__(
        self,
        dev: usb.core.Device,
        in_ep: int,
        out_ep: int,
        wMaxPacketSize: int,
        interface_index: int = 1,
        timeout_ms: int = 5000,
    ) -> None:
        self.dev = dev
        self.in_ep = in_ep
        self.out_ep = out_ep
        self.wMaxPacketSize = wMaxPacketSize
        self.interface_index = interface_index  # FTDI interface A = 1
        self.timeout_ms = timeout_ms

        # Internal read buffer state (similar to C++ chunking)
        self._rbuf = bytearray()

    # ---------- Device discovery ----------
    @staticmethod
    def find(
        vendor_id: int,
        product_id: int,
        serial: Optional[str] = None,
    ) -> Optional["FTDIDevice"]:
        # Pass backend explicitly if we have one
        kwargs = dict(idVendor=vendor_id, idProduct=product_id)
        if _backend is not None:
            kwargs["backend"] = _backend
        if serial is None:
            dev = usb.core.find(**kwargs)
        else:
            def _match(d):
                try:
                    return usb.util.get_string(d, d.iSerialNumber) == serial
                except Exception:
                    return False
            dev = usb.core.find(custom_match=_match, **kwargs)
        if dev is None:
            return None

        # Ensure configured
        if dev.get_active_configuration() is None:
            dev.set_configuration()

        cfg = dev.get_active_configuration()
        intf = usb.util.find_descriptor(cfg, bInterfaceNumber=0, bAlternateSetting=0)
        if intf is None:
            # fallback: first interface
            intf = cfg[(0, 0)]

        # claim if needed (ignore errors on Windows)
        try:
            if usb.util.device_has_kernel_driver(dev, intf.bInterfaceNumber):
                try:
                    dev.detach_kernel_driver(intf.bInterfaceNumber)
                except Exception:
                    pass
            usb.util.claim_interface(dev, intf.bInterfaceNumber)
        except Exception:
            pass

        # Endpoints: choose bulk IN and bulk OUT
        in_ep = None
        out_ep = None
        wMaxPacketSize = 64
        for ep in intf.endpoints():
            addr = ep.bEndpointAddress
            if addr & 0x80:
                in_ep = addr
                wMaxPacketSize = ep.wMaxPacketSize
            else:
                out_ep = addr
        if in_ep is None or out_ep is None:
            raise RuntimeError("Failed to find bulk IN/OUT endpoints")

        return FTDIDevice(dev, in_ep, out_ep, wMaxPacketSize)

    @staticmethod
    def find_any_bitbabbler(serial: Optional[str] = None) -> Optional["FTDIDevice"]:
        """Find any connected BitBabbler by scanning USB strings.

        This scans all USB devices and selects the first whose manufacturer or
        product string contains "bitbabbler" (case-insensitive). If a serial is
        provided, it must match exactly.
        """
        # Pass backend explicitly if we have one
        find_kwargs = {}
        if _backend is not None:
            find_kwargs["backend"] = _backend

        try:
            for dev in usb.core.find(find_all=True, **find_kwargs):
                try:
                    manufacturer = usb.util.get_string(dev, dev.iManufacturer) if dev.iManufacturer else ""
                    product = usb.util.get_string(dev, dev.iProduct) if dev.iProduct else ""
                except Exception:
                    manufacturer = ""
                    product = ""

                text = f"{manufacturer} {product}".lower()
                if "bitbabbler" not in text:
                    continue

                if serial is not None:
                    try:
                        dev_serial = usb.util.get_string(dev, dev.iSerialNumber) if dev.iSerialNumber else None
                    except Exception:
                        dev_serial = None
                    if dev_serial != serial:
                        continue

                # Ensure configured
                try:
                    if dev.get_active_configuration() is None:
                        dev.set_configuration()
                except Exception:
                    # Some backends raise if already configured; ignore
                    pass

                cfg = dev.get_active_configuration()
                intf = usb.util.find_descriptor(cfg, bInterfaceNumber=0, bAlternateSetting=0)
                if intf is None:
                    # fallback: first interface
                    intf = cfg[(0, 0)]

                # Claim interface when needed; ignore errors on Windows
                try:
                    if usb.util.device_has_kernel_driver(dev, intf.bInterfaceNumber):
                        try:
                            dev.detach_kernel_driver(intf.bInterfaceNumber)
                        except Exception:
                            pass
                    usb.util.claim_interface(dev, intf.bInterfaceNumber)
                except Exception:
                    pass

                # Endpoints: choose bulk IN and bulk OUT
                in_ep = None
                out_ep = None
                wMaxPacketSize = 64
                for ep in intf.endpoints():
                    addr = ep.bEndpointAddress
                    if addr & 0x80:
                        in_ep = addr
                        wMaxPacketSize = ep.wMaxPacketSize
                    else:
                        out_ep = addr
                if in_ep is None or out_ep is None:
                    # Not suitable
                    continue

                return FTDIDevice(dev, in_ep, out_ep, wMaxPacketSize)
        except Exception:
            pass

        return None

    # ---------- FTDI control helpers ----------
    def _ctrl_out(self, request: int, value: int, index: int) -> None:
        self.dev.ctrl_transfer(0x40, request, value, index, None, self.timeout_ms)

    def _ctrl_in(self, request: int, value: int, index: int, length: int) -> bytes:
        return bytes(self.dev.ctrl_transfer(0xC0, request, value, index, length, self.timeout_ms))

    def reset(self) -> None:
        self._ctrl_out(FTDI_SIO_RESET, FTDI_SIO_RESET_SIO, self.interface_index)

    def set_bitmode(self, bitmode: int, mask: int = 0) -> None:
        self._ctrl_out(FTDI_SIO_SET_BITMODE, (bitmode | (mask & 0xFF)) & 0xFFFF, self.interface_index)

    def set_latency(self, ms: int) -> None:
        if ms < 1 or ms > 255:
            raise ValueError("latency must be 1..255")
        self._ctrl_out(FTDI_SIO_SET_LATENCY_TIMER, ms, self.interface_index)

    def set_flow_control(self, mode: int) -> None:
        # Mode is passed in the index with interface
        self._ctrl_out(FTDI_SIO_SET_FLOW_CTRL, 0, (mode | self.interface_index) & 0xFFFF)

    def set_special_chars(self, event: int = 0, evt_enable: bool = False, error: int = 0, err_enable: bool = False) -> None:
        self._ctrl_out(FTDI_SIO_SET_EVENT_CHAR, (event | (0x100 if evt_enable else 0)) & 0x1FF, self.interface_index)
        self._ctrl_out(FTDI_SIO_SET_ERROR_CHAR, (error | (0x100 if err_enable else 0)) & 0x1FF, self.interface_index)

    def get_modem_status(self) -> int:
        data = self._ctrl_in(FTDI_SIO_GET_MODEM_STATUS, 0, self.interface_index, 2)
        if len(data) != 2:
            raise RuntimeError("GET_MODEM_STATUS returned wrong length")
        return (data[0] << 8) | data[1]

    # ---------- Bulk I/O ----------
    def write(self, data: bytes) -> None:
        # write may need chunking; usb core handles chunking but keep it simple
        self.dev.write(self.out_ep, data, self.timeout_ms)

    def _read_raw(self, size: int) -> bytes:
        # Read a multiple of wMaxPacketSize to avoid overflow from device
        if size % self.wMaxPacketSize:
            size += self.wMaxPacketSize - (size % self.wMaxPacketSize)
        data = self.dev.read(self.in_ep, size, self.timeout_ms)
        return bytes(data)

    def _consume_packets_strip_status(self, data: bytes) -> bytes:
        # FTDI prepends modem+line status in the first two bytes of every packet
        if not data:
            return b""
        out = bytearray()
        i = 0
        plen = self.wMaxPacketSize
        # Iterate over USB packets inside the buffer
        while i < len(data):
            chunk = data[i:i+plen]
            if len(chunk) == 0:
                break
            if len(chunk) < 2:
                # incomplete packet status; drop
                break
            # drop first two status bytes
            out.extend(chunk[2:])
            i += plen
        return bytes(out)

    def read_data(self, nbytes: int) -> bytes:
        out = bytearray()
        # drain any buffered content first
        if self._rbuf:
            take = min(nbytes, len(self._rbuf))
            out.extend(self._rbuf[:take])
            del self._rbuf[:take]
        while len(out) < nbytes:
            raw = self._read_raw(max(self.wMaxPacketSize, nbytes - len(out)))
            payload = self._consume_packets_strip_status(raw)
            if not payload:
                # avoid tight loop
                time.sleep(0.001)
                continue
            needed = nbytes - len(out)
            out.extend(payload[:needed])
            if len(payload) > needed:
                self._rbuf.extend(payload[needed:])
        return bytes(out)

    # ---------- MPSSE init and sync ----------
    def init_mpsse(self, latency_ms: int) -> bool:
        for _ in range(2):  # mirror the C++ reattempt before full reinit
            self.reset()
            # purge read by draining a raw read (best-effort)
            try:
                self._read_raw(self.wMaxPacketSize)
            except Exception:
                pass
            self.set_special_chars(0, False, 0, False)
            self.set_latency(latency_ms)
            self.set_flow_control(FLOW_RTS_CTS)
            self.set_bitmode(BITMODE_RESET, 0)
            self.set_bitmode(BITMODE_MPSSE, 0)
            time.sleep(0.050)
            try:
                _ = self.get_modem_status()
            except Exception:
                pass
            if self._check_sync(0xAA) and self._check_sync(0xAB):
                return True
        return False

    def _check_sync(self, cmd: int) -> bool:
        self.write(bytes([cmd, MPSSE_SEND_IMMEDIATE]))
        # Poll a few times for the expected 0xFA, cmd sequence
        for _ in range(10):
            try:
                data = self._read_raw(max(self.wMaxPacketSize, 512))
            except Exception:
                time.sleep(0.005)
                continue
            for i in range(len(data) - 1):
                if data[i] == 0xFA and data[i + 1] == cmd:
                    return True
            time.sleep(0.005)
        return False
