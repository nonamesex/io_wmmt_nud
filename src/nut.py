import os
import gzip

from BinaryReader import BinaryReaderFile, BinaryReaderBytes

OVERWEITE_TEXTURE = False

def read_to_memory(nut_path: str):
    with BinaryReaderFile(nut_path) as bin:
        size = bin.getsize()
        magic = bin.ReadUInt32()
        bin.seek(0, 0)

        buffer = bin.ReadBytes(size)

        if magic == 0x00088B1F:
            bin.seek(0, 0)
            buffer = gzip.decompress(buffer)

        return BinaryReaderBytes(buffer)

def read_nut_data(nut: BinaryReaderBytes):
    if nut.ReadUInt32() != 0x4457544E:
        return []

    padding_fix = 0
    textures = []

    nut.seek(2)
    count = nut.ReadUInt16()
    nut.seek(8)

    for i in range(count):
        nut.seek(8)
        dds_size = nut.ReadUInt32()
        header_size = nut.ReadUInt16()
        nut.seek(2 + 3)
        dds_format = nut.ReadByte()
        width = [nut.ReadByte(), nut.ReadByte()]
        height = [nut.ReadByte(), nut.ReadByte()]
        nut.seek(8)
        dds_offset = nut.ReadUInt32()

        if header_size > 0x50:
            nut.seek(4 * 2)
        
        nut.seek(4 * 3 + 2 * 2)

        if header_size == 0x60:
            nut.seek(4 * 2)
        elif header_size == 0x70:
            nut.seek(4 * 6)
        elif header_size == 0x80:
            nut.seek(4 * 10)
        elif header_size == 0x90:
            nut.seek(4 * 14)
        
        nut.seek(4 * 5)

        tex_index = [nut.ReadByte(), nut.ReadByte(), nut.ReadByte(), nut.ReadByte()]

        nut.seek(4)

        textures.append({
            "dds_size": dds_size,
            "dds_offset": dds_offset + 16 + padding_fix,
            "dds_format": dds_format,
            "width": width,
            "height": height,
            "tex_index": tex_index
        })

        padding_fix += header_size

    return textures

def unpack_textures(nut: BinaryReaderBytes, textures: list, output_dir: str):
    for texture in textures:
        texture_name = f"0x{''.join(f'{i:02X}' for i in reversed(texture['tex_index']))}"
        texture_path = os.path.join(output_dir, texture_name + ".dds")

        if os.path.exists(texture_path) and not OVERWEITE_TEXTURE:
            continue

        os.makedirs(output_dir, exist_ok=True)

        with open(texture_path, "wb") as dds:
            if texture["dds_format"] == 14:
                new_dds = bytearray(b"\x44\x44\x53\x20\x7C\x00\x00\x00\x07\x10\x08\x00\x80\x00\x00\x00\x80\x00\x00\x00\x00\x20\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x20\x00\x00\x00\x41\x00\x00\x00\x00\x00\x00\x00\x20\x00\x00\x00\x00\xFF\x00\x00\x00\x00\xFF\x00\x00\x00\x00\xFF\xFF\x00\x00\x00\x08\x10\x40\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
            elif texture["dds_format"] == 21:
                new_dds = bytearray(b"\x44\x44\x53\x20\x7C\x00\x00\x00\x07\x10\x08\x00\x80\x00\x00\x00\x80\x00\x00\x00\x00\x20\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x20\x00\x00\x00\x41\x00\x00\x00\x00\x00\x00\x00\x20\x00\x00\x00\xFF\x00\x00\x00\x00\xFF\x00\x00\x00\x00\xFF\x00\x00\x00\x00\xFF\x08\x10\x40\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
            else:
                new_dds = bytearray(b"\x44\x44\x53\x20\x7C\x00\x00\x00\x07\x10\x08\x00\x80\x00\x00\x00\x80\x00\x00\x00\x00\x20\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x20\x00\x00\x00\x04\x00\x00\x00\x44\x58\x54\x31\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")

            if texture["dds_format"] == 1:
                new_dds[0x57] = 0x33
            elif texture["dds_format"] == 2:
                new_dds[0x57] = 0x35
            elif texture["dds_format"] == 47:
                new_dds[0x54] = 0x41
                new_dds[0x55] = 0x54
                new_dds[0x56] = 0x49
                new_dds[0x57] = 0x31

            new_dds[0x0C] = texture["height"][0]
            new_dds[0x0D] = texture["height"][1]
            new_dds[0x10] = texture["width"][0]
            new_dds[0x11] = texture["width"][1]

            dds.write(new_dds)
            nut.seek(texture["dds_offset"], 0)
            dds.write(nut.ReadBytes(texture["dds_size"]))

def unpack_nut(nut_path: str):
    nut_name = os.path.basename(nut_path).split(".")[0]
    output_dir = os.path.join(os.path.dirname(nut_path), "unpacked", nut_name)

    print(f"Reading {nut_name}.nut")
    nut = read_to_memory(nut_path)
    print(f"Reading {nut_name} textures")
    textures = read_nut_data(nut)
    print(f"Unpacking {nut_name} textures")
    unpack_textures(nut, textures, output_dir)
    nut.close()

def nut_unpack(nut_paths: str):
    for nut_path in nut_paths:
        unpack_nut(nut_path)
