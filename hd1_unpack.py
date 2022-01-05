import crcmod
import sys


def decode_block(block):
    result = b""
    for i in range(0, len(block), 4):
        val = int.from_bytes(block[i:i+4], "little")
        if val in (0x00000000, 0xffffffff):
            val ^= 0xffffffff
        elif val & (1 << 28):
            val ^= 0x01111111
        else:
            val ^= 0x07777777
        result += val.to_bytes(4, "little")

    return result


def expect(expected, actual, loc):
    if expected != actual:
        print(f"Error: expected '{expected:x}' but got '{actual:x}' at 0x{loc:X}")
        sys.exit()

def expect_char(expected, infile):
    loc = infile.tell()
    expect(expected, infile.read(1)[0], loc)

blocks = []
crc_fn = crcmod.predefined.mkCrcFun('xmodem')

with open(sys.argv[1], 'rb') as infile:
    block_count = int.from_bytes(infile.read(2), "big")

    for i in range(1, block_count+1):
        # Read STX
        expect_char(0x02, infile)

        # Read block ID
        block_id = infile.read(2)
        if block_id[0] != i & 0xff:
            print(f"Error: expected block {i & 0xff} but got {block_id[0]}")
            sys.exit()

        if block_id[0] + block_id[1] != 0xff:
            print(f"Error: block ID checksum error ({block_id})")
            sys.exit()

        # Read block
        block = infile.read(1024)
        expected_crc = int.from_bytes(infile.read(2), "big")
        actual_crc = crc_fn(block)
        if actual_crc != expected_crc:
            print(f"Error: block CRC incorrect, expected {expected_crc:04x} but got {actual_crc:04x}")
            sys.exit()
        blocks.append(block)

with open(sys.argv[2], 'wb') as outfile:
    for block in blocks:
        outfile.write(decode_block(block))

