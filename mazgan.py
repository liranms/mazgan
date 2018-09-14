import glob
import os
import re
import sys
from options import *

R = re.compile(r"(pulse|space) (\d+)")

RANGES = {
    (600, 800): 1,
    (1600, 1800): 0,
    (3900, 4300): 2,
    (7900, 8200): 3,
    (1801, 2000): 4,
    (10000, sys.maxint): 9
}
PULSE_SPACE = {"pulse": "=", "space": "-"}


def decode_mode2_output(inp):
    values = []
    pulsespace = []
    for line in inp:
        line = line.strip()
        r = re.findall(r"(pulse|space) (\d+)", line)
        if r:
            r = r[0]
            ps = PULSE_SPACE.get(r[0], "?")
            n = int(r[1])
            found = False
            for ((l, h), v) in RANGES.iteritems():
                if n < h and n > l:
                    n = v
                    found = True
                    break
            if not found:
                n = "?" + str(n) + "?"
            values.append(n)
            pulsespace.append(ps)
    return (values, pulsespace)


def load_files(where="."):
    r = {}
    for i in os.listdir(where):
        r[i] = decode_mode2_output(open(i, "r"))
    return r


def to_csv():
    for i in glob.glob("input/*"):
        with open(i + ".csv", "w") as fout:
            fout.write(i + "\n")
            with open(i, "r") as fin:
                for tpl in decode_mode2_output(fin):
                    fout.write("%s,%d" % tpl)
                    fout.write("\n")


def pretty(arr):
    s = ""
    x = 0
    b = 0
    for i in arr:
        s += str(i)
        x += 1
        if (i == 0 or i == 1):
            b = b * 2 + i
        if (i != 0 and i != 1) or x >= 8:
            s += " (%03d) " % (b,)
            x = 0
            b = 0
    return s


def decode(arr):
    out = []
    i = 0
    while i < len(arr) - 1:
        bit = arr[i]
        if bit != 0 and bit != 1:
            out.append(bit)
        else:
            i += 1
            if bit == 0 and arr[i] == 1:
                out.append(1)
            elif bit == 1 and arr[i] == 0:
                out.append(0)
            else:
                raise Exception()
        i += 1
    return out


def reverse_bits(arr):
    out = []
    byte = []
    for bit in arr:
        if bit != 0 and bit != 1:
            out.append(bit)
        else:
            byte.append(bit)
            if len(byte) == 8:
                byte.reverse()
                out += byte
                byte = []
    byte.reverse()
    out += byte
    return out


def to_single_csv():
    for fname in glob.glob("input/*"):
        with open(fname, "r") as fin:
            (values, pulse) = decode_mode2_output(fin)
            print "%-030s: %s" % (fname, pretty(reverse_bits(decode(values))))
        # print "%-012s: %s" % (fname, pretty(pulse))





class Mazgan(object):
    """
    8 bytes
    struct cmd {                             byte     <=> reversed
        0   byte        = 0x00000001            (00000001 <=> 10000000)
        8   half-byte  	= mode: cool = 	  1     (    0001 <=>     1000)
                                heat =    2     (    0010 <=>     0100)
                                defrost = 4     (    0100 <=>     0010)
                                auto =    5     (    0101 <=>     1010)
        12  half-byte   = fan:  low =     1     (    0001 <=>     1000)
                                med =     2     (    0010 <=>     0100)
                                high =    3     (    0011 <=>     1100)
                                auto =    4     (    0100 <=>     0010)
        16  byte        = temp  001XXXX0, 0x20 -> 0x3c
                                            32 -> 60
                                            16c -> 30c, jumps of 0x2
                                        temp(c) = 32 + (c - 16) * 2   [ 16 <= c <= 30 ]
        24  byte        = 0x00000000
        32  byte        = 0x00000000
        40  half-byte   = energy: auto  = 0x0     ( 0000 <=>   0000)
                                  night = 0x1     ( 0001 <=>   0001)
                                  none =  0x2     ( 0011 <=>   0011)
        40  half-byte   = on/off: on = 0x30       ( 0011 <=>   1100)
                                 off = 0xc0       ( 1100 <=>   0011)
        48  byte        = 0x00000000 or 0x00000011
        56  byte		= sum(half-bytes)

    }

    reversed bits:

    input\off                     : 9 3 2 10000000 1000 1100 01110100 00000000 00000000 00000011 00000000 10000100 4
    input\23_auto_mode            : 9 3 2 10000000 1010 0010 01110100 00000000 00000000 00001100 00000011 10010100 4
    input\30                      : 9 3 2 10000000 1000 0010 00111100 00000000 00000000 00001100 00000000 00011000 4
                                                   m ?? fan?  temp                      enrg ono          sum
                                                   o                                           f
                                                   d                                           f
                                                   e

    """

    def __init__(self, temperature, mode=Mode.auto, fan=Fan.auto, energy=Energy.auto, state=State.on):
        self._temp = temperature
        self._mode = mode
        self._fan = fan
        self._energy = energy
        self._state = state

    def _make_temperature(self, desired_temp):
        return 32 + (desired_temp - 16) * 2

    @staticmethod
    def _byte_to_bin(n, reverse=False):
        return '{0:08b}'.format(n)[::-1 if reverse else 1]

    @staticmethod
    def two_words_to_byte(n, m):
        return (n << 4) | m

    @staticmethod
    def _calc_checksum(arr):
        s = 0
        for i in arr:
            s += (i >> 4) + (i & 0b1111)
        return s

    def build_binary(self):
        result = [
            1,
            self.two_words_to_byte(self._fan.value, self._mode.value),
            self._make_temperature(self._temp),
            0,
            0,
            self.two_words_to_byte(self._state.value, self._energy.value),
            0
        ]
        checksum = self._calc_checksum(result)
        result.append(checksum)
        return result

    def to_str(self, delim=" ", reverse=False):
        arr = self.build_binary()
        return delim.join(self._byte_to_bin(i, reverse) for i in arr)

    def make_name(self):
        return make_name(self._state, self._temp, self._fan, self._energy, self._mode)

    @staticmethod
    def _bit_to_lirc(bit):
        if bit:
            return [1700, 700]  ##   ______---   (1700, 700)  01  => 1
        else:
            return [700, 1700]  ##    ___------  (700, 1700)  10  => 0

    @staticmethod
    def flatten(l):
        return [item for sublist in l for item in sublist]

    def pretty_lirc(self, codes, pretty):
        s = ""
        if pretty:
            for (i, code) in enumerate(codes):
                if i % 6 == 0:
                    s += "\n"
                s += " %8d" % (code,)
        else:
            s = " ".join(str(i) for i in codes)
        return "name %s\n%s\n\n" % (self.make_name(), s)

    def to_lirc(self, pretty=False):
        s = self.to_str(delim="", reverse=True)
        codes = self.flatten([self._bit_to_lirc(int(i)) for i in s])
        header = [8000, 4000] # pulse, space
        footer = [1800] # pulse
        space = [25000] # space
        # Write it twice
        final_codes = (header + codes + footer) + space + (header + codes + footer)
        return self.pretty_lirc(final_codes, pretty)


def all_options():
    result = [Mazgan(23, state=State.off)]
    for temp in range(16, 31):
        for mode in Mode:
            for fan in Fan:
                for energy in Energy:
                    result.append(Mazgan(temp, mode, fan, energy))
    return result

def create_lirc(remote_name, filename=None):
    if filename is None:
        filename = remote_name + ".conf"
    with open(filename, "w") as f:
        f.write("""
begin remote

name %s
flags RAW_CODES
eps 30
aeps 100

gap 91000

begin raw_codes

""" % (remote_name,))
        for i in all_options():
            f.write(i.to_lirc(pretty=True))
        f.write("end raw_codes\nend remote")

if __name__ == "__main__":
    create_lirc(REMOTE_NAME, "/etc/lirc/%s.conf" % (REMOTE_NAME,))

