import sys, os, binascii, itertools, argparse

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
def GenerateSoundmap(soundlists):
    soundmap = {}
    for soundlist in soundlists:
        with open(soundlist) as file:
            for line in file.readlines():
                line = line.strip().lower()
                crc = binascii.crc32(line.encode('ascii'))
                if (crc in soundmap):
                    if (line != soundmap[crc]):
                        print("COLLISION BETWEEN", line, "AND", soundmap[crc])
                else:
                    soundmap[crc] = line
    return soundmap

def DecompileFile(to_open, soundmap, skipHashSuffix, shouldSkipFormatting, isVerbose, shouldUpdateProgress):
    with open('./' + to_open, "rb") as data, open('./' + to_open, "rb") as datacopy:
        labels = {}
        
        # parse file
        magic = data.read(4).decode("ascii")
        version = int.from_bytes(data.read(4), byteorder='little')
        numblocks = int.from_bytes(data.read(4), byteorder='little')
        blocksize = int.from_bytes(data.read(4), byteorder='little')
        directorysize = int.from_bytes(data.read(4), byteorder='little')
        dataoffset = int.from_bytes(data.read(4), byteorder='little')
        
        if isVerbose:
            print('magic string: {0}'.format(magic))
            print('version data: {0}'.format(version))
            print('blocks count: {0}'.format(numblocks))
            print('block length: {0}'.format(blocksize))
            print('captions num: {0}'.format(directorysize))
            print('block offset: {0}'.format(dataoffset))
            print(flush=True)
        
        if shouldUpdateProgress:
            print('progress: 0/{0}'.format(directorysize), flush=True)
        
        for i in range(directorysize):
            crc = int.from_bytes(data.read(4), byteorder='little')
            blocknum = int.from_bytes(data.read(4), byteorder='little')
            oldOffset = int.from_bytes(data.read(2), byteorder='little')
            written = int.from_bytes(data.read(2), byteorder='little')
            
            label = ''
            if crc in soundmap:
                label = soundmap[crc]
                
                if isVerbose:
                    hexcrc = '{:08x}'.format(crc)
                    print('found crc {0}: {1}'.format(hexcrc, label), flush=True)
            else:
                if skipHashSuffix:
                    label = 'U.{:08x}'.format(crc)
                else:
                    label = 'U.{:08x}.'.format(crc)
                    label = label + Crc32Collider.GenerateAsciiCollisionSuffix(label, crc)
                if isVerbose:
                    hexcrc = '{:08x}'.format(crc)
                    print('failed to find crc {0}, fallback set to {1}'.format(hexcrc, label), flush=True)
            
            datacopy.seek(dataoffset + blocknum * blocksize + oldOffset)
            text = datacopy.read(written).decode('utf-16-le')[:-1]
            labels[label] = text
            
            if isVerbose:
                print('at offset {0} in block {1} with length {2}: "{3}"'.format(oldOffset, blocknum, written, text), flush=True)
            
            if shouldUpdateProgress:
                print('progress: {0}/{1}'.format(i + 1, directorysize), flush=True)
        
        # form file
        output = ''
        
        if shouldSkipFormatting:
            for label, text in labels.items():
                output += '"{0}" "{1}"\n'.format(label, text)
        else:
            output += '"lang"\n'
            output += '{\n'
            output += '\t"Language" "english"\n'
            output += '\t"Tokens"\n'
            output += '\t{\n'
            for label, text in labels.items():
                output += '\t\t"{0}" "{1}"\n'.format(label, text)
            output += '\t}\n'
            output += '}\n'
        
        return output

def main():
    parser = argparse.ArgumentParser(
        prog='Source Caption Decompiler',
        description='Decompiles source caption .dat files')
    
    parser.add_argument('filename', nargs='?')
    parser.add_argument('-i', '--infile', nargs='?', default='closecaption_english.dat')
    parser.add_argument('-o', '--outfile', nargs='?', default='closecaption_decompiled.txt')
    parser.add_argument('-l', '--lists', nargs='+', default=['./lists/tf2.txt', './lists/commentary.txt', './lists/common_cc_emit.txt'])
    parser.add_argument('--nohashsuffix', action='store_true')
    parser.add_argument('--stdout', action='store_true')
    parser.add_argument('--raw', action='store_true')
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-p', '--progress', action='store_true')
    
    args = parser.parse_args()
    
    filename = args.filename if args.filename else args.infile
    
    soundmap = GenerateSoundmap(args.lists)
    data = DecompileFile(filename, soundmap, args.nohashsuffix, args.raw, args.verbose, args.progress)
    
    if args.stdout:
        print(data)
    else:
        with open(args.outfile, "w") as file:
            file.write(data)
    
    if args.progress:
        print('done!')

if __name__ == "__main__":
    main()
