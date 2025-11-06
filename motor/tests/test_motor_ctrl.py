import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from motor import SMC100Controller
import time

DLLPATH = r'C:\Windows\Microsoft.NET\assembly\GAC_64\Newport.SMC100.CommandInterface\v4.0_2.0.0.3__d9d722840772240b\Newport.SMC100.CommandInterface.dll'
print(f"Using DLL path: {DLLPATH}")

with SMC100Controller(dll_path=DLLPATH,
                      port='COM6',
                      log_fn=print) as motor:
    # motor.go_home(log_fn=print)
    # motor.wait(log_fn=print)
    # print(f"Homed position: {motor.get_theoretical_position()}")
    # time.sleep(3)
    for d in range(60,181,60):
        motor.move_absolute(d, log_fn=print)
        motor.wait(log_fn=print)
        print(f"Reached position {motor.get_current_position()}")
        time.sleep(2)
    print(f"Final position {motor.get_current_position()}")
    time.sleep(2)
    motor.move_relative(25, log_fn=print)
    print(f"Moving relative 25 units to position {motor.get_target_position()}")
    motor.wait(log_fn=print)
    print(f"Reached position {motor.get_current_position()}")
    time.sleep(2)
    motor.move_absolute(0,log_fn=print)
    motor.wait(log_fn=print)
    print(f"Returned to position: {motor.get_theoretical_position()}")
    time.sleep(2)
    motor.close(log_fn=print)
print("Done.")