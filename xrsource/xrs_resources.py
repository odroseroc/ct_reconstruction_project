import serial
import time

ser = serial.Serial(
    port='COM4', # Adjust the port as necessary
    baudrate = 38400,
    bytesize = serial.EIGHTBITS,
    parity = serial.PARITY_NONE,
    stopbits = serial.STOPBITS_ONE,
    timeout = 0.1 # Adjust as necessary
)

def xrs_command(cmd):
    """Send a command to the x-ray source and return the response."""
    ser.write((cmd + '\r').encode())
    time.sleep(0.1)  # Wait for the command to be processed
    response = ser.read_all().decode(errors='ignore')
    return response