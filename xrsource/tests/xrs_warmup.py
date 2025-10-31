import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from xrsource.xrs_controller import XRSController
import time

xrs = XRSController(port='COM4')
xrs.show_status()
xrs.show_preheat_status()
print(xrs.send_command("SWE"))
print(xrs.start_warmup())
time.sleep(2)
print(xrs.get_status())
print(xrs.get_status().strip() == 'STS 1'.strip())
while xrs.get_status().strip() == 'STS 1'.strip():
    print(f'Warming up... Current status: {xrs.get_warmup_status()}')
    print(f'Current warmup step: {xrs.get_warmup_step()}')
    time.sleep(10)
print(xrs.get_status())
xrs.close()
print("warmup complete")