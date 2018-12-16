# The MIT License (MIT)
#
# Copyright (c) 2018 ladyada for Adafruit Industries
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
"""
`adafruit_miniesptool`
====================================================

ROM loader for ESP chips, works with ESP8266 or ESP32.
This is a 'no-stub' loader, so you can't read MD5 or firmware back on ESP8266.

See this document for protocol we're implementing: 
https://github.com/espressif/esptool/wiki/Serial-Protocol

See this for the 'original' code we're miniaturizing: 
https://github.com/espressif/esptool/blob/master/esptool.py

There's a very basic Arduino ROM loader here for ESP32:
https://github.com/arduino-libraries/WiFiNINA/tree/master/examples/Tools/FirmwareUpdater

* Author(s): ladyada

Implementation Notes
--------------------

**Hardware:**

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases


"""

import os
import time
import struct
import board
from digitalio import DigitalInOut, Direction, Pull

__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_miniesptool.git"

SYNC_PACKET = b'\x07\x07\x12 UUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUU'
ESP32_DATAREGVALUE = 0x15122500
ESP8266_DATAREGVALUE = 0x00062000

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
ESP_SPI_SET_PARAMS  = 0x0b
ESP_SPI_ATTACH  = 0x0d
ESP_CHANGE_BAUDRATE = 0x0f
ESP_SPI_FLASH_MD5   = 0x13
ESP_CHECKSUM_MAGIC = 0xef

ESP8266 = 0x8266
ESP32 = 0x32

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

    def __init__(self, uart, gpio0_pin, reset_pin, flashsize, baudrate=ESP_ROM_BAUD):
        gpio0_pin.direction = Direction.OUTPUT
        reset_pin.direction = Direction.OUTPUT
        self._gpio0pin = gpio0_pin
        self._resetpin = reset_pin
        self._uart = uart
        self._uart.baudrate = baudrate
        self._debug = False
        self._efuses = [0] * 4
        self._chipfamily = None
        self._chipname = None
        self._flashsize = flashsize
        #self._debug_led = DigitalInOut(board.D13)
        #self._debug_led.direction = Direction.OUTPUT

    @property
    def debug(self):
        return self._debug

    @debug.setter
    def debug(self, f):
        self._debug = f

    @property
    def baudrate(self):
        return self._uart.baudrate

    @baudrate.setter
    def baudrate(self, baud):
        if self._chipfamily == ESP8266:
            raise NotImplementedError("Baud rate can only change on ESP32")
        buffer = struct.pack('<II', baud, 0)
        self.check_command(ESP_CHANGE_BAUDRATE, buffer)
        self._uart.baudrate = baud
        time.sleep(0.05)
        self._uart.reset_input_buffer()
        self.check_command(ESP_CHANGE_BAUDRATE, buffer)

    def md5(self, offset, size):
        if self._chipfamily == ESP8266:
            raise NotImplementedError("MD5 only supported on ESP32")
        self.check_command(ESP_SPI_ATTACH, bytes([0] * 8))
        buffer = struct.pack('<IIII', offset, size, 0, 0)
        md5 = self.check_command(ESP_SPI_FLASH_MD5, buffer, timeout=2)[1]
        return ''.join([chr(i) for i in md5])

    @property
    def mac_addr(self):
        self.read_efuses()
        mac_addr = [0] * 6
        if self._chipfamily == ESP8266:
            mac_addr[0] = (self._efuses[3]>>16) & 0xff
            mac_addr[1] = (self._efuses[3]>>8) & 0xff
            mac_addr[2] = self._efuses[3] & 0xff
            mac_addr[3] = (self._efuses[1]>>8) & 0xff
            mac_addr[4] = self._efuses[1] & 0xff
            mac_addr[5] = (self._efuses[0]>>24) & 0xff
        if self._chipfamily == ESP32:
            mac_addr[0] = self._efuses[2] >> 8 & 0xFF
            mac_addr[1] = self._efuses[2] & 0xFF
            mac_addr[2] = self._efuses[1] >> 24 & 0xFF
            mac_addr[3] = self._efuses[1] >> 16 & 0xFF
            mac_addr[4] = self._efuses[1] >> 8 & 0xFF
            mac_addr[5] = self._efuses[1] & 0xFF
        return mac_addr

    @property
    def chip_type(self):
        if not self._chipfamily:
            datareg = self.read_register(0x60000078)
            if datareg == ESP32_DATAREGVALUE:
                self._chipfamily = ESP32
            elif datareg == ESP8266_DATAREGVALUE:
                self._chipfamily = ESP8266
            else:
                raise RuntimeError("Unknown Chip")
        return self._chipfamily

    @property
    def chip_name(self):
        self.chip_type
        self.read_efuses()

        if self.chip_type == ESP32:
            return "ESP32"
        elif self.chip_type == ESP8266:
            if self._efuses[0] & (1 << 4) or self._efuses[2] & (1 << 16):
                return "ESP8285"
            else:
                return "ESP8266EX"

    def read_efuses(self):
        if self._chipfamily == ESP8266:
            base_addr = 0x3FF00050
        elif self._chipfamily == ESP32:
            base_addr = 0x6001a000
        else:
            raise RuntimeError("Don't know what chip this is")
        for i in range(4):
            self._efuses[i] = self.read_register(base_addr + 4*i)

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

    def flash_begin(self, *, size=0, offset=0):
        if self._chipfamily == ESP32:
            self.check_command(ESP_SPI_ATTACH, bytes([0] * 8))
            buffer = struct.pack('<IIIIII', 0, self._flashsize, 0x10000, 4096, 256, 0xFFFF)
            self.check_command(ESP_SPI_SET_PARAMS, buffer)

        num_blocks = (size + self.FLASH_WRITE_SIZE - 1) // self.FLASH_WRITE_SIZE
        if self._chipfamily == ESP8266:
            erase_size = self.get_erase_size(offset, size)
        else:
            erase_size = size
        timeout = 5
        t = time.monotonic()
        buffer = struct.pack('<IIII', erase_size, num_blocks, self.FLASH_WRITE_SIZE, offset)
        print("***erase size %d, num_blocks %d, size %d, offset 0x%04x" %  (erase_size, num_blocks, self.FLASH_WRITE_SIZE, offset))

        self.check_command(ESP_FLASH_BEGIN, buffer, timeout=timeout)
        if size != 0:
            print("Took %.2fs to erase %d flash blocks" % (time.monotonic() - t, num_blocks))
        return num_blocks

    def check_command(self, opcode, buffer, checksum=0, timeout=0.1):
        self.send_command(opcode, buffer)
        value, data = self.get_response(opcode, timeout)
        if self._chipfamily == ESP8266:
            status_len = 2
        else:
            status_len = 4
        if len(data) < status_len:
            raise RuntimeError("Didn't get enough status bytes")
        status = data[-status_len:]
        data = data[:-status_len]
        #print("status", status)
        #print("value", value)
        #print("data", data)
        if status[0] != 0:
            raise RuntimeError("Command failure error code 0x%02x" % status[1])
        return (value, data)

    def send_command(self, opcode, buffer):
        self._uart.reset_input_buffer()

        #self._debug_led.value = True
        checksum = 0
        if opcode == 0x03:
            checksum = self.checksum(buffer[16:])
        #self._debug_led.value = False

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
        value = reply[5:9]
        data = reply[9:-1]
        if self._debug:
            print("value:", [hex(i) for i in value],
                  "data:", [hex(i) for i in data])
        return (value, data)

    def read_register(self, reg):
        if self._debug:
            print("Reading register 0x%08x" % reg)
        packet = struct.pack('I', reg)
        register = self.check_command(ESP_READ_REG, packet)[0]
        return struct.unpack('I', bytearray(register))[0]

    def reset(self, program_mode=False):
        print("Resetting")
        self._gpio0pin.value = not program_mode
        self._resetpin.value = False
        time.sleep(0.1)
        self._resetpin.value = True
        time.sleep(0.2)

    def flash_block(self, data, seq, timeout=0.1):
        self.check_command(ESP_FLASH_DATA,
                           struct.pack('<IIII', len(data), seq, 0, 0) + data,
                           self.checksum(data),
                           timeout=timeout)

    def flash_file(self, filename, offset=0, md5=None):
        filesize = os.stat(filename)[6]
        with open(filename, "rb") as f:
            print("\nWriting", filename, "w/filesize:", filesize)
            blocks = self.flash_begin(size=filesize, offset=offset)
            seq = 0
            written = 0
            address = offset
            t = time.monotonic()
            while filesize - f.tell() > 0:
                print('\rWriting at 0x%08x... (%d %%)' %
                      (address + seq * self.FLASH_WRITE_SIZE, 100 * (seq + 1) // blocks), end='')
                block = f.read(self.FLASH_WRITE_SIZE)
                # Pad the last block
                block = block + b'\xff' * (self.FLASH_WRITE_SIZE - len(block))
                #print(block)
                self.flash_block(block, seq, timeout=2)
                seq += 1
                written += len(block)
            print("Took %.2fs to write %d bytes" % (time.monotonic() - t, filesize))
            if md5:
                print("Verifying MD5sum ", md5)
                calcd = self.md5(offset, filesize)
                if md5 != calcd:
                    raise RuntimeError("MD5 mismatch, calculated:", calcd)

    def _sync(self):
        self.send_command(0x08, SYNC_PACKET)
        result = []
        for _ in range(8):
            value, data = self.get_response(0x08, 0.1)
            if not data:
                continue
            if len(data) > 1 and data[0] == 0 and data[1] == 0:
                return True
        return False

    def sync(self):
        self.reset(True)

        for _ in range(3):
            if self._sync():
                time.sleep(0.1)
                return True
            time.sleep(0.1)
        else:
            raise RuntimeError("Couldn't sync to ESP")

    @staticmethod
    def checksum(data, state=ESP_CHECKSUM_MAGIC):
        """ Calculate checksum of a blob, as it is defined by the ROM """
        for b in data:
            state ^= b
        return state

    @staticmethod
    def slip_encode(buffer):
        encoded = []
        for b in buffer:
            if b == 0xdb:
                encoded += [0xdb, 0xdd]
            elif b == 0xc0:
                encoded += [0xdb, 0xdc]
            else:
                encoded += [b]
        return bytearray(encoded)
