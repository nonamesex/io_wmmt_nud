u32 paddingfix = 0;
u16 headersize = 0;


struct Texture {
    u32 fullsize;
    padding[4];
    u32 size;
    u16 headerSize;
    padding[2 + 3];
    u8 ddsFormat;
    
    u16 width;
    u16 height;
    u32 mipMaps;
    padding[4];
    u32 offset;
    // _offset = offset + 16;
    if (headerSize > 0x50) {
        padding[4 * 2];
    }
    
    padding[4 * 3 + 2*2];
    
    if (headerSize == 0x60) {
        padding[4 * 2];
    } else if (headerSize == 0x70) {
        padding[4 * 6];
    } else if (headerSize == 0x80) {
        padding[4 * 10];
    } else if (headerSize == 0x90) {
        padding[4 * 14];
    }
    
    padding[4 * 5];
    u8 texIndex[4];
    padding[4];
    
    // u8 dds[size / 8] @ offset + 16 + paddingfix;
    u8 dds_start @ offset + 16 + paddingfix;
    u8 dds_end @ offset + 16 + paddingfix + size - 1;
    paddingfix += headerSize;
};

struct NTWD {
    char magic[4];
    u8 version;
    u8 unk00;
    u16 texCount;
    padding[8];
    
    Texture textures[texCount];
};

NTWD ntwd @ 0x0;
