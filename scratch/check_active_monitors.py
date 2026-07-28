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

def get_active_desktop_monitors():
    user32 = ctypes.windll.user32
    active_monitors = []
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
                # DISPLAY_DEVICE_ACTIVE = 0x1
                if mon.StateFlags & 0x1:
                    active_monitors.append((adapter.DeviceName, mon.DeviceString, mon.DeviceID))
                j += 1
        i += 1
    return active_monitors

if __name__ == "__main__":
    from monitorcontrol import get_monitors
    raw = list(get_monitors())
    print(f"monitorcontrol detecta {len(raw)} monitores activos:")
    for idx, m in enumerate(raw):
        print(f"  [{idx}] VCP handle: {m}")

    active_win = get_active_desktop_monitors()
    print(f"\nWindows Desktop API detecta {len(active_win)} monitores activos en el escritorio:")
    for idx, (adap, name, dev_id) in enumerate(active_win):
        print(f"  [{idx}] Adaptador: {adap} | Nombre: {name} | ID: {dev_id}")
