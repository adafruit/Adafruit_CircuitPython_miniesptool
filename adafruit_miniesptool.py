import time
import os
import struct
from digitalio import DigitalInOut, Direction, Pull


SYNC_PACKET = b'\x07\x07\x12 UUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUU'

# Commands supported by ESP8266 ROM bootloader
ESP_FLASH_BEGIN = 0x02
ESP_FLASH_DATA  = 0x03
ESP_FLASH_END   = 0x04
ESP_MEM_BEGIN   = 0x05
ESP_MEM_END     = 0x06
ESP_MEM_DATA    = 0x07
ESP_SYNC        = 0x08
ESP_WRITE_REG   = 0x09
ESP_READ_REG    = 0x0a

FLASH_SIZES = {
    '512KB':0x00,
    '256KB':0x10,
    '1MB':0x20,
    '2MB':0x30,
    '4MB':0x40,
    '2MB-c1': 0x50,
    '4MB-c1':0x60,
    '8MB':0x80,
    '16MB':0x90,
}

class miniesptool:
    FLASH_WRITE_SIZE = 0x400
    FLASH_SECTOR_SIZE = 0x1000 # Flash sector size, minimum unit of erase.
    ESP_ROM_BAUD = 115200

    def __init__(self, uart, gpio0_pin, reset_pin):
        gpio0_pin.direction = Direction.OUTPUT
        reset_pin.direction = Direction.OUTPUT
        self._gpio0pin = gpio0_pin
        self._resetpin = reset_pin
        self._uart = uart
        self._uart.baudrate = self.ESP_ROM_BAUD
        self._debug = False
        self._efuses = [0] * 4

    @property
    def debug(self):
        return self._debug

    @debug.setter
    def debug(self, f):
        self._debug = f

    @property
    def mac_addr(self):
        self.read_efuses()
        mac_addr = [0] * 6
        mac_addr[0] = (self._efuses[3]>>16) & 0xff
        mac_addr[1] = (self._efuses[3]>>8) & 0xff
        mac_addr[2] = self._efuses[3] & 0xff
        mac_addr[3] = (self._efuses[1]>>8) & 0xff
        mac_addr[4] = self._efuses[1] & 0xff
        mac_addr[5] = (self._efuses[0]>>24) & 0xff
        return mac_addr

    @property
    def chip_name(self):
        self.read_efuses()
        if self._efuses[0] & (1 << 4) or self._efuses[2] & (1 << 16):
            return "ESP8285"
        else:
            return "ESP8266EX"

    def read_efuses(self):
        self._efuses[0] = self.read_register(0x3FF00050)
        self._efuses[1] = self.read_register(0x3FF00054)
        self._efuses[2] = self.read_register(0x3FF00058)
        self._efuses[3] = self.read_register(0x3FF0005C)

    def get_erase_size(self, offset, size):
        """ Calculate an erase size given a specific size in bytes.
        Provides a workaround for the bootloader erase bug."""

        sectors_per_block = 16
        sector_size = self.FLASH_SECTOR_SIZE
        num_sectors = (size + sector_size - 1) // sector_size
        start_sector = offset // sector_size

        head_sectors = sectors_per_block - (start_sector % sectors_per_block)
        if num_sectors < head_sectors:
            head_sectors = num_sectors

        if num_sectors < 2 * head_sectors:
            return (num_sectors + 1) // 2 * sector_size
        else:
            return (num_sectors - head_sectors) * sector_size

    def flash_begin(self, size=0, offset=0):
        num_blocks = (size + self.FLASH_WRITE_SIZE - 1) // self.FLASH_WRITE_SIZE
        erase_size = self.get_erase_size(offset, size)

        timeout = 5
        t = time.monotonic()
        buffer = struct.pack('<IIII', erase_size, num_blocks, self.FLASH_WRITE_SIZE, offset)
        self.check_command(ESP_FLASH_BEGIN, buffer, timeout=timeout)
        if size != 0:
            print("Took %.2fs to erase %d flash blocks" % (time.monotonic() - t, num_blocks))
        return num_blocks

    def check_command(self, opcode, buffer, timeout=0.1):
        self.send_command(opcode, buffer)
        status, data = self.get_response(opcode, timeout)
        if len(status) != 2:
            raise RuntimeError("Didn't get 2 status bytes")
        if status[0] != 0:
            raise RuntimeError("Command failure error code 0x%02x" % status[1])
        return data

    def send_command(self, opcode, buffer):
        self._uart.reset_input_buffer()

        checksum = 0
        if opcode == 0x03:
            checksum = 0xef
            for i in range(16, len(buffer)):
                checksum ^= buffer[i]

        packet = [0xC0, 0x00] # direction
        packet.append(opcode)
        packet += [x for x in struct.pack('H', len(buffer))]
        packet += [x for x in self.slip_encode(struct.pack('I', checksum))]
        packet += [x for x in self.slip_encode(buffer)]
        packet += [0xC0]
        if self._debug:
            print([hex(x) for x in packet])
            print("Writing:", bytearray(packet))
        self._uart.write(bytearray(packet))

    def get_response(self, opcode, timeout=0.1):
        reply = []

        stamp = time.monotonic()
        packet_length = 0
        escaped_byte = False
        while (time.monotonic() - stamp) < timeout:
            if self._uart.in_waiting > 0:
                c = self._uart.read(1)
                if c == b'\xDB':
                    escaped_byte = True
                elif escaped_byte:
                    if c == b'\xDD':
                        reply += b'\xDC'
                    elif c == b'\xDC':
                        reply += b'\xC0'
                    else:
                        reply += [0xDB, c]
                    escaped_byte = False
                else:
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
        if self._debug:
            print("Packet:", [hex(i) for i in reply])
            print("Reading:", bytearray(reply))
        register = reply[5:9]
        response = reply[9:-1]
        if self._debug:
            print("Response:", [hex(i) for i in response],
                  "Register:", [hex(i) for i in register])
        return (response, register)

    def read_register(self, reg):
        packet = struct.pack('I', reg)
        register = self.check_command(ESP_READ_REG, packet)
        return struct.unpack('I', bytearray(register))[0]

    def reset(self):
        print("Resetting")
        self._gpio0pin.value = False
        self._resetpin.value = False
        time.sleep(0.01)
        self._resetpin.value = True
        time.sleep(0.1)

    def flash_file(self, filename):
        size = os.stat(filename)[6]
        with open(filename, "rb") as f:
            print("Writing", filename, "w/filesize:", size)
            self.flash_begin(size, 0)



    def _sync(self):
        self.send_command(0x08, SYNC_PACKET)
        result = []
        for _ in range(8):
            reply, register = self.get_response(0x08, 0.1)
            if not reply:
                continue
            if len(reply) > 1 and reply[0] == 0 and reply[1] == 0:
                return True
        return False

    def sync(self):
        self.reset()

        for _ in range(3):
            if self._sync():
                time.sleep(0.1)
                return True
            time.sleep(0.1)
        else:
            raise RuntimeError("Couldn't sync to ESP")

    def slip_encode(self, buffer):
        encoded = []
        for b in buffer:
            if b == 0xdb:
                encoded += [0xdb, 0xdd]
            elif b == 0xc0:
                encoded += [0xdb, 0xdc]
            else:
                encoded += [b]
        return bytearray(encoded)
