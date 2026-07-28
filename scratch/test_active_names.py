import ctypes
from ctypes import wintypes
import winreg

class DISPLAY_DEVICE(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("DeviceName", wintypes.WCHAR * 32),
        ("DeviceString", wintypes.WCHAR * 128),
        ("StateFlags", wintypes.DWORD),
        ("DeviceID", wintypes.WCHAR * 128),
        ("DeviceKey", wintypes.WCHAR * 128)
    ]

def get_active_monitor_names():
    names = []
    user32 = ctypes.windll.user32
    i = 0
    while True:
        adapter = DISPLAY_DEVICE()
        adapter.cb = ctypes.sizeof(DISPLAY_DEVICE)
        if not user32.EnumDisplayDevicesW(None, i, ctypes.byref(adapter), 0):
            break
        
        if adapter.StateFlags & 0x1:
            j = 0
            while True:
                mon = DISPLAY_DEVICE()
                mon.cb = ctypes.sizeof(DISPLAY_DEVICE)
                if not user32.EnumDisplayDevicesW(adapter.DeviceName, j, ctypes.byref(mon), 0):
                    break
                if mon.StateFlags & 0x1:
                    dev_id = mon.DeviceID
                    friendly_name = ""
                    if dev_id:
                        parts = dev_id.split("\\")
                        if len(parts) >= 3:
                            pnp_code = parts[1]
                            reg_path = rf"SYSTEM\CurrentControlSet\Enum\DISPLAY\{pnp_code}\{parts[2]}"
                            try:
                                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path)
                                try:
                                    edid_key = winreg.OpenKey(key, "Device Parameters")
                                    edid, _ = winreg.QueryValueEx(edid_key, "EDID")
                                    for offset in (54, 72, 90, 108):
                                        block = edid[offset:offset+18]
                                        if block[0:3] == b'\x00\x00\x00' and block[3] in (0xfc, 0xfe):
                                            name_str = block[5:].decode('latin-1', errors='ignore').split('\n')[0].split('\x00')[0].strip()
                                            if name_str and name_str not in ("Generic PnP Monitor", "Monitor PnP genérico"):
                                                friendly_name = name_str
                                                break
                                except Exception:
                                    pass
                                winreg.CloseKey(key)
                            except Exception:
                                pass

                    if not friendly_name:
                        friendly_name = f"Monitor {len(names) + 1}"

                    names.append(friendly_name)
                j += 1
        i += 1
    return names

if __name__ == "__main__":
    active = get_active_monitor_names()
    print("Monitores activos identificados 1:1:", active)
