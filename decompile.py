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

