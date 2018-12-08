import time
import board
import busio
import ure
import gc

from digitalio import DigitalInOut, Direction, Pull
import adafruit_miniesptool

print("ESP mini prog")

uart = busio.UART(board.TX, board.RX, baudrate=115200, timeout=1)
resetpin = DigitalInOut(board.D3)
gpio0pin = DigitalInOut(board.D2)
esptool = adafruit_miniesptool.miniesptool(uart, gpio0pin, resetpin, 912600)

esptool.debug = False
esptool.sync()
print("Synced")
print(esptool.chip_name)
print("MAC ADDR: ",[hex(i) for i in esptool.mac_addr])
esptool.flash_file("AT firmware 1.6.2.0.bin")
esptool.reset()
time.sleep(0.5)
