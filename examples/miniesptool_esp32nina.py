import time
import board
import busio
from digitalio import DigitalInOut, Direction # pylint: disable=unused-import
import adafruit_miniesptool

print("ESP32 Nina-FW")

uart = busio.UART(board.TX, board.RX, baudrate=115200, timeout=1)
resetpin = DigitalInOut(board.D5)
gpio0pin = DigitalInOut(board.D6)

esptool = adafruit_miniesptool.miniesptool(uart, gpio0pin, resetpin,
                                           flashsize=4*1024*1024)
esptool.sync()

print("Synced")
print("Found:", esptool.chip_name)
if esptool.chip_name != "ESP32":
    raise RuntimeError("This example is for ESP32 only")
esptool.baudrate = 912600
print("MAC ADDR: ", [hex(i) for i in esptool.mac_addr])

# Note: Make sure to use the LATEST nina-fw binary release!
esptool.flash_file("NINA_W102-1.3.1.bin",0x0,'3f9d2765dd3b7b1eab61e1eccae73e44')

esptool.reset()
time.sleep(0.5)
