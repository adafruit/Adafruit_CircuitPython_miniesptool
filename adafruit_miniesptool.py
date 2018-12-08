import time
import struct
from digitalio import DigitalInOut, Direction, Pull


SYNC_PACKET = b'\x07\x07\x12 UUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUU'

class miniesptool:

    def __init__(self, uart, gpio0_pin, reset_pin):
        gpio0_pin.direction = Direction.OUTPUT
        reset_pin.direction = Direction.OUTPUT
        self._gpio0pin = gpio0_pin
        self._resetpin = reset_pin
        self._uart = uart
        self._uart.baudrate = 115200
        self._debug = False

    @property
    def debug(self):
        return self._debug

    @debug.setter
    def debug(self, f):
        self._debug = f

    @property
    def mac_addr(self):
        reg1 = self.read_register(0x3FF00050)
        reg2 = self.read_register(0x3FF00054)
        reg3 = self.read_register(0x3FF00058)
        reg4 = self.read_register(0x3FF0005C)
        
        mac_addr = [0] * 6
        mac_addr[0] = (reg4>>16) & 0xff
        mac_addr[1] = (reg4>>8) & 0xff
        mac_addr[2] = reg4 & 0xff
        mac_addr[3] = (reg2>>8) & 0xff
        mac_addr[4] = reg2 & 0xff
        mac_addr[5] = (reg1>>24) & 0xff
        return mac_addr

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
        self.send_command(0x0A, packet)
        reply, register = self.get_response(0x0A)
        if not reply:
            raise RuntimeError("Failed to read register")
        if len(reply) != 2 or reply[0] != 0 or reply[1] != 0:
            raise RuntimeError("Failed to read register")
        return struct.unpack('I', bytearray(register))[0]

    def reset(self):
        print("Resetting")
        self._gpio0pin.value = False
        self._resetpin.value = False
        time.sleep(0.01)
        self._resetpin.value = True
        time.sleep(0.1)

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
