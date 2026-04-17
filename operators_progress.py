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
    bl_description = "Toggle Absolute (A) vs Relative/Additive (+) pose application mode"
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
        core_apply.cancel_pose_preview(pose, context)
        pose.combined_progress = pose.preview_progress / 100.0
        core_apply._PREVIEW_SUSPEND = True
        try:
            pose.preview_progress = 0.0
        finally:
            core_apply._PREVIEW_SUSPEND = False
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
            pose.preview_progress = 0.0
        finally:
            core_apply._PREVIEW_SUSPEND = False
        return {'FINISHED'}


class PT_OT_AdjustPoseProgress(bpy.types.Operator):
    bl_idname = "pt.adjust_pose_progress"
    bl_label = "Adjust Pose"
    bl_description = "Adjust the pose by dragging: LMB confirm, RMB or Esc cancel (supports negative values; Relative/+ can exceed 100%)"
    bl_options = {'REGISTER', 'BLOCKING'}
    if TYPE_CHECKING:
        pose_index: int
    else:
        __annotations__ = {"pose_index": IntProperty()}

    _start_mouse_x = 0
    _value = 0.0
    _pose_ptr = None
    _area = None

    @staticmethod
    def _find_pose_by_pointer(armature, pose_ptr):
        if not armature or not getattr(armature, "data", None) or not hasattr(armature.data, "sim_pt_poses"):
            return None
        for pose in armature.data.sim_pt_poses:
            try:
                if pose.as_pointer() == pose_ptr:
                    return pose
            except Exception:
                continue
        return None

    def _set_status(self, context, text):
        if self._area:
            self._area.header_text_set(text)
        workspace = getattr(context, "workspace", None)
        if workspace and hasattr(workspace, "status_text_set"):
            workspace.status_text_set(text)

    def _clear_status(self, context):
        if self._area:
            self._area.header_text_set(None)
        workspace = getattr(context, "workspace", None)
        if workspace and hasattr(workspace, "status_text_set"):
            workspace.status_text_set(None)

    def invoke(self, context, event):
        armature = context.scene.sim_pt_selected_armature if context.scene.sim_pt_selected_armature else context.active_object
        if not armature or armature.type != 'ARMATURE' or self.pose_index >= len(armature.data.sim_pt_poses):
            self.report({'ERROR'}, "Invalid pose index or no armature selected")
            return {'CANCELLED'}
        self._start_mouse_x = event.mouse_x
        self._value = 0.0
        self._area = context.area
        pose = armature.data.sim_pt_poses[self.pose_index]
        core_apply.preview_pose_progress(pose, context, 0.0)
        try:
            self._pose_ptr = pose.as_pointer()
        except Exception:
            self._pose_ptr = None
        self._set_status(context, "Adjust Pose: drag to set -100..+100 (A) or beyond (+). LMB confirm, RMB/Esc cancel.")
        if self._area:
            self._area.tag_redraw()
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type in {'RIGHTMOUSE', 'ESC'}:
            self._cancel(context)
            return {'CANCELLED'}
        if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            self._confirm(context)
            return {'FINISHED'}
        if event.type == 'MOUSEMOVE':
            armature = context.scene.sim_pt_selected_armature if context.scene.sim_pt_selected_armature else context.active_object
            if not armature or armature.type != 'ARMATURE':
                self._cancel(context)
                return {'CANCELLED'}
            pose = self._find_pose_by_pointer(armature, self._pose_ptr) if self._pose_ptr else None
            if not pose:
                self._cancel(context)
                return {'CANCELLED'}
            dx = event.mouse_x - self._start_mouse_x
            sensitivity = 1.0
            if event.shift:
                sensitivity = 0.2
            if event.ctrl:
                sensitivity = 5.0
            value = dx * 0.5 * sensitivity
            if not pose.is_relative:
                value = max(-100.0, min(100.0, value))
            self._value = value
            core_apply.preview_pose_progress(pose, context, self._value)
            self._set_status(context, f"Adjust Pose: {self._value:.1f}% (LMB confirm, RMB/Esc cancel)")
            if self._area:
                self._area.tag_redraw()
            return {'RUNNING_MODAL'}
        return {'RUNNING_MODAL'}

    def _confirm(self, context):
        armature = context.scene.sim_pt_selected_armature if context.scene.sim_pt_selected_armature else context.active_object
        if not armature or armature.type != 'ARMATURE':
            self._clear_status(context)
            return
        pose = self._find_pose_by_pointer(armature, self._pose_ptr) if self._pose_ptr else None
        if not pose:
            core_apply.clear_pose_preview()
            self._clear_status(context)
            if self._area:
                self._area.tag_redraw()
            return
        core_apply.cancel_pose_preview(pose, context)
        core_apply.update_pose(pose, context, progress_override=self._value / 100.0, insert_keyframes=True, push_undo=True)
        self._clear_status(context)
        if self._area:
            self._area.tag_redraw()

    def _cancel(self, context):
        armature = context.scene.sim_pt_selected_armature if context.scene.sim_pt_selected_armature else context.active_object
        if armature and armature.type == 'ARMATURE':
            pose = self._find_pose_by_pointer(armature, self._pose_ptr) if self._pose_ptr else None
            if pose:
                core_apply.cancel_pose_preview(pose, context)
            else:
                core_apply.clear_pose_preview()
        self._clear_status(context)
        if self._area:
            self._area.tag_redraw()
