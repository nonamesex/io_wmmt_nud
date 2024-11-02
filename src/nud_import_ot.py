import os

import bpy
from bpy.props import StringProperty, BoolProperty, CollectionProperty
from bpy.types import Operator
from bpy_extras.io_utils import ImportHelper

from .nud import nud_import_stage
from .nud import setup_flags

empty_set = set()

class NUD_OT_import(Operator, ImportHelper):
    bl_idname = 'import_mesh.nud'
    bl_label = 'Import (.nud/.bin)'
    bl_options = {'INTERNAL', 'UNDO'}

    __doc__ = 'Load a NUD file'

    filename_ext = '.nud'
    filter_glob: StringProperty(default='*.nud;*.bin', options={'HIDDEN'})
    files: CollectionProperty(type=bpy.types.PropertyGroup)

    split_meshes: BoolProperty(
        default = True,
        name = 'Split Meshes by Materials',
        options = empty_set
    )

    def execute(self, context):
        directory = self.filepath
        for j, i in enumerate(self.files):
            directory = directory.replace(i.name, "")

        files = [os.path.join(directory, i.name) for j, i in enumerate(self.files)]

        setup_flags(self.split_meshes)
        nud_import_stage(files)

        self.report({'INFO'}, f'NUD imported')

        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'split_meshes')

classes = (
    NUD_OT_import,
)
