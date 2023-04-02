import bpy
import json
from pathlib import Path
from bpy.props import StringProperty
from bpy_extras.io_utils import ImportHelper, ExportHelper

cache_path = Path(__file__).parent / "userprefs.json"
on_register = True

def fetch_user_preferences():
    return bpy.context.preferences.addons[__package__].preferences

def load_pref_cache():
    try:
        set_preference_values(cache_path)
    except Exception:
        save_pref_cache(cache_path)

def set_preference_values(filepath=None):
    prefs = fetch_user_preferences()
    entry_list = prefs.entry_list

    with open(filepath, "r") as f:
        pref_defaults = json.loads(f.read())

    for key, value in pref_defaults.items():
        if key == "entry_list":
            for entry in value:
                item = entry_list.add()
                for key, value in entry.items():
                    setattr(item, key, value)
        else:
            setattr(prefs, key, value)
    
def update_pref_cache(self = None, context = None):
    if not on_register:
        save_pref_cache(cache_path)

def save_pref_cache(filepath=None):
    userprefs = fetch_user_preferences()
    pref_ids = set(dir(userprefs)) - {'__annotations__', '__dict__', '__doc__', '__module__', 
        '__weakref__', 'bl_idname', 'bl_rna', 'draw', 'rna_type'}
    pref_dict = {}

    for pref_id in pref_ids:
        pref_value = getattr(userprefs, pref_id)

        try:
            if not isinstance(pref_value, str):
                pref_value = tuple(pref_value)
        except TypeError:
            pass

        if pref_id == "entry_list":
            pref_value = [{
                "name": i.name, 
                "prefix": i.prefix, 
                "filepath": i.filepath, 
                "is_enabled" : i.is_enabled
                } for i in pref_value]

        pref_dict[pref_id] = pref_value
    
    with open(filepath, "w") as fp:
        json.dump(pref_dict, fp=fp, indent=4)

class JSON_LoaderTemplate(bpy.types.Operator, ImportHelper):
    bl_label = "Load Preferences"
    bl_idname = "nd_utils.prefs_loadpreferences"
    bl_description = "Loads preference settings from specified JSON file. (Does not include keymaps)"
    bl_options = {'UNDO'}

    filename_ext = '.json'
    filter_glob: StringProperty(default='*.json', options={'HIDDEN'})

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        filepath = Path(self.properties.filepath)
        with open(cache_path, "r") as f:
            cache_dict = json.loads(f.read())

        if filepath == cache_path:
            relative_path = filepath.relative_to(filepath.parent.parent)
            self.report({'ERROR'}, f"{relative_path} is a protected file. It cannot be imported.")
        else:
            try:
                set_preference_values(filepath=filepath)
                self.report({'INFO'}, f"File succesfully written at {filepath}")

            except Exception as error:
                self.report({'ERROR'}, f"Failed to load data from {filepath} \n{type(error).__name__}: {error}")
                with open(cache_path, "w") as fp:
                    json.dump(cache_dict, fp=fp, indent=4)
                load_pref_cache()
            
        return {'FINISHED'}

class JSON_SaverTemplate(bpy.types.Operator, ExportHelper):
    bl_label = "Save Preferences"
    bl_description = "Save preference settings to a JSON file. (Does not include keymaps)"
    bl_options = {'UNDO'}

    filename_ext = '.json'
    filter_glob: StringProperty(default='*.json', options={'HIDDEN'})

    check_existing = True
    use_filter_folder = True
    
    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        filepath = Path(self.properties.filepath)

        if filepath == cache_path:
            self.report({'ERROR'}, f"Cannot overwrite addon's cache JSON file.")

        elif filepath.parent == cache_path.parent:
            self.report({'ERROR'}, f"Cannot save files in addon's folder location.")

        else:
            try:
                save_pref_cache(filepath=filepath)
                self.report({'INFO'}, f"File succesfully written at {filepath}")
            except Exception:
                self.report({'ERROR'}, f"Failed to write data at {filepath}")

        return {'FINISHED'}
