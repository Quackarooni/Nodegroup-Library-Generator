import bpy
import re
from bpy.types import Operator
from bpy.props import StringProperty, FloatProperty
from pathlib import Path

class NodegroupLibrary_BaseMenu(bpy.types.Menu):
    tree_type: StringProperty()

    @classmethod
    def poll(cls, context):
        space = context.space_data
        is_node_editor = (space.type == 'NODE_EDITOR')
        is_exists = (space.node_tree is not None)
        is_valid = space.tree_type == cls.tree_type
        return all((is_node_editor, is_exists, is_valid))

class NODE_OT_NODEGROUP_LIBRARY_append_group(Operator):
    bl_idname = "nodegroup_library.append_group"
    bl_label = "Append Node Group"
    bl_description = "Append Node Group"
    bl_options = {"REGISTER", "UNDO"}

    group_name: StringProperty()
    tooltip: StringProperty()
    filepath: StringProperty()
    width: FloatProperty()

    # adapted from https://github.com/blender/blender/blob/master/release/scripts/startup/bl_operators/node.py
    @staticmethod
    def store_mouse_cursor(context, event):
        context.space_data.cursor_location_from_region(event.mouse_region_x, event.mouse_region_y)

    @classmethod
    def poll(cls, context):
        return context.space_data.type == 'NODE_EDITOR'

    @classmethod
    def description(self, context, props):
        return props.tooltip

    @staticmethod
    def remove_duplicate_imports(added_groups):
        for group in added_groups:
            for node in group.nodes:
                if node.type == "GROUP":
                    unduped_name, *_ = re.split("\.\d+$", node.node_tree.name)
                    node.node_tree = bpy.data.node_groups[unduped_name]
        for group in added_groups:
            split_name, *_ = re.split("\.\d+$", group.name)
        
            if len(_) > 0 and split_name in bpy.data.node_groups:
                bpy.data.node_groups.remove(group)


    def execute(self, context):
        if self.group_name not in bpy.data.node_groups:
            old_groups = set(bpy.data.node_groups)
            filepath = Path(self.filepath)
            with bpy.data.libraries.load(str(filepath), link=False) as (data_from, data_to):
                data_to.node_groups.append(self.group_name)

            added_groups = tuple(set(bpy.data.node_groups)-old_groups)

            if len(added_groups) > 1:
                self.remove_duplicate_imports(added_groups)

        bpy.ops.node.add_group(name=self.group_name)
        context.active_node.location = context.space_data.cursor_location
        context.active_node.width = self.width
        bpy.ops.node.translate_attach_remove_on_cancel("INVOKE_DEFAULT")
        return {"FINISHED"}
    
    def invoke(self, context, event):
        self.store_mouse_cursor(context, event)
        return self.execute(context)

classes = (
    NODE_OT_NODEGROUP_LIBRARY_append_group,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)