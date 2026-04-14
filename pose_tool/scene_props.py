import os

import bpy  # type: ignore[import-not-found]
from bpy.props import (  # type: ignore[import-not-found]
    BoolProperty,
    EnumProperty,
    PointerProperty,
    StringProperty,
)

from .constants import DEFAULT_PRESETS_PATH


def _sim_pt_preset_items(self, context):
    try:
        scene = context.scene if context else None
        if not scene:
            return []
        presets_path = getattr(scene, "sim_pt_presets_path", None)
        if not presets_path or not os.path.isdir(presets_path):
            return []
        return [(f, f, "") for f in os.listdir(presets_path) if f.endswith('.json')]
    except Exception:
        return []


def register_properties():
    bpy.types.Scene.sim_pt_use_rotation = BoolProperty(name="Use Rotation", default=True)
    bpy.types.Scene.sim_pt_use_location = BoolProperty(name="Use Location", default=True)
    bpy.types.Scene.sim_pt_use_scale = BoolProperty(name="Use Scale", default=True)
    bpy.types.Scene.sim_pt_settings_expanded = BoolProperty(name="Settings Expanded", default=True)
    bpy.types.Scene.sim_pt_apply_to_all_bones = BoolProperty(name="Apply to All Bones", default=False)
    bpy.types.Scene.sim_pt_presets_path = StringProperty(
        name="Presets Path",
        description="Path to the folder containing pose presets",
        default=DEFAULT_PRESETS_PATH,
        subtype='DIR_PATH'
    )
    bpy.types.Scene.sim_pt_presets_expanded = BoolProperty(name="Presets Expanded", default=True)
    bpy.types.Scene.sim_pt_selected_armature = PointerProperty(
        name="Selected Armature",
        description="Armature to work with",
        type=bpy.types.Object,
        poll=lambda self, obj: obj.type == 'ARMATURE'
    )
    bpy.types.Scene.sim_pt_selected_preset = EnumProperty(
        name="Preset",
        description="Select a preset to load",
        items=_sim_pt_preset_items
    )


def unregister_properties():
    del bpy.types.Scene.sim_pt_use_rotation
    del bpy.types.Scene.sim_pt_use_location
    del bpy.types.Scene.sim_pt_use_scale
    del bpy.types.Scene.sim_pt_settings_expanded
    del bpy.types.Scene.sim_pt_apply_to_all_bones
    del bpy.types.Scene.sim_pt_presets_path
    del bpy.types.Scene.sim_pt_presets_expanded
    del bpy.types.Scene.sim_pt_selected_armature
    del bpy.types.Scene.sim_pt_selected_preset
