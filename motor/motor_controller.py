import clr
from pathlib import Path
import time
from core.log_utils import no_op

class SMC100Controler:
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
        self.axis = axis
        self.port = port

        # Add reference to assembly
        dll_path = Path(dll_path)
        if not dll_path.exists():
            raise FileNotFoundError(dll_path)
        clr.AddReferenceToFile(dll_path)
        from CommandInterfaceSMC100 import SMC100

        # Create a device instance
        self._smc = SMC100()
        result = self._smc.OpenInstrument(self.port)
        if result != 0:
            raise RuntimeError(f"Failed to open Instrument on {self.port}, error code {result}")
        log_fn(f"Opened Instrument on {self.port}")
        self.go_home(log_fn=log_fn)
        while self.is_moving(): time.sleep(1)
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

    def get_positioner_status(self): -> str
        errorCode, status_code = self.execute('TS')
        if errorCode != 0:
            raise RuntimeError(f"Positioner error code {status_code}")
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

    def get_teoretical_position(self):
        return self.execute('TH')

    def move_absolute(self, target_pos, log_fn=no_op) -> None:
        self.execute('PA_Set', abs(target_pos))
        log_fn(f"Moving to absolute position: {target_pos}")

    def move_relative(self, dist, log_fn=no_op) -> None:
        self.execute('PR_Set', abs(dist))
        log_fn(f"Moving a distance: {dist}")

    def get_target_position(self) -> float:
        return self.execute('PA_get')

    def go_home(self, log_fn=no_op) -> None:
        self.execute('OR')
        log_fn(f"Homing...")

    def close(self, log_fn = no_op):
        response = self._smc.CloseInstrument()
        log_fn("Motor closed correctly.")
        if response != 0:
            raise RuntimeError(f"Failed to close Instrument on {self.port}, error code {response}")
        self._smc.UnregisterInstrument()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __del__(self):
        self.close()
