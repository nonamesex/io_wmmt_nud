import os

import bpy
from bpy.props import StringProperty, BoolProperty, CollectionProperty
from bpy.types import Operator
from bpy_extras.io_utils import ImportHelper

from .nut import nut_unpack

empty_set = set()

class NUT_OT_import(Operator, ImportHelper):
    bl_idname = 'unpack_texture.nut'
    bl_label = 'Unpack (.nut)'
    bl_options = {'INTERNAL', 'UNDO'}

    __doc__ = 'Unpacks a NUT file'

    filename_ext = '.nut'
    filter_glob: StringProperty(default='*.nut', options={'HIDDEN'})
    files: CollectionProperty(type=bpy.types.PropertyGroup)

    def execute(self, context):
        directory = self.filepath
        for j, i in enumerate(self.files):
            directory = directory.replace(i.name, "")

        files = [os.path.join(directory, i.name) for j, i in enumerate(self.files)]

        nut_unpack(files)

        self.report({'INFO'}, f'NUT unpacked')

        return {'FINISHED'}

classes = (
    NUT_OT_import,
)
