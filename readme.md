# Source Caption Decompiler

This is a simple utility to decompile captions `.dat` files in the Source engine.

## Usage

1. Place `closecaption_english.dat` (the file you want to decompile) alongside `decompile.py`
2. Run `python decompile.py`

## How it works

The format of compiled captions files looks something like:

```
- metadata
- list of crc32 hashes of (lowercase) sound names, paired with offsets for the caption strings they reference
- blocks of data that contain the caption strings refered to by the hashes
```

Even though (by the nature of how hashing works) we can't reverse the crc32 hashes to get the human-readable name directly, we can take lists of human-readable names and generate their hashes to compare against the hashes we find when decompiling. We use lists oriented towards Team Fortress 2, though these lists can be modified to support other Source games.

Unfortunately, it's pretty common for caption files to include things that aren't included in our list. The reasons can range from genuine mistakes on the caption's part (things like including `Demoman.PainSevere07` despite not being a valid sound name referenced ingame anywhere) to including custom captions for use in scripts with `cc_emit`. In these cases we'll decompile it to `U.XXXXXXXX` where `XXXXXXXX` is the hash written in hex.
