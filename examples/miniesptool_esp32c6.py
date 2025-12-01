# SPDX-FileCopyrightText: 2025 Brent Rubell for Adafruit Industries
# SPDX-License-Identifier: MIT
import time

import board
import busio
from digitalio import DigitalInOut, Direction

import adafruit_miniesptool

print("ESP32-C6 Nina-FW Loader")

# Adafruit FruitJam (ESP32-C6) Configuration
tx = board.ESP_TX
rx = board.ESP_RX
resetpin = board.ESP_RESET
gpio0pin = board.I2S_IRQ

uart = busio.UART(tx, rx, baudrate=115200, timeout=1)
esptool = adafruit_miniesptool.miniesptool(
    uart, DigitalInOut(gpio0pin), DigitalInOut(resetpin), flashsize=4 * 1024 * 1024
)
esptool.sync()

print("Synced")
print("Found:", esptool.chip_name)
if esptool.chip_name != "ESP32-C6":
    raise RuntimeError("This example is for ESP32-C6 only")

esptool.baudrate = 912600
print("MAC ADDR: ", [hex(i) for i in esptool.mac_addr])

# NOTE: Make sure to use the LATEST ninafw binary release and
# rename it to ninafw.bin (or change the filename below)!
esptool.flash_file("ninafw.bin", 0x0)

print("Done flashing, resetting..")
esptool.reset()
time.sleep(0.5)
