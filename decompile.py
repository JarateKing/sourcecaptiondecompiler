import sys, os, binascii, itertools, zlib

class Crc32Collider:
    # adapted from https://www.nayuki.io/page/forcing-a-files-crc-to-any-value
    # ............ https://www.nayuki.io/res/forcing-a-files-crc-to-any-value/forcecrc32.py
    # with some edits to suit our use-case
    
    POLYNOMIAL = 0x104C11DB7
    ALPHABET = 'abcdefghijklmnopqrstuvwxyz0123456789'
    ALPHASET = set(ALPHABET)
    
    def GenerateAsciiCollisionSuffix(string, desiredHash):
        # most of this class finds a crc32 collision by appending 4 arbitrary bytes
        # here, we append a extra characters for the needed entropy to keep it in ascii
        # this is done naively by redoing it if the appended bytes are outside of ascii
        # we could improve this further (see: madler/spoof) but this works good enough
        
        for a in Crc32Collider.ALPHABET:
            for b in Crc32Collider.ALPHABET:
                for c in Crc32Collider.ALPHABET:
                    suffix = Crc32Collider.GenerateCollisionSuffix(string + a + b + c, desiredHash)
                    if (suffix != '') and (set(suffix) <= Crc32Collider.ALPHASET):
                        return a + b + c + suffix
        return ''

    def GenerateCollisionSuffix(string, desiredHash):
        bytes = bytearray(string.lower() + 'aaaa', 'ascii')
        crc = binascii.crc32(bytes)
        
        length = len(bytes)
        offset = length - 4
        delta = crc ^ desiredHash
        delta = Crc32Collider.multiply_mod(Crc32Collider.reciprocal_mod(Crc32Collider.pow_mod(2, (length - offset) * 8)), Crc32Collider.reverse32(delta))
        
        bytes4 = bytearray(bytes[offset:length])
        for i in range(4):
            bytes4[i] ^= (Crc32Collider.reverse32(delta) >> (i * 8)) & 0xFF
        
        for i in range(1, 5):
            bytes[-i] = bytes4[-i]
        
        try:
            return bytes.decode()[-4:]
        except:
            return ''

    def reverse32(x):
        y = 0
        for i in range(32):
            y = (y << 1) | (x & 1)
            x >>= 1
        return y

    def multiply_mod(x, y):
        z = 0
        while y != 0:
            z ^= x * (y & 1)
            y >>= 1
            x <<= 1
            if (x >> 32) & 1 != 0:
                x ^= Crc32Collider.POLYNOMIAL
        return z

    def pow_mod(x, y):
        z = 1
        while y != 0:
            if y & 1 != 0:
                z = Crc32Collider.multiply_mod(z, x)
            x = Crc32Collider.multiply_mod(x, x)
            y >>= 1
        return z

    def divide_and_remainder(x, y):
        if y == 0:
            raise ValueError("division by zero")
        if x == 0:
            return (0, 0)
        ydeg = Crc32Collider.get_degree(y)
        z = 0
        for i in range(Crc32Collider.get_degree(x) - ydeg, -1, -1):
            if (x >> (i + ydeg)) & 1 != 0:
                x ^= y << i
                z |= 1 << i
        return (z, x)
        
    def reciprocal_mod(x):
        y = x
        x = Crc32Collider.POLYNOMIAL
        a = 0
        b = 1
        while y != 0:
            q, r = Crc32Collider.divide_and_remainder(x, y)
            c = a ^ Crc32Collider.multiply_mod(q, b)
            x = y
            y = r
            a = b
            b = c
        if x == 1:
            return a
        else:
            raise ValueError("reciprocal does not exist")

    def get_degree(x):
        return x.bit_length() - 1

# obtain the hashes of possible sound names
soundmap = {}
soundlists = ['tf2.txt', 'commentary.txt', 'common_cc_emit.txt']
for soundlist in soundlists:
    with open('./lists/' + soundlist) as file:
        for line in file.readlines():
            line = line.strip().lower()
            crc = binascii.crc32(line.encode('ascii'))
            
            if (crc in soundmap):
                if (line != soundmap[crc]):
                    print("COLLISION BETWEEN", line, "AND", soundmap[crc])
            else:
                soundmap[crc] = line

# decompile file
to_open = 'closecaption_english'
with open('./' + to_open + '.dat', "rb") as data, open('./' + to_open + '.dat', "rb") as datacopy, open('./' + to_open + '_decompiled.txt', "w", encoding='utf16') as file:
    labels = {}
    
    # parse file
    magic = data.read(4).decode("ascii")
    version = int.from_bytes(data.read(4), byteorder='little')
    numblocks = int.from_bytes(data.read(4), byteorder='little')
    blocksize = int.from_bytes(data.read(4), byteorder='little')
    directorysize = int.from_bytes(data.read(4), byteorder='little')
    dataoffset = int.from_bytes(data.read(4), byteorder='little')
    
    for i in range(directorysize):
        crc = int.from_bytes(data.read(4), byteorder='little')
        blocknum = int.from_bytes(data.read(4), byteorder='little')
        oldOffset = int.from_bytes(data.read(2), byteorder='little')
        written = int.from_bytes(data.read(2), byteorder='little')
        
        label = ''
        if crc in soundmap:
            label = soundmap[crc]
        else:
            label = 'U.{:08x}.'.format(crc)
            label = label + Crc32Collider.GenerateAsciiCollisionSuffix(label, crc)
        
        datacopy.seek(dataoffset + blocknum * blocksize + oldOffset)
        text = datacopy.read(written).decode('utf-16-le')[:-1]
        labels[label] = text
    
    # write file
    file.write('"lang"\n')
    file.write('{\n')
    file.write('\t"Language" "english"\n')
    file.write('\t"Tokens"\n')
    file.write('\t{\n')
    for label, text in labels.items():
        file.write('\t\t"{0}" "{1}"\n'.format(label, text))
    file.write('\t}\n')
    file.write('}\n')
