import bpy
from bpy.props import EnumProperty, BoolProperty

class NodegroupLibraryPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    bool_prop: BoolProperty(
        name="Bool Prop Template",
        default=True,
        description="Template for Boolean Property")

    def draw(self, context):
        layout = self.layout
        keymap_spacing = 0.15

        col = layout.row().column(heading="Options:")

def register():
    bpy.utils.register_class(NodegroupLibraryPreferences)

def unregister():
    bpy.utils.unregister_class(NodegroupLibraryPreferences)