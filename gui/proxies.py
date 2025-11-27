'''
This file contains proxy function to be used by the GUI to safely control the devices.
'''

class XRSProxy:
    def __init__(self, gui):
        self.gui = gui

    def connect(self):
        e = self.gui.init_xrs()
        if e:
            title = "X-Ray init error"
            message = f"Failed to initialize X-ray source:\n {e}
            self.gui.show_error(title, message)

    def xon(self):
        if not self.gui.xrs:
            return
        status = self.gui.xrs.get_status()
        match status:
            case "STS 0":
                self.gui.xrs.start_warmup()
                self.gui.log_msg("X-Ray source warming up...")
                self.gui.xrs_warmup_started = True
            case "STS 2":
                self.gui.xrs.xon()
                self.gui.log_msg("X-Ray source turned ON.")
                # time.sleep(0.5)  # Small delay to allow status update
            case _:
                pass

    def xoff(self):
        if not self.gui.xrs:
            return
        self.gui.xrs.xoff()
        self.gui.log_msg("X-Ray source turned OFF.")

class MotorProxy:
    def __init__(self, gui):
        self.gui = gui

    def connect(self):
        pass