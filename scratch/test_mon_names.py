import sys
sys.path.insert(0, 'src')
from brightness_ctrl import BrightnessController

bc = BrightnessController()
for m in bc.monitors:
    print(f"Monitor {m.index}: Name='{m.name}', DDC={m.ddc_ok}, Brightness={m.brightness}%")
