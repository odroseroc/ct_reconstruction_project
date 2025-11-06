import clr
from pathlib import Path
import time
from core.log_utils import no_op

class MotorController:
    # Dictionaries to interpret status and error codes
    ERROR_DICT = {
        "A": "A: Unknown message code or floating point controller address.",
        "B": "B: Controller address not correct.",
        "C": "C: Parameter missing or out of range.",
        "D": "D: Execution not allowed",
        "E": "E: home sequence already started.",
        "F": "F: ",
        "G": "G: Target position out of limits.",
        "H": "H: Execution not allowed in NOT REFERENCED state.",
        "I": "I: Execution not allowed in CONFIGURATION state.",
        "J": "J: Execution not allowed in DISABLE state.",
        "K": "K: Execution not allowed in READY state.",
        "L": "L: Execution not allowed in HOMING state.",
        "M": "M: Execution not allowed in MOVING state.",
        "W": "W: Command not allowed for SMC100PP version."
    }
    CONTROLLER_STATES_DICT = {
        "0A": "0A: NOT REFERENCED from reset.",
        "0B": "0B: NOT REFERENCED from HOMING.",
        "0C": "0C: NOT REFERENCED from CONFIGURATION.",
        "0D": "0D: NOT REFERENCED from DISABLE.",
        "0E": "0E: NOT REFERENCED from READY.",
        "0F": "0F: NOT REFERENCED from MOVING.",
        "10": "10: NOT REFERENCED ESP stage error.",
        "11": "11: NOT REFERENCED from JOGGING.",
        "14": "14: CONFIGURATION.",
        "1E": "1E: HOMING commanded from RS-232-C.",
        "1F": "1F: HOMING commanded from SMC-RC.",
        "28": "28: MOVING",
        "32": "32: READY from HOMING.",
        "33": "33: READY from MOVING.",
        "34": "34: READY from DISABLE.",
        "35": "32: READY from JOGGING.",
        "3C": "3C: DISABLE from READY.",
        "3D": "3D: DISABLE from MOVING.",
        "3E": "3E: DISABLE from JOGGING.",
        "46": "JOGGING from READY.",
        "47": "JOGGING from DISABLE."
    }
    def __init__(self,
                 dll_path: str,
                 port='COM6',
                 axis = 1,
                 log_fn=no_op
                 ):
        self.closed = False
        self.axis = axis
        self.port = port

        # Add reference to assembly
        dll_p = Path(dll_path)
        if not dll_p.exists():
            raise FileNotFoundError(dll_path)
        clr.AddReference(dll_path)

        # Import the .NET class and create an instance
        from CommandInterfaceSMC100 import SMC100
        self._smc = SMC100()

        # Open the instrument in the specified port
        result = self._smc.OpenInstrument(self.port)
        if result != 0:
            raise RuntimeError(f"Failed to open Instrument on {self.port}, error code {result}")
        log_fn(f"Opened Instrument on {self.port}")

        # If the motor is NOT REFERENCED, perform homing
        status = self.get_positioner_status()
        if status.startswith('0'):
            log_fn(f"Motor in NOT REFERENCED state ({status}), performing homing...")
            self.home(log_fn=log_fn)
            self.wait(log_fn=log_fn)
        if self.get_theoretical_position() != 0:
            log_fn(f"Motor is REFERENCED but not at position 0 ({self.get_theoretical_position()}), moving to 0...")
            self.move_absolute(0, log_fn=log_fn)
            self.wait(log_fn=log_fn)
        log_fn(f"Rotating stage ready to be used.")

    def execute(self, command, *params, log_fn=no_op, debug=False):
        """
                Dynamically execute any SMC100 command by name.
                :param command: String name of method (e.g. 'TP_Get', 'VE')
                :param params: Additional parameters for the method
                :returns: Tuple(response_value(s)) on success
                :raises RuntimeError: if the command returns an error code
                (Author: Benjamin Velin, 2025)
                """
        # Build method name: direct mapping to .NET API, e.g. 'TP_Get' or 'SR_Get'
        if not hasattr(self._smc, command):
            raise AttributeError(f"SMC100 has no command '{command}'")

        # Call the method with axis and any extra params
        method = getattr(self._smc, command)
        # Many methods follow signature: method(axis, *args)
        result_tuple = method(self.axis, *params)

        # At minimum: (resultCode, value), optionally ending with errString
        result_code = result_tuple[0]
        if result_code != 0:
            # Assume last element is error string if present
            err = result_tuple[-1] if len(result_tuple) > 1 else None
            raise RuntimeError(f"Error executing {command}: {self.ERROR_DICT.get(err, f"unknown. Ended with code {result_code}")}")

        # On success, return all output elements except the result code
        # (could be a single value or multiple)
        if debug == True:
            return result_tuple
        outputs = result_tuple[1:]
        # If only one output, unwrap it
        if len(outputs) == 2:
            return outputs[0]
        return outputs[:-1]

    def get_positioner_status(self) -> str:
        err_code, status_code = self.execute('TS')
        return status_code

    def show_positioner_status(self, statusCode, log_fn=print) -> None:
        log_fn(f'Positioner status: {self.CONTROLLER_STATES_DICT.get(statusCode, f"unknown {statusCode}")}')

    def is_moving(self) -> bool:
        return self.get_positioner_status() in ('28', '1E', '1F')

    def get_motion_time(self, dist):
        ''' Return motion time for a relative move dist '''
        self.execute('PT_Set', abs(dist))
        return self.execute('PT_Get')

    def get_current_position(self):
        return self.execute('TP')

    def get_theoretical_position(self):
        return self.execute('TH')

    def move_absolute(self, target_pos, log_fn=no_op) -> None:
        self.execute('PA_Set', abs(target_pos))
        log_fn(f"Moving to absolute position: {target_pos}")

    def move_relative(self, dist, log_fn=no_op) -> None:
        self.execute('PR_Set', abs(dist))
        log_fn(f"Moving a distance: {dist}")

    def get_target_position(self) -> float:
        return self.execute('PA_Get')

    def home(self, log_fn=no_op) -> None:
        ''' Perform homing sequence.'''
        self.execute('OR')
        log_fn(f"Homing...")

    def wait(self, poll_interval=0.2, log_fn=no_op) -> None:
        ''' Wait until the motor stops moving.'''
        log_fn("Waiting for motion to complete...")
        while self.is_moving():
            time.sleep(poll_interval)
        log_fn("Motion complete.")

    def close(self, log_fn = no_op):
        ''' Close the motor connection, returning to home position first.'''
        if not self.closed:
            log_fn("Returning to home position before closing...")
            self.move_absolute(0)
            self.wait()
            log_fn("Closing motor...")
            response = self._smc.CloseInstrument()
            if response != 0:
                raise RuntimeError(f"Failed to close Instrument on {self.port}, error code {response}")
            self.closed = True
            log_fn("Motor closed correctly.")
        else:
            log_fn("Motor already closed.")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        ''' 
        Ensure the motor connection is closed when exiting context. 
        Please note that this does not return to home position first. Whenever
        possible, use the close() method instead.
        '''
        if not self.closed:
            response = self._smc.CloseInstrument()
            if response != 0:
                raise RuntimeError(f"Failed to close Instrument on {self.port}, error code {response}")
            self.closed = True
        else:
            pass

    def __del__(self):
        ''' 
        Ensure the motor connection is closed when the object is deleted.
        Please note that this does not return to home position first. Whenever
        possible, use the close() method instead.
        '''
        if not self.closed:
            response = self._smc.CloseInstrument()
            if response != 0:
                raise RuntimeError(f"Failed to close Instrument on {self.port}, error code {response}")
            self.closed = True
        else:
            pass

def motor_basic_test():
    DLLPATH = r'C:\Windows\Microsoft.NET\assembly\GAC_64\Newport.SMC100.CommandInterface\v4.0_2.0.0.3__d9d722840772240b\Newport.SMC100.CommandInterface.dll'
    with MotorController(dll_path=DLLPATH,
                          port='COM6',
                          log_fn=print) as motor:
        motor.move_absolute(90, log_fn=print)
        motor.wait(log_fn=print)
        print(f"Reached position {motor.get_theoretical_position()}")
        time.sleep(2)
        motor.move_absolute(10, log_fn=print)
        motor.wait(log_fn=print)
        print(f"Homed position: {motor.get_theoretical_position()}")
        time.sleep(2)
        motor.close(log_fn=print)
    print("Done.")

if __name__ == "__main__":
    motor_basic_test()