import bpy
from bpy.props import EnumProperty, BoolProperty

class NodegroupLibraryPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    enable_parent_menu: BoolProperty(
        name='Enable "User Library" Menu',
        default=True,
        description='When enabled, put all generated menus in a "User Library" menu. \nOtherwise, generated menus will be appended to the Node Add Menu')

    hide_empty_headers: BoolProperty(
        name='Hide Empty Headers',
        default=False,
        description="When enabled, in Expanded UI Mode, all headers that don't have text or an icon will be hidden")

    ui_mode: EnumProperty(
        name="UI Mode",
        items=(
            ("COMPACT", "Compact", "Draws subcategories as nested submenus"),
            ("EXPANDED", "Expanded", "Draws subcategories as separate columns"),
        ),
        default='EXPANDED',
        description="Specifies how the node subcategories are drawn")

    def draw(self, context):
        layout = self.layout
        keymap_spacing = 0.15

        col = layout.row().column(heading="Options:")
        col.prop(self, "enable_parent_menu")
        col.prop(self, "ui_mode")

        if self.ui_mode == 'EXPANDED':
            col.prop(self, "hide_empty_headers")

def register():
    bpy.utils.register_class(NodegroupLibraryPreferences)

def unregister():
    bpy.utils.unregister_class(NodegroupLibraryPreferences)