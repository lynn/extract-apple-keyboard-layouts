from typing import *
from dataclasses import dataclass
import sys

@dataclass
class M2t:
    default: int
    tables: List[int]
    def __repr__(self):
        return f"M2t(...)"

    def parse(m2t: memoryview):
        u16 = lambda i: int.from_bytes(m2t[i:i+2], byteorder="little")
        u32 = lambda i: int.from_bytes(m2t[i:i+4], byteorder="little")
        fmt, default = u16(0), u16(2)
        n = u32(4)
        return M2t(default, list(m2t[8:8+n]))

@dataclass
class K2c:
    n_codes: int
    tables: List[List[int]]
    def __repr__(self):
        return f"K2c(...)"

    def parse(k2c: memoryview):
        u16 = lambda i: int.from_bytes(k2c[i:i+2], byteorder="little")
        u32 = lambda i: int.from_bytes(k2c[i:i+4], byteorder="little")
        fmt, n_codes, n_tables = u16(0), u16(2), u32(4)
        offsets = [u32(8+4*i) for i in range(n_tables)]
        tables = [[u16(o+2*i) for i in range(n_codes)] for o in offsets]
        return K2c(n_codes, tables)


@dataclass
class KeyStateRecord:
    default: int
    next_dead: int
    states: List[int]

    def parse(dat: bytes):
        u16 = lambda i: int.from_bytes(dat[i:i+2], byteorder="little")
        u32 = lambda i: int.from_bytes(dat[i:i+4], byteorder="little")
        default = u16(0)
        next_dead = u16(2)
        n_states = u16(4)
        fmt_states = u16(6)
        states = None
        if fmt_states == 1:
            states = [(u16(8+i*4), u16(10+i*4)) for i in range(n_states)]
        return KeyStateRecord(default, next_dead, states)

    def __repr__(self):
        s = chr(self.default)
        if self.states:
            s += "[" + "".join(chr(x) for _,x in self.states) + "]"
        return s

@dataclass
class Ksr:
    records: List[KeyStateRecord]
    def __repr__(self):
        return f"Ksr(...)"

    def parse(ksr: memoryview, uchr: memoryview):
        u16 = lambda i: int.from_bytes(ksr[i:i+2], byteorder="little")
        u32 = lambda i: int.from_bytes(ksr[i:i+4], byteorder="little")
        fmt, n_records = u16(0), u16(2)
        offsets = [u32(4+4*i) for i in range(n_records)]
        records = [KeyStateRecord.parse(uchr[o:]) for o in offsets]
        return Ksr(records)

def parse_kst(kst: memoryview):
    u16 = lambda i: int.from_bytes(kst[i:i+2], byteorder="little")
    n = u16(2)
    return [u16(4+2*i) for i in range(n)]

def parse_ksd(ksd: memoryview):
    u16 = lambda i: int.from_bytes(ksd[i:i+2], byteorder="little")
    u32 = lambda i: int.from_bytes(ksd[i:i+4], byteorder="little")
    n = u16(2)
    offsets = [u16(4+2*i) for i in range(n)]
    return [bytes(ksd[s:e]).decode('UTF-16LE').rstrip('\0') for s, e in zip(offsets, offsets[1:] + [len(ksd)])]

@dataclass
class KeyboardType:
    m2t: M2t
    k2c: K2c
    ksr: Optional[Ksr]
    kst: Optional[List[int]]
    ksd: Optional[List[str]]

@dataclass
class Uchr:
    types: List[Tuple[Tuple[int, int], KeyboardType]]

def parse_uchr(uchr: memoryview):
    u16 = lambda i: int.from_bytes(uchr[i:i+2], byteorder="little")
    u32 = lambda i: int.from_bytes(uchr[i:i+4], byteorder="little")
    header_format, data_version = u16(0), u16(2)
    o_feature = u32(4)
    n = u32(8)
    types = []
    for i in range(n):
        first, last, om2t, ok2c, oksr, okst, oksd = map(u32, range(12+i*28, 12+i*28+28, 4))
        m2t = M2t.parse(uchr[om2t:])
        k2c = K2c.parse(uchr[ok2c:])
        ksr = Ksr.parse(uchr[oksr:], uchr) if oksr else None
        kst = parse_kst(uchr[okst:]) if okst else None
        ksd = parse_ksd(uchr[oksd:]) if oksd else None
        types.append(((first, last), KeyboardType(m2t, k2c, ksr, kst, ksd)))
    if o_feature:
        feature_layout = u16(12+n*28)
        reserved = u16(12+n*28+2)
        longest = u32(12+n*28+4)
    return Uchr(types)


def parse_dat(dat: memoryview) -> Dict[bytes, Uchr]:
    u32 = lambda i: int.from_bytes(dat[i:i+4], byteorder="little")
    zs = lambda i: bytes(dat[i:]).partition(b'\0')[0]
    magic, entries, offset = u32(0), u32(4), u32(8)
    assert magic == 0xabcdef02

    layouts = {}
    for p in range(offset, offset+64*entries, 64):
        zero, o_name, o_number, flags, locale, unk_flags, s_data, o_data, s_ranges, o_ranges, \
            s_icon, o_icon, s_modplist, o_modplist, s_plist, o_plist = map(u32, range(p, p+64, 4))
        assert zero == 0
        name = zs(o_name)
        num = u32(o_number)
        uchr = dat[o_data : o_data + s_data]
        # plist = dat[o_plist : o_plist + s_plist]
        # print(name)
        uchr = parse_uchr(uchr)
        layouts[name] = uchr
    return layouts

if __name__ == '__main__':
    path = '/System/Library/Keyboard Layouts/AppleKeyboardLayouts.bundle/Contents/Resources/AppleKeyboardLayouts-L.dat'
    if len(sys.argv) > 1:
        path = sys.argv[1]
    with open(path, 'rb') as f:
        dat = memoryview(f.read())
        layouts = parse_dat(dat)
        print(len(layouts))

        dvorak = layouts[b'Dvorak']
        typ = dvorak.types[0][1]
        table = typ.k2c.tables[typ.m2t.default]
        keyboard = [
            [50, 18, 19, 20, 21, 23, 22, 26, 28, 25, 29, 27, 24],
            [12, 13, 14, 15, 17, 16, 32, 34, 31, 35, 33, 30, 42],
            [0, 1, 2, 3, 5, 4, 38, 40, 37, 41, 39],
            [6, 7, 8, 9, 11, 45, 46, 43, 47, 44],
        ]
        def show_uc(uc):
            if uc >> 14 in (0, 3):
                return chr(uc)
            elif (uc >> 14) == 1:
                return repr(typ.ksr.records[uc & 0x3fff])
            else:
                return '2'

        for row in keyboard:
            print(*[show_uc(table[i]) for i in row])
