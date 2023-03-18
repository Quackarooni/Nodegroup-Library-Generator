import bpy
from pathlib import Path
import json
from .operators import NODE_OT_NODEGROUP_LIBRARY_append_group as append_nodegroup
from .operators import NodegroupLibrary_BaseMenu as NGL_BaseMenu

config_folder = Path(__file__).parent / "menu_configs"
config_files = list(config_folder.glob("*.json"))

menu_classes = []
menu_draw_funcs = []
spacing = 0.65
default_menu_text = "unnamed_menu"

def fetch_user_prefs(prop_name=None):
    ADD_ON_PATH = Path(__file__).parent.name
    prefs = bpy.context.preferences.addons[ADD_ON_PATH].preferences
    return prefs if (prop_name is None) else getattr(prefs, prop_name)

def append_submenu_to_parent(menu, icon):
    def draw(self, context):
        self.layout.menu(menu.bl_idname, icon=icon)
        
    menu_draw_funcs.append(draw)
    bpy.types.NODE_MT_nodegroup_library.append(draw)
    return draw

class NODE_MT_nodegroup_library(bpy.types.Menu):
    bl_label = "User Library"
    bl_idname = "NODE_MT_nodegroup_library"

    valid_nodetrees = []

    @classmethod
    def set_valid_nodetrees(cls):
        nodetrees = []
        for config in config_files:
            with open(config, "r") as f:
                config_dict = json.loads(f.read())

            nodetrees += list(config_dict['configs'].keys())

        cls.valid_nodetrees = list(set(nodetrees))

    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type in cls.valid_nodetrees

    def draw(self, context):
        pass

def draw_library_menu(self, context):
    if fetch_user_prefs("enable_parent_menu"):
        self.layout.menu("NODE_MT_nodegroup_library", icon='ASSET_MANAGER')
        
    elif context.space_data.tree_type in NODE_MT_nodegroup_library.valid_nodetrees:
        self.layout.separator(factor=spacing)
        self.layout.menu_contents("NODE_MT_nodegroup_library")

def generate_menu(filepath, menu_data, data_dict, tree_type):
    menu_idname, data = menu_data
    submenu_groups = data['items']['submenus']
    nodegroup_items = data['items']['nodegroups']
    nodegroups = data_dict['nodegroups']
    menus = data_dict['menus']

    def draw_compact(self, context):
        layout = self.layout

        for group in submenu_groups.values():
            layout.separator(factor=spacing)
            for submenu_idname in group:       
                icon = menus[submenu_idname].get('icon', 'NONE')
                layout.menu(submenu_idname, icon=icon)

        if submenu_groups and nodegroup_items:
            layout.separator(factor=spacing)

        for group_index, group in nodegroup_items.items():
            layout.separator(factor=spacing)
            for nodegroup in group:
                nodegroup_data = nodegroups[nodegroup]
                label = nodegroup_data['label']
                nodetree_name = nodegroup_data['node_tree']
                label = label if label != '' else nodetree_name
                
                props = layout.operator(append_nodegroup.bl_idname, text=label, icon=nodegroup_data.get("icon", 'NONE'))
                props.filepath = filepath
                props.group_name = nodetree_name
                props.width = nodegroup_data['width']
    
    def draw_expanded(self, context):
        layout = self.layout

        row = layout.row()
        for group_index, group in submenu_groups.items():
            if group_index != "null":
                col = row.column()

            for index, submenu_idname in enumerate(group):
                submenu_data = menus[submenu_idname]

                if group_index == "null":
                    col = row.column()
                elif index > 0:
                    col.separator(factor=spacing)

                label = submenu_data['label']
                icon = submenu_data.get('icon', 'NONE')
                if label != '' or icon != 'NONE' or not fetch_user_prefs("hide_empty_headers"):
                    text = label if label != '' else default_menu_text
                    col.label(text=text, icon=icon)
                    col.separator(factor=spacing)

                col.menu_contents(submenu_idname)

        if not nodegroup_items:
            return

        col = row.column()
        if submenu_groups:
            col.label(text="Misc.")
            col.separator(factor=spacing)

        for group_index, group in nodegroup_items.items():
            layout.separator(factor=spacing)
            for nodegroup in group:
                nodegroup_data = nodegroups[nodegroup]
                label = nodegroup_data['label']
                nodetree_name = nodegroup_data['node_tree']
                label = label if label != '' else nodetree_name
                
                props = col.operator(append_nodegroup.bl_idname, text=label, icon=nodegroup_data.get("icon", 'NONE'))
                props.filepath = filepath
                props.group_name = nodetree_name
                props.width = nodegroup_data['width']
        
    menu_class = type(menu_idname,(NGL_BaseMenu,),
        {
            "bl_idname": menu_idname,
            "bl_label": data['label'],
            "is_expandable": data['is_expandable'],
            "tree_type": tree_type,
            "draw_expanded": draw_expanded,
            "draw_compact": draw_compact,
        }
    )

    menu_classes.append(menu_class)
    bpy.utils.register_class(menu_class)

    if menu_idname.endswith('main'):
        append_submenu_to_parent(menu_class, icon=data.get('icon', 'NONE'))

def make_menus(config):
    with open(config, "r") as f:
        config_dict = json.loads(f.read())
    
    filepath = config_dict['filepath']

    for tree, data_dict in config_dict['configs'].items():
        for menu_data in data_dict['menus'].items():
            generate_menu(filepath=filepath, menu_data=menu_data, data_dict=data_dict, tree_type=tree)

def register():
    menu_classes.clear()
    menu_draw_funcs.clear()
       
    NODE_MT_nodegroup_library.set_valid_nodetrees()

    if not hasattr(bpy.types, "NODE_MT_nodegroup_library"):
        bpy.utils.register_class(NODE_MT_nodegroup_library)
        bpy.types.NODE_MT_add.append(draw_library_menu)

    for config in config_files:
        make_menus(config)

    return
    try:    
        if not hasattr(bpy.types, "NODE_MT_nodegroup_library"):
            bpy.utils.register_class(NODE_MT_nodegroup_library)
            bpy.types.NODE_MT_add.append(draw_library_menu)

        for config in config_files:
            make_menus(config)
    except:
        unregister()

def unregister():
    for draw_func in menu_draw_funcs:
        bpy.types.NODE_MT_nodegroup_library.remove(draw_func)
    for cls in menu_classes:
        bpy.utils.unregister_class(cls)
    
    if hasattr(bpy.types, "NODE_MT_nodegroup_library"):
        bpy.utils.unregister_class(NODE_MT_nodegroup_library)
        bpy.types.NODE_MT_add.remove(draw_library_menu)