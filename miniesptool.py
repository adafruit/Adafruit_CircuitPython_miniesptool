import time
import board
import busio
import struct
from digitalio import DigitalInOut, Direction, Pull
import gc

print(gc.mem_free())

uart = busio.UART(board.TX, board.RX, baudrate=115200, timeout=1)
print("ESP mini prog")

gpio0pin = DigitalInOut(board.D2)
gpio0pin.direction = Direction.OUTPUT
resetpin = DigitalInOut(board.D3)
resetpin.direction = Direction.OUTPUT

SYNC_PACKET = b'\x07\x07\x12 UUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUU'

def escape(buffer):
    return buffer
def unescape(buffer):
    return buffer

def send_command(opcode, buffer):
    uart.reset_input_buffer()
    
    checksum = 0
    if opcode == 0x03:
        checksum = 0xef
        for i in range(16, len(buffer)):
            checksum ^= buffer[i]

    packet = [0xC0, 0x00] # start byte and direction
    packet.append(opcode)
    packet += [x for x in struct.pack('H', len(buffer))]
    packet += [x for x in escape(struct.pack('I', checksum))]
    packet += [x for x in escape(buffer)]
    packet.append(0xC0)
    print([hex(x) for x in packet])
    print("Writing:", bytearray(packet))
    uart.write(bytearray(packet))

def get_response(opcode, timeout=0.1):
    reply = []
    
    stamp = time.monotonic()
    packet_length = 0
    while (time.monotonic() - stamp) < timeout:
        if uart.in_waiting > 0:
            c = uart.read(1)
            reply += c
        if len(reply) > 0 and reply[0] != 0xc0:
            # packets must start with 0xC0
            del(reply[0])
        if len(reply) > 1 and reply[1] != 0x01:
            del(reply[0])
        if len(reply) > 2 and reply[2] != opcode:
            del(reply[0])
        if len(reply) > 4:
            # get the length
            packet_length = reply[3] + (reply[4] << 8)
        if len(reply) == packet_length + 10:
            break
    else:
        return (None, None)
    print("Packet:", [hex(i) for i in reply])
    print("Reading:", bytearray(reply))
    register = reply[5:9]
    response = reply[9:-1]
    print("Response:", [hex(i) for i in response], "Register:", [hex(i) for i in register])
    return (response, register)

def sync():
    send_command(0x08, SYNC_PACKET)
    result = []
    for _ in range(8):
        reply, register = get_response(0x08, 0.1)
        if not reply:
            continue
        if len(reply) > 1 and reply[0] == 0 and reply[1] == 0:
            return True
    return False

def read_register(reg):
    packet = struct.pack('I', reg)
    send_command(0x0A, packet)
    reply, register = get_response(0x0A)
    if not reply:
        raise RuntimeError("Failed to read register")
    if len(reply) != 2 or reply[0] != 0 or reply[1] != 0:
        raise RuntimeError("Failed to read register")
    return struct.unpack('I', bytearray(register))[0]

def md5_flash(offset, size):
    packet = struct.pack('IIII', offset, size, 0x0, 0x0)
    print(packet)
    
print("Resetting")
gpio0pin.value = False
resetpin.value = False
time.sleep(0.01)
resetpin.value = True
time.sleep(0.1)

for _ in range(3):
    if sync():
        break
    time.sleep(0.1)
else:
    print("Couldn't sync")

print("Synced")
time.sleep(0.1)

reg1 = read_register(0x3FF00050)
reg2 = read_register(0x3FF00054)
reg3 = read_register(0x3FF00058)
reg4 = read_register(0x3FF0005C)

mac_addr = [0] * 6
mac_addr[0] = (reg4>>16) & 0xff
mac_addr[1] = (reg4>>8) & 0xff
mac_addr[2] = reg4 & 0xff
mac_addr[3] = (reg2>>8) & 0xff
mac_addr[4] = reg2 & 0xff
mac_addr[5] = (reg1>>24) & 0xff
print("MAC ADDR: ",[hex(i) for i in mac_addr])
# 5c:cf:7f:fe:81:1f
"""
chip_id = [0] * 4
chip_id[0] = (reg2 >> 16) & 0xff
chip_id[1] = (reg2 >> 8) & 0xff
chip_id[2] = reg2 & 0xff
chip_id[3] = (reg1>>24) & 0xff
print("CHIP ID:", [hex(i) for i in chip_id])
# Chip ID: 0x00fe811f
"""

gpio0pin.direction = Direction.INPUT
resetpin.direction = Direction.INPUT


while True:
    time.sleep(1)
    pass