import bpy
import json
from bpy.types import Operator
from bpy.app.handlers import persistent
from pathlib import Path
from . import menu_generator
from .global_data import icon_list

config_folder = Path(__file__).parent / "blendfiles"
valid_filepaths = list(path.resolve() for path in config_folder.glob("*.blend"))

@persistent
def execute_on_save(dummy):
    file_in_folder = any(list((Path(bpy.data.filepath) == path) for path in valid_filepaths))

    if file_in_folder:
        bpy.ops.nodegroup_library.update_json('EXEC_DEFAULT')
        menu_generator.unregister()
        menu_generator.register()

class NODEGROUP_LIBRARY_UPDATE_JSON_CONFIGS(Operator):
    bl_label = "Update JSON Files"
    bl_idname = "nodegroup_library.update_json"
    bl_description = "Updates the JSON Config files for menu generation"
    bl_options = {"REGISTER"}

    @staticmethod
    def RAISE_ERROR(error_message):
        def display_error(self, context):
            for index, line in enumerate(error_message.splitlines()):
                icon = 'CANCEL' if (index == 0) else 'NONE'
                self.layout.label(text=line, icon=icon)
        
        bpy.context.window_manager.popup_menu(display_error, title='Report: Error')
        raise ValueError(error_message)

    @staticmethod
    def fetch_nodetrees():
        data = bpy.data
        nodetrees = []

        #===== COMPOSITOR NODETREE =====
        scene = data.scenes.get('Nodegroup Library')
        if hasattr(scene, "node_tree") and (scene.node_tree is not None):
            compositor_tree = scene.node_tree
            nodetrees.append(compositor_tree)

        #===== SHADER NODETREE =====
        material = data.materials.get('Nodegroup Library')
        if hasattr(material, "node_tree") and (material.node_tree is not None):
            shader_tree = material.node_tree
            nodetrees.append(shader_tree)

        #===== GEOMETRY NODETREE =====
        nodegroup = data.node_groups.get('Nodegroup Library')
        if hasattr(nodegroup, 'bl_idname'):
            if nodegroup.bl_idname == 'GeometryNodeTree':
                geonodes_tree = nodegroup
                nodetrees.append(geonodes_tree)
            else:
                raise Exception("Nodegroup that isn't of type GeometryNodeTree is named 'Nodegroup Library'")

        #===== TEXTURE NODETREE =====
        texture = data.textures.get('Nodegroup Library')
        if hasattr(texture, 'node_tree'):
            if hasattr(texture.node_tree, "nodes") and (texture.node_tree is not None):
                texture_nodes_tree = texture.node_tree
                nodetrees.append(texture_nodes_tree)

        return nodetrees

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        bpy.ops.outliner.orphans_purge(do_recursive=True)
        filepath = Path(bpy.data.filepath)

        main_name = filepath.name.removesuffix(".blend")
        abbr = "".join(chars[0] for chars in main_name.replace(" ", "_").split("_")[:10])

        nodetrees = self.fetch_nodetrees()

        def name_hash(menu_name, prefix):
            hashed_name = str(hash(f'{main_name}{menu_name}'))
            if hashed_name.startswith("-"):
                hashed_name = hashed_name.replace("-","1")
            hashed_name = hex(int(hashed_name))
            return generate_idname(hashed_name, prefix)

        def generate_idname(name, prefix):
            return f'NODEGROUP_LIBRARY_MT_{abbr}_{prefix.upper()}_{name}'

        supported_variables = {
            'ICON' : "string",
            'GROUP_INDEX' : "int",
            'SORT_INDEX' : "int",
        }

        #===== MENUS=====  
        def generate_config(nodetree):
            nodes = nodetree.nodes
            tree_type = nodetree.bl_idname
            
            prefix_dict = {
                "GeometryNodeTree" : "GEO",
                "ShaderNodeTree" : "SHAD",
                "CompositorNodeTree" : "COMP",
                "TextureNodeTree" : "TEX",
            }
            
            prefix = prefix_dict.get(nodetree.bl_idname, "NULL")
            main = generate_idname("main", prefix)

            nodegroups = {}
            menus = {
                main: {
                    'label': main_name,
                    'items': {'submenus': [] , 'nodegroups': []}, 
                    }
            }
            property_frames = {}
            
            def is_property_frame(node):
                if node is None:
                    return False
                
                return node.use_custom_color and tuple(node.color) == (0.0, 1.0, 1.0)
            
            frames = [node for node in nodes if node.bl_label == 'Frame' and not is_property_frame(node)]
            prop_frames = [node for node in nodes if node.bl_label == 'Frame' and is_property_frame(node)]
            groups = [node for node in nodes if node.bl_label == 'Group']
            variables = [node for node in nodes if node.bl_label == 'Value' and node.mute is False]
            
            for node in prop_frames:
                if is_property_frame(node.parent):
                    error_message = f"PropertyFrame cannot be nested inside another PropertyFrame. \nError at: '{node.label}' - {node}"
                    self.RAISE_ERROR(error_message)

                name = name_hash(node.name, prefix)
                property_frames[name] = {}
                
            for node in frames:
                name = name_hash(node.name, prefix)
                parent = name_hash(node.parent.name, prefix) if node.parent is not None else None

                menus[name] = {
                    'label': node.label,
                    'items': {'submenus': [] , 'nodegroups': []}, 
                    }
                    
                if parent is not None:
                    menus[parent]['items']['submenus'].append(name)
                else:
                    menus[main]['items']['submenus'].append(name)    
                    
            for node in variables:
                data = node.label.strip().split(":")
                if len(data) != 2:
                    error_message = f"Invalid variable data, labels should contain exactly one semicolon. \nError at: '{node.label}' - {node}"
                    self.RAISE_ERROR(error_message)
                var_name, value = (value.strip() for value in data)

                var_type = supported_variables.get(var_name)
                if var_type is None:
                    error_message = f"'{var_name}' is not a valid variable name. \nError at: '{node.label}' - {node}"
                    self.RAISE_ERROR(error_message)
                
                
                if var_name == 'ICON':
                    value = value.strip().replace("'", "").replace('"', '').upper()
                    if value not in icon_list:
                        error_message = f"'{value}' is not a valid icon name. \nError at: '{node.label}' - {node}"
                        self.RAISE_ERROR(error_message)
                    
                    node.label = f"{var_name}: {value}"
                    node.show_options = False
                    for socket in node.outputs:
                        socket.hide = True
                    
                elif var_name == 'GROUP_INDEX':
                    if not value.isdigit():
                        error_message = f"GROUP_INDEX '{value}' is not a non-negative integer. \nError at: '{node.label}' - {node}"
                        self.RAISE_ERROR(error_message)
                    else:
                        value = int(value)
                        node.label = f"{var_name}: {value}"
                        node.show_options = False
                        for socket in node.outputs:
                            socket.hide = True
                
                parent = name_hash(node.parent.name, prefix) if node.parent is not None else main
                var_lookup = var_name.strip().lower().replace(" ", "_")
                
                if not is_property_frame(node.parent):
                    variable = menus[parent].get(var_lookup)
                    if variable is not None:
                        error_message = f"Variable '{var_name}' has been defined multiple times for menu {parent}. \nError at: '{node.label}' - {node}"
                        self.RAISE_ERROR(error_message)
                    menus[parent][var_lookup] = value
                else:
                    variable = property_frames[parent].get(var_lookup)         
                    if variable is not None:
                        error_message = f"Variable '{var_name}' has been defined multiple times for property frame {parent}. \nError at: '{node.label}' - {node}"
                        self.RAISE_ERROR(error_message)
                
                    property_frames[parent][var_lookup] = value
                    

            for node in groups:
                name = name_hash(node.name, prefix)
                label = node.label

                parent = name_hash(node.parent.name, prefix) if node.parent is not None else None
                
                extra_data = {}
                if is_property_frame(node.parent):
                    extra_data = property_frames[parent]
                    parent = name_hash(node.parent.parent.name, prefix) if node.parent.parent is not None else None
                    
                default_data = {
                    'label' : label,
                    'width' : node.width,
                    'node_tree' : node.node_tree.name,
                }
            
                nodegroups[name] = default_data | extra_data

                if parent is not None:
                    menus[parent]['items']['nodegroups'].append(name)
                else:
                    menus[main]['items']['nodegroups'].append(name)              

            for value in menus.values():
                does_children_have_submenu = list(len(menus[submenu]['items']['submenus']) == 0 for submenu in value['items']['submenus'])
                is_expandable = all(does_children_have_submenu) and len(does_children_have_submenu) != 0
                value['is_expandable'] = is_expandable
                submenus = value['items']['submenus']
            
                submenu_dict = {}
            
                submenus.sort(key=lambda _: menus[_]['label'])
                value['items']['nodegroups'].sort(key=lambda _: nodegroups[_]['node_tree'])
            
                for submenu in submenus:
                    group_index = menus[submenu].get('group_index', None)
                    group_index_val = submenu_dict.get(group_index)
                    
                    if group_index_val is None:
                        submenu_dict[group_index] = [submenu,]
                    else:
                        group_index_val.append(submenu)
                        
                sorted_dict = {i:submenu_dict[i] for i in sorted(submenu_dict, key=lambda _: str(_))}
                value['items']['submenus'] = sorted_dict
                
            return tree_type, menus, nodegroups

        tree_configs = {}
        for tree in nodetrees:
            if len([node for node in tree.nodes if node.bl_label in ('Group', 'Frame')]) > 0:
                tree_type, menus, nodegroups = generate_config(tree)
                tree_configs[tree_type] = {'menus': menus, 'nodegroups': nodegroups}


        output = {'filepath' : str(filepath), 'configs': tree_configs}
        cache_path = filepath.parent.parent / "menu_configs" / f"{main_name}.json"

        with open(cache_path, "w") as fp:
            json.dump(output, fp=fp, indent=4)

        self.report({'INFO'}, "Successfully update menu configs")
        return {'FINISHED'}


def register():
    bpy.utils.register_class(NODEGROUP_LIBRARY_UPDATE_JSON_CONFIGS)
    bpy.app.handlers.save_post.append(execute_on_save)

def unregister():
    bpy.utils.unregister_class(NODEGROUP_LIBRARY_UPDATE_JSON_CONFIGS)
    bpy.app.handlers.save_post.remove(execute_on_save)