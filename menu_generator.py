import bpy
from pathlib import Path
import json
from .operators import NODE_OT_NODEGROUP_LIBRARY_append_group as append_nodegroup

config_folder = Path(__file__).parent / "menu_configs"
config_files = list(config_folder.glob("*.json"))

parent_menus = []
menu_classes = []
menu_draw_funcs = []

def fetch_user_prefs(prop_name=None):
    ADD_ON_PATH = Path(__file__).parent.name
    prefs = bpy.context.preferences.addons[ADD_ON_PATH].preferences

    return prefs if (prop_name is None) else getattr(prefs, prop_name)

def draw_library_menu(self, context):
    if fetch_user_prefs("bool_prop"):
        self.layout.menu("NODE_MT_nodegroup_library", icon='ASSET_MANAGER')
    else:
        self.layout.menu_contents("NODE_MT_nodegroup_library")


def append_submenu_to_parent(menu):
    def draw(self, context):
        self.layout.menu(menu.bl_idname)
        
    menu_draw_funcs.append(draw)
    bpy.types.NODE_MT_nodegroup_library.append(draw)
    return draw

class NODE_MT_nodegroup_library(bpy.types.Menu):
    bl_label = "User Library"
    bl_idname = "NODE_MT_nodegroup_library"

    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == "GeometryNodeTree"

    def draw(self, context):
        pass

def generate_idname(menu_name, blendname):
    return f"NODEGROUP_LIBRARY_MT_{blendname}_{menu_name}"

def generate_menu(filepath, blendname, menu_name, data, nodegroups, menus):
    def draw_compact(self, context):
        layout = self.layout
        submenus = self.items['submenus']
        nodegroup_items = self.items['nodegroups']

        for menu in submenus:
            submenu_idname = generate_idname(menu, blendname)
            layout.menu(submenu_idname)

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

            submenu_idname = generate_idname(menu, blendname)
            col = row.column()
            col.label(text=label)
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

    menu_class = type(idname,(bpy.types.Menu,),
        {
            "bl_idname": idname,
            "bl_label": data['label'],
            "is_expandable": data['is_expandable'],
            "items": data['items'],
            "draw": draw,
        }
    )

    menu_classes.append(menu_class)
    bpy.utils.register_class(menu_class)

    if menu_name == 'main':
        append_submenu_to_parent(menu_class)

def make_menus(config):
    with open(config, "r") as f:
        config_dict = json.loads(f.read())

    filepath = config_dict['filepath']
    blendname = config.name.removesuffix('.json').replace(" ", "_").upper()

    for key, value in config_dict['menus'].items():
        generate_menu(filepath=filepath, blendname=blendname, menu_name=key, data=value, nodegroups=config_dict['nodegroups'], menus=config_dict['menus'])

def register():
    menu_classes.clear()
    menu_draw_funcs.clear()
       
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