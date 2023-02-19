import bpy
from bpy.types import Panel

class NodegroupLibraryUtils(Panel):
    bl_label = "Utils"
    bl_idname = "NODEGROUP_LIBRARY_UTILS_PT_PANEL_NAME"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = "UI"
    bl_category = "Library Utils"

    def draw(self, context):
        layout = self.layout

def register():
    bpy.utils.register_class(NodegroupLibraryUtils)

def unregister():
    bpy.utils.unregister_class(NodegroupLibraryUtils)