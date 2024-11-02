#include "type/float16"
#pragma pattern_limit 2147483647

/*

if PolySize_array[z] == 0x00 do(
    FaceCount = PolyAmount_array[z]
    FaceStart = ftell m
    VerStart = (FaceCount * 2) + FaceStart

    StartDirection = 1
    f1 = (readshort m #unsigned) + 1
    f2 = (readshort m #unsigned) + 1  
    FaceDirection = StartDirection
    Do (
	    f3 = (readshort m #unsigned)
	    if (f3==0xFFFF) then (
	        f1 = (readshort m #unsigned) + 1
	        f2 = (readshort m #unsigned) + 1
	        FaceDirection = StartDirection 
	    ) else (
	        f3 += 1
	        FaceDirection *= -1
	        if (f1!=f2) AND (f2!=f3) AND (f3!=f1) then (
			    if FaceDirection > 0 then
				    append Face_array [f3,f2,f1]
			    else
				    append Face_array [f2,f3,f1]
		    )
		    f1 = f2
		    f2 = f3
	    ) 
    ) while ((ftell m) != (VerStart))
)

*/

enum NormalType : u8 {
    NoNormals = 0x0,
    NormalsFloat = 0x1,
    NormalsTanBiTanFloat = 0x3,
    NormalsHalfFloat = 0x6,
    NormalsTanBiTanHalfFloat = 0x7
};

enum BoneType : u8 {
    NoBones = 0x00,
    Float = 0x10,
    HalfFloat = 0x20,
    Byte = 0x40
};

enum UVType : u8 {
    HalfFloat = 0,
    Float = 1
};

enum ColorType : u8 {
    None = 0,
    Byte = 1,
    HalfFloat = 2
};

bitfield VertexFlag {
    NormalType normalType: 4;
    BoneType boneType: 4;
    UVType uvType: 1;
    ColorType colorType: 3;
    unsigned UvCount: 4;
};

struct TextureData {
    u8 index;
    u8 subGroup;
    u8 group;
    u8 class;
};

struct MaterialData {
    padding[4 + 4 + 2];
    u16 texCount;
    padding[4 + 4 * 4];
    TextureData textures[texCount];
};

struct VertexData {
    float position[3];
    if (parent.vertexFlag.normalType == NormalType::NormalsFloat) {
        float normal[4];
    } else if (parent.vertexFlag.normalType == NormalType::NormalsTanBiTanFloat) {
        float normal[4];
        float bitangent[4];
        float tangent[4];
    } else if (parent.vertexFlag.normalType == NormalType::NormalsHalfFloat) {
        type::float16 normal[4];
    } else if (parent.vertexFlag.normalType == NormalType::NormalsTanBiTanHalfFloat) {
        type::float16 normal[4];
        type::float16 bitangent[4];
        type::float16 tangent[4];
    }
    if (parent.vertexFlag.colorType == ColorType::Byte) {
        u8 RGBA[4];
    } else if (parent.vertexFlag.colorType == ColorType::HalfFloat) {
        type::float16 RGBA[4];
    }
    // float16: u * 2; v * -2 + 1;
    // float32: u; v * -1 + 1;
    if (parent.vertexFlag.UvCount >= 1) {
        if (parent.vertexFlag.uvType == UVType::HalfFloat) {
            type::float16 uv1[2];
        } else if (parent.vertexFlag.uvType == UVType::Float) {
            float uv1[2];
        }
    }
    if (parent.vertexFlag.UvCount >= 2) {
        if (parent.vertexFlag.uvType == UVType::HalfFloat) {
            type::float16 uv2[2];
        } else if (parent.vertexFlag.uvType == UVType::Float) {
            float uv2[2];
        }
    }
    if (parent.vertexFlag.UvCount >= 3) {
        if (parent.vertexFlag.uvType == UVType::HalfFloat) {
            type::float16 uv3[2];
        } else if (parent.vertexFlag.uvType == UVType::Float) {
            float uv3[2];
        }
    }
    if (parent.vertexFlag.UvCount >= 4) {
        if (parent.vertexFlag.uvType == UVType::HalfFloat) {
            type::float16 uv4[2];
        } else if (parent.vertexFlag.uvType == UVType::Float) {
            float uv4[2];
        }
    }
    //if (parent.vertexFlag.unk08) {
    //    float unk08;
    //}
};

struct MeshData {
    u32 indicesOffset;
    u32 vertexOffset;
    u32 vertexAddOffset;
    u16 vertexCount;
    VertexFlag vertexFlag;
    
    u32 materialsOffset[4];
    u16 indicesCount;
    u16 indicesFlag;
    
    padding[12];
    
    MaterialData materials @ materialsOffset[0];
    u16 indices[indicesCount] @ parent.parent._indicesOffset + indicesOffset;
    VertexData vertices[vertexCount] @ parent.parent._vertexOffset + vertexOffset;
};

struct ModelData {
    padding[32];

    u32 nameOffset;
    padding[4];
    u16 singleBind;
    u16 meshesCount;
    u32 meshesOffset;
    
    MeshData meshes[meshesCount] @ meshesOffset;
    u8 names[parent._nameSize] @ parent._nameOffset + nameOffset;
};

struct NDWD {
    u8 _headerSize = 48;

    char magic[4];
    u32 size;
    padding[2];
    u16 modelsCount;
    padding[2 * 2];
    u32 indicesOffset;
    u32 indicesSize;
    u32 vertexSize;
    u32 vertexAddSize;
    padding[16];

    u32 _indicesOffset = indicesOffset + _headerSize;
    u32 _vertexOffset = _indicesOffset + indicesSize;
    u32 _vertexAddOffset = _vertexOffset + vertexSize;
    u32 _nameOffset = _vertexAddOffset + vertexAddSize;
    u32 _nameSize = (size + 4) - _nameOffset;
    
    ModelData models[modelsCount];
};

NDWD ndwd[1] @ 0x0 [[inline]];
