import bpy
from pathlib import Path
import json
from .operators import NODE_OT_NODEGROUP_LIBRARY_append_group as append_nodegroup
from .operators import NodegroupLibrary_BaseMenu as NGL_BaseMenu

config_folder = Path(__file__).parent / "menu_configs"
config_files = list(config_folder.glob("*.json"))

parent_menus = []
menu_classes = []
menu_draw_funcs = []

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
        #return True
        return context.space_data.tree_type in cls.valid_nodetrees

    def draw(self, context):
        pass

def draw_library_menu(self, context):
    if fetch_user_prefs("bool_prop"):
        self.layout.menu("NODE_MT_nodegroup_library", icon='ASSET_MANAGER')
    else:
        if context.space_data.tree_type in NODE_MT_nodegroup_library.valid_nodetrees:
            print(NODE_MT_nodegroup_library.valid_nodetrees)
            self.layout.separator(factor=1)
            self.layout.menu_contents("NODE_MT_nodegroup_library")

def generate_idname(menu_name, blendname):
    abbr = "".join(chars[0] for chars in blendname.split("_")[:10])
    idname = f"NODEGROUP_LIBRARY_MT_{abbr}_{menu_name}"
    return idname

def generate_menu(filepath, blendname, menu_name, data, nodegroups, menus, tree_type):
    def draw_compact(self, context):
        layout = self.layout
        submenus = self.items['submenus']
        nodegroup_items = self.items['nodegroups']

        for menu in submenus:
            icon = menus[menu].get('icon', 'NONE')
            submenu_idname = generate_idname(menu, blendname)
            layout.menu(submenu_idname, icon=icon)

        if submenus and nodegroup_items:
            layout.separator(factor=1)

        for nodegroup in nodegroup_items:
            nodegroup_data = nodegroups[nodegroup]
            label = nodegroup_data['label']
            nodetree_name = nodegroup_data['node_tree']
            label = label if label != '' else nodetree_name
            
            props = layout.operator(append_nodegroup.bl_idname, text=label)
            props.filepath = filepath
            props.group_name = nodetree_name
            props.width = nodegroup_data['width']
    
    def draw_expanded(self, context):
        layout = self.layout
        submenus = self.items['submenus']
        nodegroup_items = self.items['nodegroups']

        row = layout.row()
        for menu in submenus:
            submenu_data = menus[menu]
            label = submenu_data['label']
            icon = submenu_data.get('icon', 'NONE')

            submenu_idname = generate_idname(menu, blendname)
            col = row.column()
            col.label(text=label, icon=icon)
            col.separator(factor=1)
            col.menu_contents(submenu_idname)

        if not nodegroup_items:
            return

        col = row.column()
        if submenus:
            col.label(text="Misc.")
            col.separator(factor=1)

        for nodegroup in nodegroup_items:
            nodegroup_data = nodegroups[nodegroup]
            label = nodegroup_data['label']
            nodetree_name = nodegroup_data['node_tree']
            label = label if label != '' else nodetree_name
            
            props = col.operator(append_nodegroup.bl_idname, text=label)
            props.filepath = filepath
            props.group_name = nodetree_name
            props.width = nodegroup_data['width']
        
    def draw(self, context):
        if self.is_expandable:
            draw_expanded(self, context)
        else:
            draw_compact(self, context)
        return
    
    idname = generate_idname(menu_name, blendname)

    menu_class = type(idname,(NGL_BaseMenu,),
        {
            "bl_idname": idname,
            "bl_label": data['label'],
            "is_expandable": data['is_expandable'],
            "items": data['items'],
            "tree_type": tree_type,
            "draw": draw,
        }
    )

    menu_classes.append(menu_class)
    bpy.utils.register_class(menu_class)

    if menu_name.endswith('main'):
        append_submenu_to_parent(menu_class, icon=data.get('icon', 'NONE'))

def make_menus(config):
    with open(config, "r") as f:
        config_dict = json.loads(f.read())
    
    filepath = config_dict['filepath']
    blendname = config.name.removesuffix('.json').replace(" ", "_").upper()

    for tree, data_dict in config_dict['configs'].items():
        for key, value in data_dict['menus'].items():
            generate_menu(filepath=filepath, blendname=blendname, menu_name=key, data=value, nodegroups=data_dict['nodegroups'], menus=data_dict['menus'], tree_type=tree)

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