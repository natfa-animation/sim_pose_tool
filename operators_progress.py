from typing import TYPE_CHECKING

import bpy  # type: ignore[import-not-found]
from bpy.props import IntProperty  # type: ignore[import-not-found]

from . import core_apply
from .core_apply import update_pose


class PT_OT_TogglePoseMirror(bpy.types.Operator):
    bl_idname = "pt.toggle_pose_mirror"
    bl_label = "Toggle Pose Mirror"
    bl_description = "Toggle mirror mode for the selected pose"
    if TYPE_CHECKING:
        pose_index: int
    else:
        __annotations__ = {"pose_index": IntProperty()}

    def execute(self, context):
        armature = context.scene.sim_pt_selected_armature if context.scene.sim_pt_selected_armature else context.active_object
        if not armature or self.pose_index >= len(armature.data.sim_pt_poses):
            self.report({'ERROR'}, "Invalid pose index or no armature selected")
            return {'CANCELLED'}
        pose = armature.data.sim_pt_poses[self.pose_index]
        pose.is_mirrored = not pose.is_mirrored
        bpy.ops.ed.undo_push(message=f"Toggle mirror for pose '{pose.name}' to {'on' if pose.is_mirrored else 'off'}")
        return {'FINISHED'}


class PT_OT_SetProgress_Minus1(bpy.types.Operator):
    bl_idname = "pt.set_progress_minus1"
    bl_label = "-1"
    bl_description = "Set pose progress to -100%"
    if TYPE_CHECKING:
        pose_index: int
    else:
        __annotations__ = {"pose_index": IntProperty()}

    def execute(self, context):
        armature = context.scene.sim_pt_selected_armature if context.scene.sim_pt_selected_armature else context.active_object
        if not armature or self.pose_index >= len(armature.data.sim_pt_poses):
            self.report({'ERROR'}, "Invalid pose index or no armature selected")
            return {'CANCELLED'}
        pose = armature.data.sim_pt_poses[self.pose_index]
        pose.combined_progress = -1.0
        bpy.ops.ed.undo_push(message=f"Set pose '{pose.name}' progress to -1")
        return {'FINISHED'}


class PT_OT_SetProgress_Minus025(bpy.types.Operator):
    bl_idname = "pt.set_progress_minus025"
    bl_label = "-0.25"
    bl_description = "Set pose progress to -25%"
    if TYPE_CHECKING:
        pose_index: int
    else:
        __annotations__ = {"pose_index": IntProperty()}

    def execute(self, context):
        armature = context.scene.sim_pt_selected_armature if context.scene.sim_pt_selected_armature else context.active_object
        if not armature or self.pose_index >= len(armature.data.sim_pt_poses):
            self.report({'ERROR'}, "Invalid pose index or no armature selected")
            return {'CANCELLED'}
        pose = armature.data.sim_pt_poses[self.pose_index]
        pose.combined_progress = -0.25
        bpy.ops.ed.undo_push(message=f"Set pose '{pose.name}' progress to -0.25")
        return {'FINISHED'}


class PT_OT_SetProgress_Minus01(bpy.types.Operator):
    bl_idname = "pt.set_progress_minus01"
    bl_label = "-0.1"
    bl_description = "Set pose progress to -10%"
    if TYPE_CHECKING:
        pose_index: int
    else:
        __annotations__ = {"pose_index": IntProperty()}

    def execute(self, context):
        armature = context.scene.sim_pt_selected_armature if context.scene.sim_pt_selected_armature else context.active_object
        if not armature or self.pose_index >= len(armature.data.sim_pt_poses):
            self.report({'ERROR'}, "Invalid pose index or no armature selected")
            return {'CANCELLED'}
        pose = armature.data.sim_pt_poses[self.pose_index]
        pose.combined_progress = -0.1
        bpy.ops.ed.undo_push(message=f"Set pose '{pose.name}' progress to -0.1")
        return {'FINISHED'}


class PT_OT_SetProgress_Plus01(bpy.types.Operator):
    bl_idname = "pt.set_progress_plus01"
    bl_label = "+0.1"
    bl_description = "Set pose progress to +10%"
    if TYPE_CHECKING:
        pose_index: int
    else:
        __annotations__ = {"pose_index": IntProperty()}

    def execute(self, context):
        armature = context.scene.sim_pt_selected_armature if context.scene.sim_pt_selected_armature else context.active_object
        if not armature or self.pose_index >= len(armature.data.sim_pt_poses):
            self.report({'ERROR'}, "Invalid pose index or no armature selected")
            return {'CANCELLED'}
        pose = armature.data.sim_pt_poses[self.pose_index]
        pose.combined_progress = 0.1
        bpy.ops.ed.undo_push(message=f"Set pose '{pose.name}' progress to +0.1")
        return {'FINISHED'}


class PT_OT_SetProgress_Plus025(bpy.types.Operator):
    bl_idname = "pt.set_progress_plus025"
    bl_label = "+0.25"
    bl_description = "Set pose progress to +25%"
    if TYPE_CHECKING:
        pose_index: int
    else:
        __annotations__ = {"pose_index": IntProperty()}

    def execute(self, context):
        armature = context.scene.sim_pt_selected_armature if context.scene.sim_pt_selected_armature else context.active_object
        if not armature or self.pose_index >= len(armature.data.sim_pt_poses):
            self.report({'ERROR'}, "Invalid pose index or no armature selected")
            return {'CANCELLED'}
        pose = armature.data.sim_pt_poses[self.pose_index]
        pose.combined_progress = 0.25
        bpy.ops.ed.undo_push(message=f"Set pose '{pose.name}' progress to +0.25")
        return {'FINISHED'}


class PT_OT_SetProgress_Plus1(bpy.types.Operator):
    bl_idname = "pt.set_progress_plus1"
    bl_label = "+1"
    bl_description = "Set pose progress to +100%"
    if TYPE_CHECKING:
        pose_index: int
    else:
        __annotations__ = {"pose_index": IntProperty()}

    def execute(self, context):
        armature = context.scene.sim_pt_selected_armature if context.scene.sim_pt_selected_armature else context.active_object
        if not armature or self.pose_index >= len(armature.data.sim_pt_poses):
            self.report({'ERROR'}, "Invalid pose index or no armature selected")
            return {'CANCELLED'}
        pose = armature.data.sim_pt_poses[self.pose_index]
        pose.combined_progress = 1.0
        bpy.ops.ed.undo_push(message=f"Set pose '{pose.name}' progress to +1")
        return {'FINISHED'}


class PT_OT_TogglePoseMode(bpy.types.Operator):
    bl_idname = "pt.toggle_pose_mode"
    bl_label = "Toggle Pose Mode"
    bl_description = "Switch between relative and absolute pose mode"
    if TYPE_CHECKING:
        pose_index: int
    else:
        __annotations__ = {"pose_index": IntProperty()}

    def execute(self, context):
        armature = context.scene.sim_pt_selected_armature if context.scene.sim_pt_selected_armature else context.active_object
        if not armature or self.pose_index >= len(armature.data.sim_pt_poses):
            self.report({'ERROR'}, "Invalid pose index or no armature selected")
            return {'CANCELLED'}
        pose = armature.data.sim_pt_poses[self.pose_index]
        pose.is_relative = not pose.is_relative
        bpy.ops.ed.undo_push(message=f"Toggle pose '{pose.name}' mode to {'relative' if pose.is_relative else 'absolute'}")
        return {'FINISHED'}


class PT_OT_ResetProgress(bpy.types.Operator):
    bl_idname = "pt.reset_progress"
    bl_label = "Reset Progress"
    bl_description = "Reset pose progress to default"
    if TYPE_CHECKING:
        pose_index: int
    else:
        __annotations__ = {"pose_index": IntProperty()}

    def execute(self, context):
        armature = context.scene.sim_pt_selected_armature if context.scene.sim_pt_selected_armature else context.active_object
        if not armature or self.pose_index >= len(armature.data.sim_pt_poses):
            self.report({'ERROR'}, "Invalid pose index or no armature selected")
            return {'CANCELLED'}
        pose = armature.data.sim_pt_poses[self.pose_index]
        if pose.combined_progress != 0.1:
            pose.combined_progress = 0.1
            update_pose(pose, context)
            bpy.ops.ed.undo_push(message=f"Reset pose '{pose.name}' progress")
        return {'FINISHED'}


class PT_OT_ConfirmProgressPreview(bpy.types.Operator):
    bl_idname = "pt.confirm_progress_preview"
    bl_label = "Confirm Preview"
    bl_description = "Confirm the previewed progress value and apply it"
    if TYPE_CHECKING:
        pose_index: int
    else:
        __annotations__ = {"pose_index": IntProperty()}

    def execute(self, context):
        armature = context.scene.sim_pt_selected_armature if context.scene.sim_pt_selected_armature else context.active_object
        if not armature or self.pose_index >= len(armature.data.sim_pt_poses):
            self.report({'ERROR'}, "Invalid pose index or no armature selected")
            return {'CANCELLED'}
        pose = armature.data.sim_pt_poses[self.pose_index]
        core_apply.clear_pose_preview()
        pose.combined_progress = pose.preview_progress
        return {'FINISHED'}


class PT_OT_CancelProgressPreview(bpy.types.Operator):
    bl_idname = "pt.cancel_progress_preview"
    bl_label = "Cancel Preview"
    bl_description = "Cancel the preview and restore the previous pose state"
    if TYPE_CHECKING:
        pose_index: int
    else:
        __annotations__ = {"pose_index": IntProperty()}

    def execute(self, context):
        armature = context.scene.sim_pt_selected_armature if context.scene.sim_pt_selected_armature else context.active_object
        if not armature or self.pose_index >= len(armature.data.sim_pt_poses):
            self.report({'ERROR'}, "Invalid pose index or no armature selected")
            return {'CANCELLED'}
        pose = armature.data.sim_pt_poses[self.pose_index]
        core_apply.cancel_pose_preview(pose, context)
        core_apply._PREVIEW_SUSPEND = True
        try:
            pose.preview_progress = pose.combined_progress
        finally:
            core_apply._PREVIEW_SUSPEND = False
        return {'FINISHED'}
