import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from xrsource.xrs_controller import XRSController
import time

with XRSController(port='COM4', timeout=1) as xrs:
    xrs.show_status()
    print(xrs.get_presets())
    xrs.xon()
    time.sleep(2) # Allow time for the x-ray source to stabilize
    xrs.show_batch_status()
    mth_time_start = time.time()
    xrs.xoff()
    mth_time_end = time.time()
    time.sleep(2)
    print(f"Method execution time: {mth_time_end - mth_time_start} seconds")
    print('-------------------------------------------')
    xrs.show_status()
    xrs.xon()
    time.sleep(2)
    xrs.show_batch_status()
    cmd_time_start = time.time()
    xrs.xoff()
    cmd_time_end = time.time()
    time.sleep(2)
    print(f"Command execution time: {cmd_time_end - cmd_time_start} seconds")
    print('-------------------------------------------')

