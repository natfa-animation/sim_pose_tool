bl_info = {
    "name": "SIM posetool",
    "author": "Sokerov",
    "version": (1, 27),
    "blender": (4, 3, 2),
    "category": "SIM anima",
    "description": "A tool for managing, interpolating, and loading pose presets in Blender",
}

from typing import TYPE_CHECKING

import bpy  # type: ignore[import-not-found]
from bpy.props import CollectionProperty, StringProperty  # type: ignore[import-not-found]

from .constants import DEFAULT_PRESETS_PATH
from .operators_io import PT_OT_ExportPoses, PT_OT_ImportPoses, PT_OT_LoadPreset, PT_OT_MergePoses
from .operators_pose import (
    PT_OT_CreatePoseGroup,
    PT_OT_DeletePose,
    PT_OT_DeletePoseGroup,
    PT_OT_DeletePoses,
    PT_OT_DuplicatePose,
    PT_OT_RecordPose,
    PT_OT_SelectPoseBones,
    PT_OT_ToggleApplyToAllBones,
    PT_OT_ToggleLocation,
    PT_OT_ToggleRotation,
    PT_OT_ToggleScale,
    PT_OT_UpdatePose,
)
from .operators_progress import (
    PT_OT_CancelProgressPreview,
    PT_OT_ConfirmProgressPreview,
    PT_OT_ResetProgress,
    PT_OT_SetProgress_Minus01,
    PT_OT_SetProgress_Minus025,
    PT_OT_SetProgress_Minus1,
    PT_OT_SetProgress_Plus01,
    PT_OT_SetProgress_Plus025,
    PT_OT_SetProgress_Plus1,
    PT_OT_TogglePoseMirror,
    PT_OT_TogglePoseMode,
)
from .props_types import PTBonePoseData, PTPoseGroup, PTPoseItem
from .scene_props import register_properties, unregister_properties
from .ui_panel import PTPosePanel


class PTPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__
    if TYPE_CHECKING:
        presets_path: str
    else:
        __annotations__ = {
            "presets_path": StringProperty(
                name="Presets Path",
                description="Default path to the folder containing pose presets",
                default=DEFAULT_PRESETS_PATH,
                subtype="DIR_PATH",
            )
        }

    def draw(self, context):
        layout = self.layout
        layout.label(text="SIM posetool Settings")
        layout.prop(self, "presets_path", text="Default Presets Path")


CLASSES = (
    PTBonePoseData,
    PTPoseItem,
    PTPoseGroup,
    PTPosePanel,
    PTPreferences,
    PT_OT_RecordPose,
    PT_OT_DeletePoses,
    PT_OT_ExportPoses,
    PT_OT_ImportPoses,
    PT_OT_MergePoses,
    PT_OT_TogglePoseMode,
    PT_OT_TogglePoseMirror,
    PT_OT_ResetProgress,
    PT_OT_UpdatePose,
    PT_OT_SelectPoseBones,
    PT_OT_ToggleApplyToAllBones,
    PT_OT_ToggleRotation,
    PT_OT_ToggleLocation,
    PT_OT_ToggleScale,
    PT_OT_DeletePose,
    PT_OT_CreatePoseGroup,
    PT_OT_DeletePoseGroup,
    PT_OT_DuplicatePose,
    PT_OT_LoadPreset,
    PT_OT_SetProgress_Minus1,
    PT_OT_SetProgress_Minus025,
    PT_OT_SetProgress_Minus01,
    PT_OT_SetProgress_Plus01,
    PT_OT_SetProgress_Plus025,
    PT_OT_SetProgress_Plus1,
    PT_OT_ConfirmProgressPreview,
    PT_OT_CancelProgressPreview,
)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)
        if cls is PTPoseGroup:
            bpy.types.Armature.sim_pt_poses = CollectionProperty(type=PTPoseItem)
            bpy.types.Armature.sim_pt_pose_groups = CollectionProperty(type=PTPoseGroup)
            register_properties()


def unregister():
    bpy.utils.unregister_class(PTPosePanel)
    bpy.utils.unregister_class(PTPreferences)
    for cls in CLASSES[5:]:
        bpy.utils.unregister_class(cls)
    unregister_properties()
    if hasattr(bpy.types.Armature, "sim_pt_poses"):
        for armature in bpy.data.armatures:
            if hasattr(armature, "sim_pt_poses"):
                armature.sim_pt_poses.clear()
        del bpy.types.Armature.sim_pt_poses
    if hasattr(bpy.types.Armature, "sim_pt_pose_groups"):
        for armature in bpy.data.armatures:
            if hasattr(armature, "sim_pt_pose_groups"):
                armature.sim_pt_pose_groups.clear()
        del bpy.types.Armature.sim_pt_pose_groups
    bpy.utils.unregister_class(PTPoseGroup)
    bpy.utils.unregister_class(PTPoseItem)
    bpy.utils.unregister_class(PTBonePoseData)
