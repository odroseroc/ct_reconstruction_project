import tkinter as tk
from tkinter import ttk


class StatusIndicators:
    """
    Administer logical flags of a device and its indicator labels.
    """

    def __init__(self, parent_frame, flags_dict, columns, tick):
        """
        parent_frame : Frame where indicators are located
        flags_dict   : dictionary {'FLAG_NAME': bool}
        columns      : number of columns in the grid
        tick         : reference to a global tick counter (for blinking)
        """
        self.parent = parent_frame
        self.flags = flags_dict
        self.columns = columns
        self.tick = tick
        self.widgets = {}  # {'FLAG_NAME': Label}
        # self.blinking = {
        #     "WARMUP": False,
        #     "X_RAY": False,
        # } # { "FLAG" : {"state":bool, "job":after_id} }

        self._build()

    # -----------------------------------------------------------
    def _build(self):
        """Build labels based on the glags dict's keys."""
        for i, key in enumerate(self.flags.keys()):
            row = i // self.columns
            col = i % self.columns

            lbl = tk.Label(
                self.parent,
                text=f" {key} ",
                bg="gray20",
                fg="white",
                width=12
            )
            lbl.grid(row=row, column=col, padx=5, pady=4)
            self.widgets[key] = lbl

    # -----------------------------------------------------------
    def update(self):
        """Update colors according to each flag."""
        for key, widget in self.widgets.items():
            value = self.flags.get(key, False)

            widget.config(bg="green" if value else "red")

    # -----------------------------------------------------------
    def reset(self):
        """Turns OFF all visual indicators."""
        for widget in self.widgets.values():
            widget.config(bg="gray20")

    # -----------------------------------------------------------
    def blink(self, key, color_on="red", color_off="green"):
        """
        Hace parpadear un indicador específico.
        key : nombre del indicador
        interval : tiempo en ms
        """
        if key not in self.widgets:
            return

        def _toggle():
            widget = self.widgets[key]
            current_bg = widget.cget("bg")
            new_bg = color_off if current_bg == color_on else color_on
            widget.config(bg=new_bg)

        if self.tick[0] % 2 == 0:
            _toggle()

    # -----------------------------------------------------------
    def stop_blink(self, key):
        """Detiene el parpadeo y devuelve el color normal según la flag."""
        if key not in self.widgets:
            return

        # restaurar color según flag
        val = self.flags.get(key, False)
        self.widgets[key].config(bg="green" if val else "red")