import winreg

def get_monitor_model_names():
    models = []
    try:
        key_path = r"SYSTEM\CurrentControlSet\Enum\DISPLAY"
        display_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path)
        i = 0
        while True:
            try:
                device_id = winreg.EnumKey(display_key, i)
                device_key = winreg.OpenKey(display_key, device_id)
                j = 0
                while True:
                    try:
                        sub_id = winreg.EnumKey(device_key, j)
                        sub_key = winreg.OpenKey(device_key, sub_id)
                        try:
                            # Intentar leer DeviceDesc o FriendlyName
                            try:
                                friendly, _ = winreg.QueryValueEx(sub_key, "FriendlyName")
                            except FileNotFoundError:
                                friendly, _ = winreg.QueryValueEx(sub_key, "DeviceDesc")
                            
                            # Limpiar prefijo como 'Generic PnP Monitor' o ';Generic PnP Monitor'
                            if ";" in friendly:
                                friendly = friendly.split(";")[-1]
                            
                            # Intentar leer los datos del EDID para extraer el nombre real del modelo
                            try:
                                edid_key = winreg.OpenKey(sub_key, "Device Parameters")
                                edid, _ = winreg.QueryValueEx(edid_key, "EDID")
                                # EDID contiene descriptores de texto en los bytes 54-125
                                text_blocks = []
                                for offset in (54, 72, 90, 108):
                                    block = edid[offset:offset+18]
                                    if block[0:3] == b'\x00\x00\x00':
                                        # Block type 0xfc = Monitor Name, 0xfe = Unspecified text
                                        if block[3] in (0xfc, 0xfe):
                                            name_bytes = block[5:]
                                            name_str = name_bytes.decode('latin-1', errors='ignore').split('\n')[0].split('\x00')[0].strip()
                                            if name_str:
                                                text_blocks.append(name_str)
                                if text_blocks:
                                    friendly = text_blocks[0]
                            except Exception as ex:
                                pass

                            if friendly and friendly not in models:
                                models.append((device_id, friendly))
                        except Exception:
                            pass
                        winreg.CloseKey(sub_key)
                        j += 1
                    except OSError:
                        break
                winreg.CloseKey(device_key)
                i += 1
            except OSError:
                break
        winreg.CloseKey(display_key)
    except Exception as e:
        print("Error leyendo registro:", e)
    return models

if __name__ == "__main__":
    found = get_monitor_model_names()
    for dev_id, model in found:
        print(f"Device: {dev_id} --> Modelo Real: '{model}'")
