import time
import board
import busio

from digitalio import DigitalInOut, Direction, Pull
from adafruit_miniesptool import adafruit_miniesptool

print("ESP32 mini prog")

uart = busio.UART(board.TX, board.RX, baudrate=115200, timeout=1)
resetpin = DigitalInOut(board.D3)
gpio0pin = DigitalInOut(board.D2)
esptool = adafruit_miniesptool.miniesptool(uart, gpio0pin, resetpin,
                                           flashsize=4*1024*1024)

esptool.debug = False

esptool.sync()
print("Synced")
print("Found:", esptool.chip_name)
if esptool.chip_name != "ESP32":
    raise RuntimeError("This example is for ESP32 only")
esptool.baudrate = 912600
print("MAC ADDR: ", [hex(i) for i in esptool.mac_addr])

esptool.flash_file("esp32/bootloader/bootloader.bin", 0x1000,
                   '4035b2317251ecb51894a02802c1912d') # 0x1000 bootloader/bootloader.bin
esptool.flash_file("esp32/at_customize.bin", 0x20000,
                   '652ab545a6c93a51a8b21a347452c6ca') # 0x20000 at_customize.bin
esptool.flash_file("esp32/customized_partitions/ble_data.bin", 0x21000,
                   'e941cc7c66f3a4caedf2981604fc5bbf') # 0x21000 customized_partitions/ble_data.bin
esptool.flash_file("esp32/customized_partitions/server_cert.bin", 0x24000,
                   '766fa1e87aabb9ab78ff4023f6feb4d3') # 0x24000 customized_partitions/server_cert.bin
esptool.flash_file("esp32/customized_partitions/server_key.bin", 0x26000,
                   '05da7907776c3d5160f26bf870592459') # 0x26000 customized_partitions/server_key.bin
esptool.flash_file("esp32/customized_partitions/server_ca.bin", 0x28000,
                   'e0169f36f9cb09c6705343792d353c0a')  # 0x28000 customized_partitions/server_ca.bin
esptool.flash_file("esp32/customized_partitions/client_cert.bin", 0x2a000,
                   '428ed3bae5d58b721b8254cbeb8004ff')  # 0x2a000 customized_partitions/client_cert.bin
esptool.flash_file("esp32/customized_partitions/client_key.bin", 0x2c000,
                   '136f563811930a5d3bf04c946f430ced')  # 0x2c000 customized_partitions/client_key.bin
esptool.flash_file("esp32/customized_partitions/client_ca.bin", 0x2e000,
                   '25ab638695819daae67bcd8a4bfc5626')  # 0x2e000 customized_partitions/client_ca.bin
esptool.flash_file("esp32/phy_init_data.bin", 0xf000,
                   'bc9854aa3687ca73e25d213d20113b23')  #  0xf000 phy_init_data.bin
esptool.flash_file("esp32/esp-at.bin", 0x100000,
                   '02e9c4af9480387644c7e45f7f8b9c0a')  # 0x100000 esp-at.bin
esptool.flash_file("esp32/partitions_at.bin", 0x8000,
                   '76bc3722dae4b1f2e66c9f5649b31e02')  # 0x8000 partitions_at.bin
esptool.reset()
time.sleep(0.5)
