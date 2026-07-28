import ctypes
from ctypes import wintypes

class DISPLAY_DEVICE(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("DeviceName", wintypes.WCHAR * 32),
        ("DeviceString", wintypes.WCHAR * 128),
        ("StateFlags", wintypes.DWORD),
        ("DeviceID", wintypes.WCHAR * 128),
        ("DeviceKey", wintypes.WCHAR * 128)
    ]

def get_monitor_names():
    names = []
    user32 = ctypes.windll.user32
    i = 0
    while True:
        adapter = DISPLAY_DEVICE()
        adapter.cb = ctypes.sizeof(DISPLAY_DEVICE)
        if not user32.EnumDisplayDevicesW(None, i, ctypes.byref(adapter), 0):
            break
        
        # DISPLAY_DEVICE_ATTACHED_TO_DESKTOP = 0x1
        if adapter.StateFlags & 0x1:
            j = 0
            while True:
                mon = DISPLAY_DEVICE()
                mon.cb = ctypes.sizeof(DISPLAY_DEVICE)
                if not user32.EnumDisplayDevicesW(adapter.DeviceName, j, ctypes.byref(mon), 0):
                    break
                if mon.StateFlags & 0x1: # ACTIVE
                    name = mon.DeviceString.strip()
                    if name and name not in names:
                        names.append(name)
                j += 1
        i += 1
    return names

if __name__ == "__main__":
    mon_names = get_monitor_names()
    print("Monitores encontrados:", mon_names)
