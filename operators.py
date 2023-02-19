import bpy
from bpy.types import Operator

addon_name = "Addon Name"
def fetch_user_preferences():
    return bpy.context.preferences.addons[addon_name].preferences

def get_selected_nodes(context):
    tree = context.space_data.node_tree

    if tree.nodes.active:
        while tree.nodes.active != context.active_node:
            tree = tree.nodes.active.node_tree

    nodes = tree.nodes
    return (tuple(node for node in nodes if node.select and node.bl_static_type != 'FRAME'), nodes.active)


class NodegroupLibraryBase:
    bl_label = "Base Operator"
    bl_options = {'REGISTER', 'UNDO_GROUPED'} 

    @classmethod
    def poll(cls, context):
        space = context.space_data
        valid_trees = ("ShaderNodeTree", "CompositorNodeTree", "TextureNodeTree", "GeometryNodeTree")
        is_node_editor = (space.type == 'NODE_EDITOR')
        is_exists = (space.node_tree is not None)
        is_valid = (space.tree_type in valid_trees)
        return all((is_node_editor, is_exists, is_valid))

classes = (
    #NodegroupLibraryBase,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)