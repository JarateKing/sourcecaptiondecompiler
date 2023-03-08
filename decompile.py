import sys, os, binascii, itertools

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
        
        label = (soundmap[crc] if (crc in soundmap) else 'U.{:08x}'.format(crc))
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
