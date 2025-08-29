import serial
import time

class XRaySource:
    def __init__(self, port='COM4', timeout=0.1):
        self.ser = serial.Serial(
            port=port,
            baudrate=38400,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=timeout
        )

        self.status_dict = {
            "STS 0": "0: Awaiting warm-up.",
            "STS 1": "1: Warm-up in progress.",
            "STS 2": "2: Ready to emit X-rays.",
            "STS 3": "3: X-rays are being emitted.",
            "STS 4": "4: Overload protection activated.",
            "STS 5": "5: X-rays cannot be emitted. (Preheating, PC board defect, interlock open)",
            "STS 6": "6: Self-test in progress.",
            "XON": "X-rays are being emitted.",
            "XOF": "X-ray source is OFF."
        }

        self.preheat_status_dict = {
            "SPH 0": "0: Preheating is complete.",
            "SPH 1": "1: Preheating in progress."
        }

    def send_command(self, cmd):
        """Send a command to the x-ray source and return the response."""
        self.ser.reset_input_buffer()  # Cleans buffer to avoid reading old data
        self.ser.write((cmd + '\r').encode())
        time.sleep(0.1)  # Wait for the command to be processed
        response = self.ser.read_all().decode(errors='ignore')
        return response
    
    def xon(self):
        """Start X-ray emission."""
        return self.send_command("XON")
    
    def xoff(self):
        """Stop X-ray emission."""
        return self.send_command("XOF")
    
    def set_voltage(self, kv):
        """Set the X-ray tube voltage. Setting range is from 0 to 130."""
        return self.send_command(f"HIV {kv}")
    
    def set_current(self, ua):
        """Set the X-ray tube current. Setting range is from 0 to 300.
        *** Additional conditions apply based on the focal spot mode."""
        return self.send_command(f"CUR {ua}")
    
    def warmup(self):
        """When status is "STS 0" or "STS 2", starts the warm-up process."""
        return self.send_command("WUP")
    
    def set_focal_spot_mode(self, mode):
        """Sets the focal spot mode.
        mode = 0: small focal spot
        mode = 1: medium focal spot
        mode = 2: large focal spot
        """
        return self.send_command(f"CFS {mode}")
    
    def self_test(self):
        """When a "STS 2" is teruned in response to the "STS" command, a self test starts by sending this command. Upon sending this command, X-ray emission automatically starts and then stops after about 90 seconds. The self-test continues for about 10 seconds after stopping X-ray emission. To interrupt te self-test before it is completed, execute xoff()."""
        return self.send_command("TSF")
    
    def set_auto_off_time(self, seconds):
        """Set the time(seconds) for X-ray emission to automatically turn off if no commands are sent from the external control unit within a certain time."""
        return self.send_command(f"AST {seconds}")
    
    def overload_protection_reset(self):
        """When the overload protection is activated, the X-ray source stops emitting X-rays and the status terutns "STS 4". This method resets the overload protection."""
        return self.send_command("RST")
    
    def set_emission_mode(self, mode):
        """Sets X-ray emission mode.
        Four modes from 0 to 3 are available.
        mode = 0: Pulse mode that emits X-rays when the trigger signal is at "H", and stops X-rays when the trigger signal is at "L".
        mode = 1: Trigger mode that detects the rising edge of a trigger signal and emits X-rays only during the time specified by the set_pulse_width() method.
        mode = 2: Self-running pulse mode that alternately emits and sops X-rays at a cycle of approximately 1.67Hz, regardless of the trigger signal.
        mode = 3: Continuous mode that continuously emits X-rays regardless of the trigger signal.
        """
        return self.send_command(f"MOD {mode}")
    
    def set_pulse_width(self, ms):
        """Sets the pulse width (ms) for X-ray emission when emmision mode is set to 1 (trigger mode). The setting range is from 20 to 60000.
        This method cannot be executed during X-ray emission.
        """
        return self.send_command(f"PW {ms}")
    
    def get_status(self):
        """Status check.
        Returns the X-ray source status.
        Response is rturned with the folowing priority:
        "STS 5": X-rays cannot be emitted.
        (Preheating, PC board defect, interlock open)
        "STS 4": Overload protection activated.
        "STS 1": Warm-up in progress.
        "STS 6": Self-test in progress.
        "STS 3": X-rays are being emitted.
        "STS 0": Awaiting warm-up.
        "STS 2": Ready to emit X-rays.
        """
        return self.send_command("STS")
    
    def show_status(self, log_fn=print):
        """Print the X-ray source status in a human-readable format."""
        status = self.get_status().strip()
        log_fn(f'X-ray source status {self.status_dict.get(status, f"unknown: {status}")}')

    def get_preheat_status(self):
        """Returns the preheating status.
        "SPH 0": Preheating is complete.
        "SPH 1": Preheating in profress.
        """
        return self.send_command("SPH")
    
    def show_preheat_status(self, log_fn=print):
        """Print the preheating status in a human-readable format."""
        status = self.get_preheat_status().strip()
        log_fn(f'Preheat status {self.preheat_status_dict.get(status, f"Unknown preheat status: {status}")}')

    def batch_status_check(self):
        """Returns the X-ray source operation status at one time.
        Seven parameters are returned, including the status, output voltage, and output current from the left. The remaining four are the reserved area and show in "0 0 0 0".
        Example: If the status is "XON" and the output is 50 kV, 30uA, then the following response is returned: "SAR 3 50 30 0 0 0 0"
        """
        return self.send_command("SAR")
    
    def show_batch_status(self, log_fn=print):
        """Print the batch status in a human-readable format."""
        response = self.batch_status_check().strip()
        parts = response.split()
        if len(parts) >= 4 and parts[0] == "SAR":
            status_code = parts[1]
            voltage = parts[2]
            current = parts[3]
            status_msg = self.status_dict.get(f"STS {status_code}", f"Unknown status code: {status_code}")
            log_fn("\nX-ray source batch status:")
            log_fn('='*54)
            log_fn(f'{"Status": <33} {"Voltage": <7}      {"Current": <7}')
            log_fn('-'*54)
            log_fn(f'{str(status_msg): <33} {str(voltage) + "kV": >7}      {str(current) + "uA": >7} ')
            log_fn('='*54)
        else:
            log_fn(f'Unexpected response: {response}')

    # TODO: Implement SNR "NOT READY" batch check

    def get_voltage(self):
        """Returns the X-ray tube voltage (kV)."""
        return self.send_command("SHV")
    
    def get_current(self):
        """Returns the X-ray tube current (uA)."""
        return self.send_command("SCU")
    
    def get_preset_voltage(self):
        """Returns the preset value for the X-ray tube voltage (kV)."""
        return self.send_command("SPV")
    
    def get_preset_current(self):
        """Returns the preset value for the X-ray tube current (uA)."""
        return self.send_command("SPC")
    
    def get_presets(self):
        """Returns the preset voltage and curret values."""
        return self.send_command("SVI")
    
    def get_warmup_step(self):
        """Returns the warm-up mode and current warm-up step."""
        return self.send_command("SWS")
    
    def get_warmup_status(self):
        """Returns the warm-up status, indicating that it does not start or it is in progress or complete."""
        return self.send_command("SWE")
    
    def get_focal_spot_mode(self):
        """Returns currently selected focal spot mode.
        mode = 0: small focal spot
        mode = 1: medium focal spot
        mode = 2: large focal spot
        """
        return self.send_command("SCF")
    
    def get_interlock_status(self):
        """Returns the interlock status.
        "SIN 0": Interlock is closed.
        "SIN 1": Interlock circuit is open.
        """
        return self.send_command("SIN")

    # Commands ZTE, ZTB, ZTR for self-test are not implemented
    # Commands SAT, STM, SXT, SER, SBT, TYP, SMO, SPL are not implemented
    
    def close(self):
        """Close the serial connection."""
        self.ser.close()

if __name__ == "__main__":
    xrs = XRaySource(port='COM4')
    xrs.show_status()
    xrs.show_preheat_status()
    xrs.set_auto_off_time(15)
    xrs.set_emission_mode(3) # Continuous mode
    xrs.set_focal_spot_mode(2) # Large focal spot
    xrs.set_voltage(80) # 80 kV
    xrs.set_current(300) # 300 uA
    xrs.show_batch_status()
    xrs.show_status()
    xrs.xon()
    time.sleep(3) # Allow time for the x-ray source to stabilize
    xrs.show_batch_status()
    xrs.xoff()
    time.sleep(1)
    xrs.close()