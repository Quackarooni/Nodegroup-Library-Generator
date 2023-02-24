import bpy
from bpy.props import EnumProperty, BoolProperty

class NodegroupLibraryPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    bool_prop: BoolProperty(
        name='Enable "User Library" Menu',
        default=True,
        description='When enabled, put all generated menus in a "User Library" menu. \nOtherwise, generated menus will be appended to the Node Add Menu')

    def draw(self, context):
        layout = self.layout
        keymap_spacing = 0.15

        col = layout.row().column(heading="Options:")
        col.prop(self, "bool_prop")

def register():
    bpy.utils.register_class(NodegroupLibraryPreferences)

def unregister():
    bpy.utils.unregister_class(NodegroupLibraryPreferences)