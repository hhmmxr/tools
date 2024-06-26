import apsw
import argparse
import numpy as np

element_symbols = {
    1: "H", 2: "He", 3: "Li", 4: "Be", 5: "B", 6: "C", 7: "N", 8: "O", 9: "F", 10: "Ne",
    11: "Na", 12: "Mg", 13: "Al", 14: "Si", 15: "P", 16: "S", 17: "Cl", 18: "Ar", 19: "K", 20: "Ca",
    21: "Sc", 22: "Ti", 23: "V", 24: "Cr", 25: "Mn", 26: "Fe", 27: "Co", 28: "Ni", 29: "Cu", 30: "Zn",
    31: "Ga", 32: "Ge", 33: "As", 34: "Se", 35: "Br", 36: "Kr", 37: "Rb", 38: "Sr", 39: "Y", 40: "Zr",
    41: "Nb", 42: "Mo", 43: "Tc", 44: "Ru", 45: "Rh", 46: "Pd", 47: "Ag", 48: "Cd", 49: "In", 50: "Sn",
    51: "Sb", 52: "Te", 53: "I", 54: "Xe", 55: "Cs", 56: "Ba", 57: "La", 58: "Ce", 59: "Pr", 60: "Nd",
    61: "Pm", 62: "Sm", 63: "Eu", 64: "Gd", 65: "Tb", 66: "Dy", 67: "Ho", 68: "Er", 69: "Tm", 70: "Yb",
    71: "Lu", 72: "Hf", 73: "Ta", 74: "W", 75: "Re", 76: "Os", 77: "Ir", 78: "Pt", 79: "Au", 80: "Hg",
    81: "Tl", 82: "Pb", 83: "Bi", 84: "Po", 85: "At", 86: "Rn", 87: "Fr", 88: "Ra", 89: "Ac", 90: "Th",
    91: "Pa", 92: "U", 93: "Np", 94: "Pu", 95: "Am", 96: "Cm", 97: "Bk", 98: "Cf", 99: "Es", 100: "Fm",
    101: "Md", 102: "No", 103: "Lr", 104: "Rf", 105: "Db", 106: "Sg", 107: "Bh", 108: "Hs", 109: "Mt", 110: "Ds",
    111: "Rg", 112: "Cn", 113: "Nh", 114: "Fl", 115: "Mc", 116: "Lv", 117: "Ts", 118: "Og"
}

class Database:
    def __init__(self, filename):
        self.cursor = apsw.Connection(filename, flags=apsw.SQLITE_OPEN_READONLY).cursor()

    def __len__(self):
        return self.cursor.execute('''SELECT * FROM metadata WHERE id=1''').fetchone()[-1]

    def __getitem__(self, idx):
        data = self.cursor.execute('''SELECT * FROM data WHERE id='''+str(idx)).fetchone()
        return self._unpack_data_tuple(data)

    def _deblob(self, buffer, dtype, shape=None):
        array = np.frombuffer(buffer, dtype)
        if not np.little_endian:
            array = array.byteswap()
        array.shape = shape
        return np.copy(array)

    def _unpack_data_tuple(self, data):
        n = len(data[3])//4  # A single int32 is 4 bytes long.
        q = np.asarray([0.0 if data[1] is None else data[1]], dtype=np.float32)
        s = np.asarray([0.0 if data[2] is None else data[2]], dtype=np.float32)
        z = self._deblob(data[3], dtype=np.int32, shape=(n,))
        r = self._deblob(data[4], dtype=np.float32, shape=(n, 3))
        e = np.asarray([0.0 if data[5] is None else data[5]], dtype=np.float32)
        f = self._deblob(data[6], dtype=np.float32, shape=(n, 3))
        d = self._deblob(data[7], dtype=np.float32, shape=(1, 3))
        return q, s, z, r, e, f, d

def write_to_xyz_file(z, r, filename="output.xyz"):
    with open(filename, 'a') as f:  # Note the 'a' here for 'append' mode
        f.write(f"{len(z)}\n")
        f.write("Generated by script\n")
        for atomic_number, position in zip(z, r):
            element_symbol = element_symbols.get(atomic_number, f"Unknown_{atomic_number}")
            f.write(f"{element_symbol} {position[0]} {position[1]} {position[2]}\n")

parser = argparse.ArgumentParser()
parser.add_argument("database")
args = parser.parse_args()

database = Database(args.database)
num_entries = len(database)  # This will now process every entry in the database.
for entry in range(num_entries):
    q, s, z, r, e, f, d = database[entry]
    write_to_xyz_file(z, r, filename="data.xyz")
    print(f'Entry {entry} successfully written to xyz format.')
