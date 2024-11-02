from os import path, walk
import gzip

import bpy
import bmesh

from .BinaryReader import BinaryReaderBytes, BinaryReaderFile
from .ProgressBar import ProgressBar
from .nut import unpack_nut

progress_bar = ProgressBar()

# from enum import Enum
# 
# class NormalType(Enum):
#     NOP = 0
#     Float = 1
#     TanBitanFloat = 3
#     Half = 6
#     TanBitanHalf = 7
# class BoneType(Enum):
#     NOP = 0
#     Float = 1
#     Half = 2
#     Byte = 4
# class UvType(Enum):
#     Half = 0
#     Float = 1
# class ColorType(Enum):
#     NOP = 0
#     Byte = 1
#     Half = 2

class VertexFlags():
    def __init__(self, int):
        self.int = int

        self.__vertex_flags__ = [
            ["NormalType", 0, 0x7],
            ["BoneType", 4, 0x7],
            ["UvType", 8, 0x1],
            ["ColorType", 9, 0x3],
            ["UvCount", 12, 0x3]
        ]

        for flag in self.__vertex_flags__:
            self.__setattr__(flag[0], ((int & 0xFFFF) >> flag[1]) & flag[2])

    def __int__(self):
        return self.int

    def __str__(self):
        return f"< {' | '.join([':'.join([x[0], str(self.__getattribute__(x[0]))]) for x in self.__vertex_flags__])} >"

def read_to_memory(nud_path: str):
    with BinaryReaderFile(nud_path) as bin:
        size = bin.getsize()
        magic = bin.ReadUInt32()
        bin.seek(0, 0)

        buffer = bin.ReadBytes(size)

        if magic == 0x00088B1F:
            bin.seek(0, 0)
            buffer = gzip.decompress(buffer)

        return BinaryReaderBytes(buffer)

def read_nuds_from_bin(bin_path: str):
    nudp = read_to_memory(bin_path)
    nudp_size = nudp.getsize()
    nuds = []

    atempts = 0

    while (nudp_size - nudp.tell()) > 8:
        if nudp.ReadUInt32() != 0x4457444E:
            if atempts == 32:
                break
            else:
                atempts += 1
                nudp.seek(-3)
                continue

        atempts = 0
        size = nudp.ReadUInt32()
        nudp.seek(-8)

        nuds.append(BinaryReaderBytes(nudp.ReadBytes(size)))

    nudp.close()

    return nuds

def read_mesh_material(nud: BinaryReaderBytes, offset):
    pos = nud.tell()

    nud.seek(offset, 0)
    nud.seek(4 + 4 + 2)
    texture_count = nud.ReadUInt16()
    nud.seek(4 + 4 * 4)

    textures = []

    for texture_index in range(texture_count):
        textures.append([nud.ReadByte(), nud.ReadByte(), nud.ReadByte(), nud.ReadByte()])
        nud.seek(4 * 5)
            
    nud.seek(pos, 0)

    return textures

def read_mesh_indices(nud: BinaryReaderBytes, offset: int, count: int):
    pos = nud.tell()
    nud.seek(offset, 0)

    indices = []
    for i in range(count):
        indices.append(nud.ReadUInt16())

    nud.seek(pos, 0)

    return indices

def read_mesh_vertices(nud: BinaryReaderBytes, offset: int, count: int, flags: VertexFlags):
    pos = nud.tell()
    nud.seek(offset, 0)

    vertices = {
        "count": count,
        "flags": flags,
        "position": [],
        "normal": [],
        "color": [],
        "uv1": [],
        "uv2": [],
        "uv3": []
    }

    for i in range(count):
        x, y, z = nud.ReadSingle() * 0.07874, nud.ReadSingle() * 0.07874, nud.ReadSingle() * 0.07874
        vertices["position"].append([ x, -z, y ])

        if flags.NormalType != 0:
            if flags.NormalType == 1 or flags.NormalType == 3:
                x, y, z = nud.ReadSingle(), nud.ReadSingle(), nud.ReadSingle()
                vertices["normal"].append([ x, -z, y ])
                nud.seek(4)
            if flags.NormalType == 3:
                nud.seek(4 * 4 * 2)
            if flags.NormalType == 6 or flags.NormalType == 7:
                x, y, z = nud.ReadHalf(), nud.ReadHalf(), nud.ReadHalf()
                nud.seek(2)
                vertices["normal"].append([ x, -z, y ])
            if flags.NormalType == 7:
                nud.seek(2 * 4 * 2)

        if flags.ColorType != 0:
            if flags.ColorType == 1:
                vertices["color"].append([ nud.ReadByte() / 255, nud.ReadByte() / 255, nud.ReadByte() / 255, nud.ReadByte() / 255 ])
            elif flags.ColorType == 2:
                vertices["color"].append([ nud.ReadHalf(), nud.ReadHalf(), nud.ReadHalf(), nud.ReadHalf() ])

        if flags.UvCount != 0:
            for i in range(1, flags.UvCount + 1):
                if flags.UvType == 0:
                    vertices[f"uv{i}"].append([ nud.ReadHalf(), nud.ReadHalf() * -1 + 1 ])
                elif flags.UvType == 1:
                    vertices[f"uv{i}"].append([ nud.ReadSingle(), nud.ReadSingle() * -1 + 1 ])

    nud.seek(pos, 0)

    return vertices

def read_meshes_data(nud: BinaryReaderBytes, meshes_offset: int, meshes_count: int, indices_offset: int, vertices_offset: int):
    pos = nud.tell()
    nud.seek(meshes_offset, 0)

    meshes = []

    for mesh_index in range(meshes_count):
        mesh_indices_offset = indices_offset + nud.ReadUInt32()
        mesh_vertex_offset = vertices_offset + nud.ReadUInt32()
        nud.seek(4)
        mesh_vertex_count = nud.ReadUInt16()
        mesh_vertex_flag = VertexFlags(nud.ReadUInt16())
        mesh_material_offset = nud.ReadUInt32()
        nud.seek(4 * 3)
        mesh_indices_count = nud.ReadUInt16()
        nud.seek(2 + 12)

        meshes.append({
            "textures": read_mesh_material(nud, mesh_material_offset),
            "indices": read_mesh_indices(nud, mesh_indices_offset, mesh_indices_count),
            "vertices": read_mesh_vertices(nud, mesh_vertex_offset, mesh_vertex_count, mesh_vertex_flag)
        })

    nud.seek(pos, 0)

    return meshes

def read_model_name(nud: BinaryReaderBytes, name_offset: int, name_size: int):
    pos = nud.tell()
    nud.seek(name_offset, 0)

    name = nud.ReadNullTerminatedString()

    nud.seek(pos, 0)
    return name

def read_nud_models(nud: BinaryReaderBytes):
    nud.seek(4)
    size = nud.ReadUInt32()
    nud.seek(2)
    models_count = nud.ReadUInt16()
    nud.seek(2 + 2)
    indices_offset = nud.ReadUInt32() + 48
    indices_size = nud.ReadUInt32()
    vertex_size = nud.ReadUInt32()
    vertexadd_size = nud.ReadUInt32()
    nud.seek(16)

    vertices_offset = indices_offset + indices_size
    vertexadd_offset = vertices_offset + vertex_size
    names_offset = vertexadd_offset + vertexadd_size
    names_size = (size + 4) - names_offset

    models = []

    for model_index in range(models_count):
        nud.seek(32)
        model_name_offset = names_offset + nud.ReadUInt32()
        nud.seek(4 + 2)
        meshes_count = nud.ReadUInt16()
        meshes_offset = nud.ReadUInt32()

        models.append({
            "name": read_model_name(nud, model_name_offset, names_size),
            "meshes": read_meshes_data(nud, meshes_offset, meshes_count, indices_offset, vertices_offset)
        })

    nud.close()

    return models

def build_nud_faces(mesh_data: dict, bm, verts: list):
    face_dir = True
    face_index = 0

    f1 = mesh_data["indices"][face_index]; face_index += 1
    f2 = mesh_data["indices"][face_index]; face_index += 1

    while len(mesh_data["indices"]) > face_index:
        f3 = mesh_data["indices"][face_index]; face_index += 1

        if f3 == 0xFFFF:
            f1 = mesh_data["indices"][face_index]; face_index += 1
            f2 = mesh_data["indices"][face_index]; face_index += 1
            face_dir = True
        else:
            face_dir = not face_dir

            if f1 != f2 and f2 != f3 and f3 != f1:
                try:
                    face = bm.faces.new([verts[f3], verts[f2], verts[f1]] if face_dir else [verts[f2], verts[f3], verts[f1]])
                except:
                    face = bm.faces.get([verts[f3], verts[f2], verts[f1]] if face_dir else [verts[f2], verts[f3], verts[f1]])
                    if face:
                        face = face.copy(verts=False, edges=True)
                        face.normal_flip()
                face.smooth = True

            f1 = f2
            f2 = f3

def get_material_texture(texture_name: str):
    texture_path = f"{texture_name}.dds"

    image = bpy.data.images.get(texture_name)

    if not image:
        image = bpy.data.images.new(texture_name, 1, 1)
        image.filepath = texture_path
        image.source = "FILE"

    return image

def get_material(textures: list):
    if len(textures) == 0:
        material_name = "0x00000000"
    else:
        material_name = f"0x{''.join(f'{i:02X}' for i in reversed(textures[0]))}"

    material_node = bpy.data.materials.get(material_name)
    if material_node:
        return material_node

    material_node = bpy.data.materials.new(name = material_name)
    material_node.preview_render_type = "FLAT"
    material_node.use_nodes = True
    material_node.diffuse_color = (1, 1, 1, 1)
    material_node.specular_color = (0, 0, 0)
    material_node.roughness = 0
    material_node.specular_intensity = 0
    material_node.metallic = 0
    material_node.blend_method = 'BLEND'
    material_node.show_transparent_back = False

    material_nodes = material_node.node_tree.nodes

    material_bsdf = material_nodes["Principled BSDF"]
    material_bsdf.show_options = False
    material_bsdf.inputs[0].default_value = (1, 1, 1, 1) # BaseColor
    material_bsdf.inputs[6].default_value = 0 # Metallic
    material_bsdf.inputs[7].default_value = 0 # Specular
    material_bsdf.inputs[9].default_value = 0 # Roughness

    image_node = material_nodes.new(type = "ShaderNodeTexImage")
    image_node.location = (-280, 300)
    image_node.interpolation = "Cubic"
    if len(textures) != 0:
        image_node.image = get_material_texture(material_name)
        image_node.image.alpha_mode = "STRAIGHT"

    material_links = material_node.node_tree.links

    material_links.new(
        image_node.outputs["Color"],
        material_bsdf.inputs["Base Color"]
    )

    material_links.new(
        image_node.outputs["Alpha"],
        material_bsdf.inputs["Alpha"]
    )

    return material_node

def build_mesh(nud_models: list):
    model_idx = 0
    for model in nud_models:
        model_idx += 1
        meshes_data = model["meshes"]
        model_name = model["name"]

        bpy.ops.object.empty_add(type="ARROWS")
        model_empty = bpy.context.view_layer.objects.active
        model_empty.name = model_name

        mesh_idx = 0
        for mesh_data in meshes_data:
            mesh_idx += 1
            # print(f" - Building model: [{model_idx}/{len(nud_models)}] {model_name}: {mesh_idx}/{len(meshes_data)}")
            # progress_bar.update(f"Building model: [{model_idx}/{len(nud_models)}] {model_name}: {mesh_idx}/{len(meshes_data)}")
            bpy_mesh = bpy.data.meshes.new(model_name)
            bpy_obj = bpy.data.objects.new(model_name, bpy_mesh)
            bpy.context.scene.collection.objects.link(bpy_obj)
            bpy_obj.parent = model_empty

            bm = bmesh.new()
            bm.from_mesh(bpy_mesh)

            verts = []

            vertex_data = mesh_data["vertices"]
            vertex_flags = vertex_data["flags"]

            for i in range(vertex_data["count"]):
                vertex = bm.verts.new(vertex_data["position"][i])
                vertex.index = i

                if vertex_flags.NormalType != 0:
                    vertex.normal = vertex_data["normal"][i]

                verts.append(vertex)

            build_nud_faces(mesh_data, bm, verts)

            if vertex_flags.ColorType != 0:
                vertex_color = bm.loops.layers.color.new("Color")
            if vertex_flags.UvCount >= 1:
                uv_layer1 = bm.loops.layers.uv.new("UV1")
            if vertex_flags.UvCount >= 2:
                uv_layer2 = bm.loops.layers.uv.new("UV2")
            if vertex_flags.UvCount >= 3:
                uv_layer3 = bm.loops.layers.uv.new("UV3")

            for face in bm.faces:
                for loop in face.loops:
                    if vertex_flags.ColorType != 0:
                        loop[vertex_color] = vertex_data["color"][loop.vert.index]
                    if vertex_flags.UvCount >= 1:
                        loop[uv_layer1].uv = vertex_data["uv1"][loop.vert.index]
                    if vertex_flags.UvCount >= 2:
                        loop[uv_layer2].uv = vertex_data["uv2"][loop.vert.index]
                    if vertex_flags.UvCount >= 3:
                        loop[uv_layer3].uv = vertex_data["uv3"][loop.vert.index]

            bm.to_mesh(bpy_mesh)
            bm.free()

            if vertex_flags.ColorType != 0:
                bpy_obj.data.color_attributes.active_color_index = 0

            bpy_mesh.materials.append(get_material(mesh_data["textures"]))

            mesh_data["object"] = bpy_obj

        if not SPLIT_MESHES:
            bpy_main_obj = meshes_data[0]["object"]

            for i in range(1, len(meshes_data)):
                bpy.ops.object.select_all(action = "DESELECT")
                meshes_data[i]["object"].select_set(True)
                bpy_main_obj.select_set(True)
                bpy.context.view_layer.objects.active = bpy_main_obj
                bpy.ops.object.join()

            with bpy.context.temp_override(selected_objects=[model_empty]):
                bpy.ops.object.delete()

            bpy_main_obj.name = model_name
            bpy_main_obj.data.name = model_name

def unpack_nuts(nuts_dir: str):
    for root, dirs, files in walk(nuts_dir, False):
        for file in files:
            if file.lower().endswith(".nut"):
                unpack_nut(path.join(root, file))

def import_nud(nud_path: str):
    nud_name = path.basename(nud_path)

    print(f"Unpacking {nud_name} nuds")
    nuds = read_nuds_from_bin(nud_path)
    progress_bar.set(0, len(nuds))
    for idx, nud in enumerate(nuds):
        # print(f"Reading {nud_name} model: {idx}/{len(nuds)}")
        nud_models = read_nud_models(nud)
        build_mesh(nud_models)
        progress_bar.increment()

def nud_import_stage(nud_paths: str):
    if len(nud_paths) == 0:
        return

    stage_root = path.abspath(path.join(path.dirname(nud_paths[0]), "..", "..", ".."))
    unpack_nuts(stage_root)

    for nud_path in nud_paths:
        import_nud(nud_path)

    print("Finalizing with lazyass texture loading")
    bpy.ops.file.find_missing_files(filter_image=True, directory=stage_root)

def setup_flags(split_meshes = True):
    global SPLIT_MESHES
    SPLIT_MESHES = split_meshes
