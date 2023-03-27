import bpy
from bpy.props import EnumProperty, BoolProperty, StringProperty, CollectionProperty, IntProperty
from bpy_extras.io_utils import ImportHelper, ExportHelper
from pathlib import Path

def clamp(value, lower, upper):
    return lower if value < lower else upper if value > upper else value

def fetch_user_preferences():
    return bpy.context.preferences.addons[__package__].preferences

def generate_prefix(name):
    return "".join(chars[0] for chars in name.replace(" ", "_").split("_")[:10] if chars[0].isupper())

class ListItem(bpy.types.PropertyGroup):
    name: StringProperty(name="Name", description="A name for this item", default="Untitled") 
    filepath: StringProperty(name="Filepath", description="", default="")
    prefix: StringProperty(name="Prefix", description="", default="")
    is_enabled: BoolProperty(name="", description="", default=True)

class MY_UL_List(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index): 
        # We could write some code to decide which icon to use here... 
        custom_icon = 'BLENDER' 
        # Make sure your code supports all 3 layout types 
        if self.layout_type in {'DEFAULT', 'COMPACT'}: 
            #layout.label(text=item.name, icon = custom_icon)
            split = layout.split(factor=0.75)
            split.prop(item, "name", icon = custom_icon, emboss=False, text="")
            icon = 'CHECKBOX_HLT' if item.is_enabled else 'CHECKBOX_DEHLT'
            split.prop(item, "prefix", emboss=False)
            layout.prop(item, "is_enabled", text="", emboss=False, icon=icon)
        elif self.layout_type in {'GRID'}: 
            layout.alignment = 'CENTER' 
            layout.label(text="", icon = custom_icon) 
            # ( inside register() ) bpy.utils.register_class(MY_UL_List)

class LIST_OT_AutogenerateName(bpy.types.Operator):
    bl_idname = "my_list.autogenerate_name" 
    bl_label = "Auto-Generate Name" 

    def execute(self, context): 
        prefs = fetch_user_preferences()
        selected_item = prefs.my_list[prefs.list_index]
        selected_item.name = Path(selected_item.filepath).stem

        return{'FINISHED'}


class LIST_OT_AutogeneratePrefix(bpy.types.Operator):
    bl_idname = "my_list.autogenerate_prefix" 
    bl_label = "Auto-Generate Prefix" 

    def execute(self, context): 
        prefs = fetch_user_preferences()
        selected_item = prefs.my_list[prefs.list_index]
        selected_item.prefix = generate_prefix(selected_item.name)

        return{'FINISHED'}

class LIST_OT_NewItem(bpy.types.Operator, ImportHelper):
    bl_idname = "my_list.new_item" 
    bl_label = "Add Blend File" 
    
    filename_ext = '.blend'
    filter_glob: StringProperty(default='*.blend', options={'HIDDEN'})

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context): 
        filepath = Path(self.properties.filepath)

        prefs = fetch_user_preferences()
        my_list = prefs.my_list 

        if str(filepath) in [item.filepath for item in my_list]:
            self.report({'WARNING'}, f"{filepath} \n File is already in list.")
            return {'CANCELLED'}

        my_list.add()
        index = prefs.list_index 
        max_index = len(my_list) - 1 

        intended_index = clamp(index + 1, lower=0, upper=max_index)
        my_list.move(max_index, intended_index)

        item = my_list[intended_index]
        item.name = filepath.stem
        item.filepath = str(filepath)
        item.prefix = generate_prefix(filepath.stem)

        prefs.list_index = intended_index
        return{'FINISHED'}

class LIST_OT_UpdateFilepath(bpy.types.Operator, ImportHelper):
    bl_idname = "my_list.update_filepath" 
    bl_label = "Update Blend File" 
    
    filename_ext = '.blend'
    filter_glob: StringProperty(default='*.blend', options={'HIDDEN'})

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context): 
        filepath = Path(self.properties.filepath)

        prefs = fetch_user_preferences()
        my_list = prefs.my_list 
        index = prefs.list_index 
        item = my_list[index]

        if str(filepath) == item.filepath:
            self.report({'WARNING'}, f"Same filepath was selected.")
            return {'CANCELLED'}            

        elif str(filepath) in [item.filepath for item in my_list]:
            self.report({'WARNING'}, f"{filepath} \n File is already in list.")
            return {'CANCELLED'}

        item.name = filepath.stem
        item.filepath = str(filepath)
        item.prefix = generate_prefix(filepath.stem)
        return{'FINISHED'}

class LIST_OT_DeleteItem(bpy.types.Operator):
    bl_idname = "my_list.delete_item" 
    bl_label = "Deletes an item"

    @classmethod 
    def poll(cls, context): 
        prefs = fetch_user_preferences()
        return prefs.my_list 
    
    def execute(self, context): 
        prefs = fetch_user_preferences()
        my_list = prefs.my_list 
        index = prefs.list_index 
        
        my_list.remove(index) 
        prefs.list_index = clamp(index - 1, lower=0, upper=len(my_list) - 1)
        return{'FINISHED'}

class LIST_OT_MoveItem_Up(bpy.types.Operator):
    bl_idname = "my_list.move_item_up"
    bl_label = ""
    bl_description = "Move an item up in the list"

    @classmethod
    def poll(cls, context):
        prefs = fetch_user_preferences()
        return prefs.list_index > 0

    def execute(self, context):
        prefs = fetch_user_preferences()
        my_list = prefs.my_list
        index = prefs.list_index
        neighbor_index = index - 1

        my_list.move(neighbor_index, index)
        prefs.list_index = clamp(neighbor_index, lower=0, upper=len(my_list) - 1)
        return{'FINISHED'}

class LIST_OT_MoveItem_Down(bpy.types.Operator):
    bl_idname = "my_list.move_item_down"
    bl_label = ""
    bl_description = "Move an item down in the list"

    @classmethod
    def poll(cls, context):
        prefs = fetch_user_preferences()
        return prefs.list_index < len(prefs.my_list) - 1

    def execute(self, context):
        prefs = fetch_user_preferences()
        my_list = prefs.my_list
        index = prefs.list_index
        neighbor_index = index + 1

        my_list.move(neighbor_index, index)
        prefs.list_index = clamp(neighbor_index, lower=0, upper=len(my_list) - 1)
        return{'FINISHED'}

class NodegroupLibraryPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    my_list: CollectionProperty(type = ListItem) 
    list_index: IntProperty(name = "Index for my_list", default = 0)

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
        prefs = fetch_user_preferences()

        col = layout.row().column(heading="Options:")
        col.prop(self, "enable_parent_menu")
        col.prop(self, "ui_mode")

        if self.ui_mode == 'EXPANDED':
            col.prop(self, "hide_empty_headers")
        
        col.separator(factor=1)
        col.label(text="User Library:")
        row = col.row()
        row.template_list("MY_UL_List", "The_List", self, "my_list", self, "list_index")

        col = row.column(align=True)
        col.operator("my_list.new_item", text="", icon='ADD')
        col.operator("my_list.delete_item", text="", icon='REMOVE')

        col.separator(factor = 1)
        col.operator("my_list.move_item_up", text="", icon='TRIA_UP')
        col.operator("my_list.move_item_down", text="", icon='TRIA_DOWN')
        
        if self.list_index >= 0 and self.my_list: 
            item = self.my_list[self.list_index] 
            col = layout.column()
            col.use_property_split = True

            row = col.row(align=True)
            row.prop(item, "name") 
            row.operator("my_list.autogenerate_name", text="", icon='EVENT_A')
            row.separator(factor = 1.35)

            row = col.row(align=True)
            row.prop(item, "filepath")
            row.operator("my_list.update_filepath", text="", icon='FILEBROWSER')
            row.separator(factor = 1.35)

            row = col.row(align=True)
            row.prop(item, "prefix")
            row.operator("my_list.autogenerate_prefix", text="", icon='EVENT_A')
            row.separator(factor = 1.35)

            row = col.row()
            row.prop(item, "is_enabled")
            row.separator(factor = 1.35)

def register():
    bpy.utils.register_class(ListItem)
    bpy.utils.register_class(NodegroupLibraryPreferences)
    bpy.utils.register_class(MY_UL_List)
    bpy.utils.register_class(LIST_OT_NewItem)
    bpy.utils.register_class(LIST_OT_DeleteItem)
    bpy.utils.register_class(LIST_OT_MoveItem_Up)
    bpy.utils.register_class(LIST_OT_MoveItem_Down)
    bpy.utils.register_class(LIST_OT_UpdateFilepath)
    bpy.utils.register_class(LIST_OT_AutogenerateName)
    bpy.utils.register_class(LIST_OT_AutogeneratePrefix)

    #bpy.types.Scene.my_list = CollectionProperty(type = ListItem) 
    #bpy.types.Scene.list_index = IntProperty(name = "Index for my_list", default = 0)

def unregister():
    bpy.utils.unregister_class(ListItem)
    bpy.utils.unregister_class(NodegroupLibraryPreferences)
    bpy.utils.unregister_class(MY_UL_List)
    bpy.utils.unregister_class(LIST_OT_NewItem)
    bpy.utils.unregister_class(LIST_OT_DeleteItem)
    bpy.utils.unregister_class(LIST_OT_MoveItem_Up)
    bpy.utils.unregister_class(LIST_OT_MoveItem_Down)
    bpy.utils.unregister_class(LIST_OT_UpdateFilepath)
    bpy.utils.unregister_class(LIST_OT_AutogenerateName)
    bpy.utils.unregister_class(LIST_OT_AutogeneratePrefix)

    #del bpy.types.Scene.my_list
    #del bpy.types.Scene.list_index