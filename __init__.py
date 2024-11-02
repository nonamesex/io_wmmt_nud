bl_info = {
    "name": "Import WanganMidnight MaximumTune 4/5/6 NUD (.nud/.bin)",
    "author": "downsided",
    "description": "Import NUD meshes",
    "version": (1, 0, 0),
    "blender": (3, 6, 0),
    "doc_url": "https://github.com/nonamesex/io_wmmt_nud",
    "tracker_url": "https://github.com/nonamesex/io_wmmt_nud/issues",
    "category": "Import"
}

if 'bpy' in locals():
    import importlib
    importlib.reload(nud_import_ot)
else:
    from .src import nud_import_ot
    from .src import nut_import_ot

import bpy

classes = nud_import_ot.classes + nut_import_ot.classes

def nud_import_menu_func(self, context):
    self.layout.operator(nud_import_ot.NUD_OT_import.bl_idname, text='WanganMidnight MaximumTune 4/5/6 Model (.nud/.bin)')
def nut_import_menu_func(self, context):
    self.layout.operator(nut_import_ot.NUT_OT_import.bl_idname, text='WanganMidnight MaximumTune 4/5/6 Texture (.nut)')

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.TOPBAR_MT_file_import.append(nud_import_menu_func)
    bpy.types.TOPBAR_MT_file_import.append(nut_import_menu_func)

def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(nut_import_menu_func)
    bpy.types.TOPBAR_MT_file_import.remove(nud_import_menu_func)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == '__main__':
    register()
