import bpy
from bpy.props import EnumProperty, BoolProperty, StringProperty, CollectionProperty, IntProperty
from bpy_extras.io_utils import ImportHelper, ExportHelper
from pathlib import Path
from . import prefs_handler

def clamp(value, lower, upper):
    return lower if value < lower else upper if value > upper else value


def fetch_user_preferences():
    return bpy.context.preferences.addons[__package__].preferences


def generate_prefix(name):
    output = ""

    for chars in name.replace("_", " ").split(" "):
        if len(chars) > 0 and chars[0].isupper():
            output = f"{output}{chars[0]}"

    return output.replace(" ", "")[:10]


class BlendFileEntry(bpy.types.PropertyGroup):
    name: StringProperty(
        name="Name", 
        description="The name used for generating the menu of this .blend file entry", 
        default="Untitled")

    filepath: StringProperty(
        name="Filepath", 
        description="The filepath pointing to where the .blend file is located", 
        default="")

    prefix: StringProperty(
        name="Prefix", 
        description=(
            "The prefix identifying all nodegroups from this file."
            "\n(This is for avoiding conflicts with similarly named nodegroups from different files)"), 
        default="")

    is_enabled: BoolProperty(name="", description="", default=True)


class NODEGROUP_LIBRARY_UL_UIList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        custom_icon = 'BLENDER'
        # Make sure your code supports all 3 layout types
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            split = layout.split(factor=0.75)
            split.prop(item, "name", icon=custom_icon, emboss=False, text="")
            icon = 'CHECKBOX_HLT' if item.is_enabled else 'CHECKBOX_DEHLT'
            split.prop(item, "prefix", emboss=False)
            layout.prop(item, "is_enabled", text="", emboss=False, icon=icon)
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon=custom_icon)


class NODE_OT_NGLibrary_AutogenerateName(bpy.types.Operator):
    bl_idname = "nodegroup_library.autogenerate_name"
    bl_label = "Auto-Generate Name"
    bl_description = "Generate entry name based from current filepath"

    def execute(self, context):
        prefs = fetch_user_preferences()
        selected_item = prefs.entry_list[prefs.current_list_index]
        selected_item.name = Path(selected_item.filepath).stem

        return{'FINISHED'}


class NODE_OT_NGLibrary_AutogeneratePrefix(bpy.types.Operator):
    bl_idname = "nodegroup_library.autogenerate_prefix"
    bl_label = "Auto-Generate Prefix"
    bl_description = "Generate entry prefix based from current name"

    def execute(self, context):
        prefs = fetch_user_preferences()
        selected_item = prefs.entry_list[prefs.current_list_index]
        selected_item.prefix = generate_prefix(selected_item.name)

        return{'FINISHED'}


class NODE_OT_NGLibrary_NewEntry(bpy.types.Operator, ImportHelper):
    bl_idname = "nodegroup_library.new_entry"
    bl_label = "Add Blend File Entry"
    bl_description = "Add a new .blend file entry to library"

    filename_ext = '.blend'
    filter_glob: StringProperty(default='*.blend', options={'HIDDEN'})

    def execute(self, context):
        filepath = Path(self.properties.filepath)

        prefs = fetch_user_preferences()
        entry_list = prefs.entry_list

        if not filepath.name.endswith(".blend"):
            self.report({'WARNING'}, f"Specified path is not a .blend file.")
            return {'CANCELLED'}

        if not filepath.exists():
            self.report({'WARNING'}, f"Specified path does not exist.")
            return {'CANCELLED'}

        elif str(filepath) in [item.filepath for item in entry_list]:
            self.report({'WARNING'}, f"{filepath} \n Selected blend file is already in list.")
            return {'CANCELLED'}

        item = entry_list.add()
        index = prefs.current_list_index
        max_index = len(entry_list) - 1

        intended_index = clamp(index + 1, lower=0, upper=max_index)
        entry_list.move(max_index, intended_index)

        item.name = filepath.stem
        item.filepath = str(filepath)
        item.prefix = generate_prefix(filepath.stem)

        prefs.current_list_index = intended_index
        return{'FINISHED'}


class NODE_OT_NGLibrary_UpdateFilepath(bpy.types.Operator, ImportHelper):
    bl_idname = "nodegroup_library.update_filepath"
    bl_label = "Update Filepath"
    bl_description = "Update the filepath of currently selected .blend file entry"

    filename_ext = '.blend'
    filter_glob: StringProperty(default='*.blend', options={'HIDDEN'})

    def execute(self, context):
        filepath = Path(self.properties.filepath)

        prefs = fetch_user_preferences()
        entry_list = prefs.entry_list
        index = prefs.current_list_index
        item = entry_list[index]

        if not filepath.name.endswith(".blend"):
            self.report({'WARNING'}, f"Specified path is not a .blend file.")
            return {'CANCELLED'}

        if not filepath.exists():
            self.report({'WARNING'}, f"Specified path does not exist.")
            return {'CANCELLED'}

        if str(filepath) == item.filepath:
            self.report({'WARNING'}, f"Specified path is already the current filepath.")
            return {'CANCELLED'}

        elif str(filepath) in [item.filepath for item in entry_list]:
            self.report({'WARNING'}, f"{filepath} \n Selected blend file is already in list.")
            return {'CANCELLED'}

        item.filepath = str(filepath)
        if prefs.override_entry_info:
            item.name = filepath.stem
            item.prefix = generate_prefix(filepath.stem)

        return{'FINISHED'}


class NODE_OT_NGLibrary_RemoveEntry(bpy.types.Operator):
    bl_idname = "nodegroup_library.remove_entry"
    bl_label = "Remove Blend File Entry"
    bl_description = "Remove currently selected .blend file entry from library"

    @classmethod
    def poll(cls, context):
        prefs = fetch_user_preferences()
        return prefs.entry_list

    def execute(self, context):
        prefs = fetch_user_preferences()
        entry_list = prefs.entry_list
        index = prefs.current_list_index

        entry_list.remove(index)
        prefs.current_list_index = clamp(index - 1, lower=0, upper=len(entry_list) - 1)
        return{'FINISHED'}


class NODE_OT_NGLibrary_RemoveAllEntries(bpy.types.Operator):
    bl_idname = "nodegroup_library.remove_all_entries"
    bl_label = "This cannot be undone, are you sure?"
    bl_description = "Removes all .blend file entries from list"

    @classmethod
    def poll(cls, context):
        prefs = fetch_user_preferences()
        return prefs.entry_list

    def execute(self, context):
        prefs = fetch_user_preferences()
        entry_list = prefs.entry_list

        entry_list.clear()
        prefs.current_list_index = 0
        return{'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)


class NODE_OT_NGLibrary_SortAllIEntries(bpy.types.Operator):
    bl_idname = "nodegroup_library.sort_all_entries"
    bl_label = "This cannot be undone, are you sure?"  # Label for confirmation menu
    bl_description = "Sorts all .blend file entries by name in alphabetical order"

    @classmethod
    def poll(cls, context):
        prefs = fetch_user_preferences()
        return len(prefs.entry_list) > 1

    def execute(self, context):
        prefs = fetch_user_preferences()
        entry_list = prefs.entry_list

        attrs = ('name', 'filepath', 'prefix', 'is_enabled')
        sorted_list = tuple(sorted(entry_list, key=lambda x: x.name.upper()))

        if all(a == b for a, b in zip(entry_list, sorted_list)):
            self.report({'INFO'}, f"List is already sorted")
            return{'FINISHED'}

        sorted_data = [(item.name, item.filepath, item.prefix, item.is_enabled) for item in sorted_list]
        entry_list.clear()

        for data in sorted_data:
            entry = entry_list.add()
            for attr, value in zip(attrs, data):
                setattr(entry, attr, value)

        return{'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)


class NODE_OT_NGLibrary_MoveEntry_Up(bpy.types.Operator):
    bl_idname = "nodegroup_library.move_entry_up"
    bl_label = ""
    bl_description = "Move an entry up in the list"

    @classmethod
    def poll(cls, context):
        prefs = fetch_user_preferences()
        return prefs.current_list_index > 0

    def execute(self, context):
        prefs = fetch_user_preferences()
        entry_list = prefs.entry_list
        index = prefs.current_list_index
        neighbor_index = index - 1

        entry_list.move(neighbor_index, index)
        prefs.current_list_index = clamp(neighbor_index, lower=0, upper=len(entry_list) - 1)
        return{'FINISHED'}


class NODE_OT_NGLibrary_MoveEntry_Down(bpy.types.Operator):
    bl_idname = "nodegroup_library.move_entry_down"
    bl_label = ""
    bl_description = "Move an entry down in the list"

    @classmethod
    def poll(cls, context):
        prefs = fetch_user_preferences()
        return prefs.current_list_index < len(prefs.entry_list) - 1

    def execute(self, context):
        prefs = fetch_user_preferences()
        entry_list = prefs.entry_list
        index = prefs.current_list_index
        neighbor_index = index + 1

        entry_list.move(neighbor_index, index)
        prefs.current_list_index = clamp(neighbor_index, lower=0, upper=len(entry_list) - 1)
        return{'FINISHED'}


class NODE_OT_NGLibrary_MoveEntry_toTop(bpy.types.Operator):
    bl_idname = "nodegroup_library.move_entry_to_top"
    bl_label = ""
    bl_description = "Move an entry to the top of list"

    @classmethod
    def poll(cls, context):
        prefs = fetch_user_preferences()
        return prefs.current_list_index > 0

    def execute(self, context):
        prefs = fetch_user_preferences()
        entry_list = prefs.entry_list
        index = prefs.current_list_index
        max_index = len(entry_list) - 1
        target_index = 0

        entry_list.move(index, target_index)
        prefs.current_list_index = clamp(target_index, lower=0, upper=max_index)
        return{'FINISHED'}


class NODE_OT_NGLibrary_MoveEntry_toBottom(bpy.types.Operator):
    bl_idname = "nodegroup_library.move_entry_to_bottom"
    bl_label = ""
    bl_description = "Move an entry to the bottom of list"

    @classmethod
    def poll(cls, context):
        prefs = fetch_user_preferences()
        return prefs.current_list_index < len(prefs.entry_list) - 1

    def execute(self, context):
        prefs = fetch_user_preferences()
        entry_list = prefs.entry_list
        index = prefs.current_list_index
        max_index = len(entry_list) - 1
        target_index = max_index

        entry_list.move(index, target_index)
        prefs.current_list_index = clamp(target_index, lower=0, upper=max_index)
        return{'FINISHED'}


class NODE_OT_NGLibrary_ToggleAllEntries(bpy.types.Operator):
    bl_idname = "nodegroup_library.toggle_all_entries"
    bl_label = ""

    mode: EnumProperty(name="UI Mode", items=(
        ("ENABLE", "Enable", "Enables all .blend file entries"),
        ("DISABLE", "Disable", "Disable all .blend file entries"),
    ),)

    @classmethod
    def description(cls, context, props):
        return f"{props.mode.capitalize()}s all the .blend file entries in the list"

    @classmethod
    def poll(cls, context):
        prefs = fetch_user_preferences()
        return len(prefs.entry_list) > 0

    def execute(self, context):
        prefs = fetch_user_preferences()
        entry_list = prefs.entry_list
        should_enable = self.mode == "ENABLE"

        for item in entry_list:
            item.is_enabled = should_enable

        return{'FINISHED'}


class NODE_OT_NGLibrary_ResetEntryInfo(bpy.types.Operator):
    bl_idname = "nodegroup_library.reset_entry_info"
    bl_label = "Reset Entry Info"

    mode: EnumProperty(name="Mode", items=(
        ("NAMES", "Names", "Resets all names"),
        ("PREFIXES", "Prefixes", "Resets all prefixes"),
        ("BOTH", "Both", "Reset both"),
    ),)

    @classmethod
    def description(cls, context, props):
        mode = props.mode
        endpart = "the auto-generated version for every .blend file entry in the list"

        if mode == "BOTH":
            return f"Reset both names and prefixes to {endpart}"
        elif mode == "NAMES":
            return f"Reset names to {endpart}"
        elif mode == "PREFIXES":
            return f"Reset prefixes to {endpart}"

    @classmethod
    def poll(cls, context):
        prefs = fetch_user_preferences()
        return len(prefs.entry_list) > 0

    def execute(self, context):
        prefs = fetch_user_preferences()
        entry_list = prefs.entry_list

        if self.mode in ("NAMES", "BOTH"):
            for item in entry_list:
                item.name = Path(item.filepath).stem

        if self.mode in ("PREFIXES", "BOTH"):
            for item in entry_list:
                item.prefix = generate_prefix(item.name)

        return{'FINISHED'}


class NODE_MT_NGLibrary_UIList_BATCH_OPS(bpy.types.Menu):
    bl_label = "Batch Operations"
    bl_idname = "NODE_MT_NGLibrary_UIList_BATCH_OPS"

    def draw(self, context):
        layout = self.layout

        props = layout.operator("nodegroup_library.toggle_all_entries", text="Enable All")
        props.mode = "ENABLE"

        props = layout.operator("nodegroup_library.toggle_all_entries", text="Disable All")
        props.mode = "DISABLE"

        layout.separator()
        layout.operator("nodegroup_library.reset_entry_info", text="Reset All Names").mode = "NAMES"
        layout.operator("nodegroup_library.reset_entry_info", text="Reset All Prefixes").mode = "PREFIXES"
        layout.operator("nodegroup_library.reset_entry_info", text="Reset Both").mode = "BOTH"

        layout.separator()
        layout.operator("nodegroup_library.move_entry_to_top", text="Reorder to Top", icon='TRIA_UP_BAR')
        layout.operator("nodegroup_library.move_entry_to_bottom", text="Reorder to Bottom", icon='TRIA_DOWN_BAR')

        layout.separator()
        layout.operator("nodegroup_library.sort_all_entries", text="Sort All by Name", icon='SORTALPHA')
        layout.operator("nodegroup_library.remove_all_entries", text="Remove All Entries", icon='X')
        return


class NodegroupLibraryPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    entry_list: CollectionProperty(type=BlendFileEntry)
    current_list_index: IntProperty(name="", description="Currently selected .blend file entry", default=0)

    override_entry_info: BoolProperty(
        name='Override Name and Prefix',
        description='When enabled, name and prefix are regenerated from updated filepath',
        default=True)

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
        row.template_list("NODEGROUP_LIBRARY_UL_UIList", "The_List", self, "entry_list", self, "current_list_index")

        col = row.column(align=True)
        col.operator("nodegroup_library.new_entry", text="", icon='ADD')
        col.operator("nodegroup_library.remove_entry", text="", icon='REMOVE')

        col.separator(factor=1)
        col.menu("NODE_MT_NGLibrary_UIList_BATCH_OPS", text="", icon='DOWNARROW_HLT')

        col.separator(factor=1)
        col.operator("nodegroup_library.move_entry_up", text="", icon='TRIA_UP')
        col.operator("nodegroup_library.move_entry_down", text="", icon='TRIA_DOWN')

        if self.current_list_index >= 0 and self.entry_list:
            item = self.entry_list[self.current_list_index]
            col = layout.column()
            col.use_property_split = True

            row = col.row(align=True)
            row.prop(item, "name")
            row.operator("nodegroup_library.autogenerate_name", text="", icon='EVENT_A')
            row.separator(factor=1.35)

            row = col.row(align=True)
            row.prop(item, "filepath")
            row.operator("nodegroup_library.update_filepath", text="", icon='FILEBROWSER')
            row.separator(factor=1.35)

            col.separator(factor=0.15)
            row = col.row(align=True)
            row.separator(factor=2)
            row.prop(self, "override_entry_info")
            col.separator(factor=0.35)

            row = col.row(align=True)
            row.prop(item, "prefix")
            row.operator("nodegroup_library.autogenerate_prefix", text="", icon='EVENT_A')
            row.separator(factor=1.35)


def register():
    bpy.utils.register_class(BlendFileEntry)
    bpy.utils.register_class(NodegroupLibraryPreferences)
    bpy.utils.register_class(NODEGROUP_LIBRARY_UL_UIList)
    bpy.utils.register_class(NODE_OT_NGLibrary_NewEntry)
    bpy.utils.register_class(NODE_OT_NGLibrary_RemoveEntry)
    bpy.utils.register_class(NODE_OT_NGLibrary_RemoveAllEntries)
    bpy.utils.register_class(NODE_OT_NGLibrary_SortAllIEntries)
    bpy.utils.register_class(NODE_OT_NGLibrary_MoveEntry_Up)
    bpy.utils.register_class(NODE_OT_NGLibrary_MoveEntry_Down)
    bpy.utils.register_class(NODE_OT_NGLibrary_MoveEntry_toTop)
    bpy.utils.register_class(NODE_OT_NGLibrary_MoveEntry_toBottom)
    bpy.utils.register_class(NODE_OT_NGLibrary_UpdateFilepath)
    bpy.utils.register_class(NODE_OT_NGLibrary_AutogenerateName)
    bpy.utils.register_class(NODE_OT_NGLibrary_AutogeneratePrefix)
    bpy.utils.register_class(NODE_OT_NGLibrary_ToggleAllEntries)
    bpy.utils.register_class(NODE_OT_NGLibrary_ResetEntryInfo)
    bpy.utils.register_class(NODE_MT_NGLibrary_UIList_BATCH_OPS)

    prefs_handler.load_pref_cache()
    setattr(prefs_handler, "on_register", False)


def unregister():
    try:
        prefs_handler.update_pref_cache()
        setattr(prefs_handler, "on_register", True)
    finally:
        bpy.utils.unregister_class(BlendFileEntry)
        bpy.utils.unregister_class(NodegroupLibraryPreferences)
        bpy.utils.unregister_class(NODEGROUP_LIBRARY_UL_UIList)
        bpy.utils.unregister_class(NODE_OT_NGLibrary_NewEntry)
        bpy.utils.unregister_class(NODE_OT_NGLibrary_RemoveEntry)
        bpy.utils.unregister_class(NODE_OT_NGLibrary_RemoveAllEntries)
        bpy.utils.unregister_class(NODE_OT_NGLibrary_SortAllIEntries)
        bpy.utils.unregister_class(NODE_OT_NGLibrary_MoveEntry_Up)
        bpy.utils.unregister_class(NODE_OT_NGLibrary_MoveEntry_Down)
        bpy.utils.unregister_class(NODE_OT_NGLibrary_MoveEntry_toTop)
        bpy.utils.unregister_class(NODE_OT_NGLibrary_MoveEntry_toBottom)
        bpy.utils.unregister_class(NODE_OT_NGLibrary_UpdateFilepath)
        bpy.utils.unregister_class(NODE_OT_NGLibrary_AutogenerateName)
        bpy.utils.unregister_class(NODE_OT_NGLibrary_AutogeneratePrefix)
        bpy.utils.unregister_class(NODE_OT_NGLibrary_ToggleAllEntries)
        bpy.utils.unregister_class(NODE_OT_NGLibrary_ResetEntryInfo)
        bpy.utils.unregister_class(NODE_MT_NGLibrary_UIList_BATCH_OPS)