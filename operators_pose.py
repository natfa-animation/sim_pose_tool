from typing import TYPE_CHECKING

import bpy  # type: ignore[import-not-found]
from bpy.props import IntProperty, StringProperty  # type: ignore[import-not-found]

from .core_apply import get_mirror_bone_name


def _pose_bone_is_selected(pose_bone):
    try:
        return pose_bone.select
    except AttributeError:
        return pose_bone.bone.select


def _pose_bone_set_selected(pose_bone, value):
    try:
        pose_bone.select = value
    except AttributeError:
        pose_bone.bone.select = value


class PT_OT_UpdatePose(bpy.types.Operator):
    bl_idname = "pt.update_pose"
    bl_label = "Update Pose"
    bl_description = "Update pose with current bone transforms and manage participating bones"
    if TYPE_CHECKING:
        pose_index: int
    else:
        __annotations__ = {"pose_index": IntProperty()}

    def execute(self, context):
        armature = context.scene.sim_pt_selected_armature if context.scene.sim_pt_selected_armature else context.active_object
        if not armature or armature.type != 'ARMATURE' or self.pose_index >= len(armature.data.sim_pt_poses):
            self.report({'ERROR'}, "Invalid pose index or no armature selected")
            return {'CANCELLED'}
        
        current_mode = armature.mode
        if armature.mode != 'POSE':
            try:
                bpy.ops.object.mode_set(mode='POSE')
            except:
                self.report({'ERROR'}, "Failed to switch to Pose mode")
                return {'CANCELLED'}
        
        pose = armature.data.sim_pt_poses[self.pose_index]
        selected_bones = [pose_bone for pose_bone in armature.pose.bones if _pose_bone_is_selected(pose_bone)]
        if not selected_bones:
            self.report({'ERROR'}, "Select at least one bone to update the pose")
            if current_mode != armature.mode:
                try:
                    bpy.ops.object.mode_set(mode=current_mode)
                except:
                    pass
            return {'CANCELLED'}
        
        # Create a set of selected bone names
        selected_bone_names = {pose_bone.name for pose_bone in selected_bones}
        
        # Clear all existing bones in the pose and rebuild based on current selection
        removed_bones = [bd.bone_name for bd in pose.bone_poses if bd.bone_name not in selected_bone_names]
        pose.bone_poses.clear()
        
        # Add or update selected bones
        for pose_bone in selected_bones:
            bone_data = pose.bone_poses.add()
            bone_data.bone_name = pose_bone.name
            bone_data.rotation_mode = pose_bone.rotation_mode
            if pose_bone.rotation_mode in {'QUATERNION', 'AXIS_ANGLE'}:
                bone_data.target_quat_w = pose_bone.rotation_quaternion.w
                bone_data.target_quat_x = pose_bone.rotation_quaternion.x
                bone_data.target_quat_y = pose_bone.rotation_quaternion.y
                bone_data.target_quat_z = pose_bone.rotation_quaternion.z
                bone_data.use_quaternion = True
            else:
                bone_data.target_rotation_x = pose_bone.rotation_euler.x
                bone_data.target_rotation_y = pose_bone.rotation_euler.y
                bone_data.target_rotation_z = pose_bone.rotation_euler.z
                bone_data.use_quaternion = False
            bone_data.target_location_x = pose_bone.location.x
            bone_data.target_location_y = pose_bone.location.y
            bone_data.target_location_z = pose_bone.location.z
            bone_data.target_scale_x = pose_bone.scale.x
            bone_data.target_scale_y = pose_bone.scale.y
            bone_data.target_scale_z = pose_bone.scale.z
        
        if current_mode != armature.mode:
            try:
                bpy.ops.object.mode_set(mode=current_mode)
            except:
                pass
        # Report removed bones if any
        if removed_bones:
            self.report({'INFO'}, f"Pose '{pose.name}' updated. Removed bones: {', '.join(removed_bones)}. Updated with {len(selected_bones)} bone(s).")
        else:
            self.report({'INFO'}, f"Pose '{pose.name}' updated with {len(selected_bones)} bone(s).")
        bpy.ops.ed.undo_push(message=f"Update pose '{pose.name}'")
        return {'FINISHED'}


class PT_OT_SelectPoseBones(bpy.types.Operator):
    bl_idname = "pt.select_pose_bones"
    bl_label = "Select Pose Bones"
    bl_description = "Select bones defined in the pose"
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
        if not pose.bone_poses:
            self.report({'WARNING'}, f"No bones defined in pose '{pose.name}'")
            return {'CANCELLED'}
        
        current_mode = armature.mode
        if armature.mode != 'POSE':
            try:
                bpy.ops.object.mode_set(mode='POSE')
            except:
                self.report({'ERROR'}, "Failed to switch to Pose mode")
                return {'CANCELLED'}
        
        for bone in armature.pose.bones:
            _pose_bone_set_selected(bone, False)
        mirror_pose = pose.is_mirrored
        debug_info = []
        for bone_data in pose.bone_poses:
            if bone_data.bone_name not in armature.pose.bones:
                debug_info.append(f"Skipping {bone_data.bone_name}: not in armature")
                continue
            if mirror_pose:
                mirror_name = get_mirror_bone_name(bone_data.bone_name)
                if mirror_name and mirror_name in armature.pose.bones:
                    _pose_bone_set_selected(armature.pose.bones[mirror_name], True)
                    debug_info.append(f"Selected mirrored: {bone_data.bone_name} -> {mirror_name}")
                else:
                    debug_info.append(f"No mirror for {bone_data.bone_name}: mirror_name={mirror_name}")
            else:
                _pose_bone_set_selected(armature.pose.bones[bone_data.bone_name], True)
                debug_info.append(f"Selected original: {bone_data.bone_name}")
        
        bpy.context.view_layer.update()
        if current_mode != armature.mode:
            try:
                bpy.ops.object.mode_set(mode=current_mode)
            except:
                pass
        self.report({'INFO'}, f"Selected bones from pose '{pose.name}': {'; '.join(debug_info)}")
        bpy.ops.ed.undo_push(message=f"Select bones for pose '{pose.name}'")
        return {'FINISHED'}


class PT_OT_ToggleApplyToAllBones(bpy.types.Operator):
    bl_idname = "pt.toggle_apply_to_all_bones"
    bl_label = "Toggle Apply to All Bones"
    bl_description = "Apply pose to all bones or only selected"

    def execute(self, context):
        context.scene.sim_pt_apply_to_all_bones = not context.scene.sim_pt_apply_to_all_bones
        bpy.ops.ed.undo_push(message="Toggle apply to all bones")
        return {'FINISHED'}


class PT_OT_ToggleRotation(bpy.types.Operator):
    bl_idname = "pt.toggle_rotation"
    bl_label = "Toggle Rotation"
    bl_description = "Enable/disable rotation for pose application"

    def execute(self, context):
        context.scene.sim_pt_use_rotation = not context.scene.sim_pt_use_rotation
        bpy.ops.ed.undo_push(message="Toggle rotation")
        return {'FINISHED'}


class PT_OT_ToggleLocation(bpy.types.Operator):
    bl_idname = "pt.toggle_location"
    bl_label = "Toggle Location"
    bl_description = "Enable/disable location for pose application"

    def execute(self, context):
        context.scene.sim_pt_use_location = not context.scene.sim_pt_use_location
        bpy.ops.ed.undo_push(message="Toggle location")
        return {'FINISHED'}


class PT_OT_ToggleScale(bpy.types.Operator):
    bl_idname = "pt.toggle_scale"
    bl_label = "Toggle Scale"
    bl_description = "Enable/disable scale for pose application"

    def execute(self, context):
        context.scene.sim_pt_use_scale = not context.scene.sim_pt_use_scale
        bpy.ops.ed.undo_push(message="Toggle scale")
        return {'FINISHED'}


class PT_OT_RecordPose(bpy.types.Operator):
    bl_idname = "pt.record_pose"
    bl_label = "Set New Pose"
    bl_description = "Record a new pose from selected bones"
    if TYPE_CHECKING:
        pose_name: str
    else:
        __annotations__ = {"pose_name": StringProperty(name="Pose Name", default="New Pose")}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        armature = context.scene.sim_pt_selected_armature if context.scene.sim_pt_selected_armature else context.active_object
        if not armature or armature.type != 'ARMATURE':
            self.report({'ERROR'}, "Select an armature")
            return {'CANCELLED'}
        
        current_mode = armature.mode
        if armature.mode != 'POSE':
            try:
                bpy.ops.object.mode_set(mode='POSE')
            except:
                self.report({'ERROR'}, "Failed to switch to Pose mode")
                return {'CANCELLED'}
        
        selected_bones = [pose_bone for pose_bone in armature.pose.bones if _pose_bone_is_selected(pose_bone)]
        if not selected_bones:
            self.report({'ERROR'}, "Select at least one bone")
            if current_mode != armature.mode:
                try:
                    bpy.ops.object.mode_set(mode=current_mode)
                except:
                    pass
            return {'CANCELLED'}
        
        new_pose = armature.data.sim_pt_poses.add()
        new_pose.name = self.pose_name
        for pose_bone in selected_bones:
            bone_data = new_pose.bone_poses.add()
            bone_data.bone_name = pose_bone.name
            bone_data.rotation_mode = pose_bone.rotation_mode
            if pose_bone.rotation_mode in {'QUATERNION', 'AXIS_ANGLE'}:
                bone_data.target_quat_w = pose_bone.rotation_quaternion.w
                bone_data.target_quat_x = pose_bone.rotation_quaternion.x
                bone_data.target_quat_y = pose_bone.rotation_quaternion.y
                bone_data.target_quat_z = pose_bone.rotation_quaternion.z
                bone_data.use_quaternion = True
            else:
                bone_data.target_rotation_x = pose_bone.rotation_euler.x
                bone_data.target_rotation_y = pose_bone.rotation_euler.y
                bone_data.target_rotation_z = pose_bone.rotation_euler.z
                bone_data.use_quaternion = False
            bone_data.target_location_x = pose_bone.location.x
            bone_data.target_location_y = pose_bone.location.y
            bone_data.target_location_z = pose_bone.location.z
            bone_data.target_scale_x = pose_bone.scale.x
            bone_data.target_scale_y = pose_bone.scale.y
            bone_data.target_scale_z = pose_bone.scale.z
            if bone_data.use_quaternion:
                pose_bone.keyframe_insert(data_path="rotation_quaternion", frame=context.scene.frame_current)
            else:
                pose_bone.keyframe_insert(data_path="rotation_euler", frame=context.scene.frame_current)
            pose_bone.keyframe_insert(data_path="location", frame=context.scene.frame_current)
            pose_bone.keyframe_insert(data_path="scale", frame=context.scene.frame_current)
        
        if current_mode != armature.mode:
            try:
                bpy.ops.object.mode_set(mode=current_mode)
            except:
                pass
        self.report({'INFO'}, f"Pose '{self.pose_name}' recorded successfully")
        bpy.ops.ed.undo_push(message=f"Record pose '{self.pose_name}'")
        return {'FINISHED'}


class PT_OT_DeletePoses(bpy.types.Operator):
    bl_idname = "pt.delete_poses"
    bl_label = "Delete All Poses"
    bl_description = "Delete all poses"
    
    def execute(self, context):
        armature = context.scene.sim_pt_selected_armature if context.scene.sim_pt_selected_armature else context.active_object
        if armature and armature.type == 'ARMATURE' and armature.data.sim_pt_poses:
            armature.data.sim_pt_poses.clear()
            self.report({'INFO'}, "All poses deleted")
            bpy.ops.ed.undo_push(message="Delete all poses")
        else:
            self.report({'WARNING'}, "No poses to delete or no armature selected")
        return {'FINISHED'}


class PT_OT_DeletePose(bpy.types.Operator):
    bl_idname = "pt.delete_pose"
    bl_label = "Delete Pose"
    bl_description = "Delete the selected pose"
    if TYPE_CHECKING:
        pose_index: int
    else:
        __annotations__ = {"pose_index": IntProperty()}

    def execute(self, context):
        armature = context.scene.sim_pt_selected_armature if context.scene.sim_pt_selected_armature else context.active_object
        if not armature or armature.type != 'ARMATURE' or self.pose_index >= len(armature.data.sim_pt_poses):
            self.report({'ERROR'}, "Invalid pose index or no armature selected")
            return {'CANCELLED'}
        pose_name = armature.data.sim_pt_poses[self.pose_index].name
        armature.data.sim_pt_poses.remove(self.pose_index)
        self.report({'INFO'}, f"Pose '{pose_name}' deleted")
        bpy.ops.ed.undo_push(message=f"Delete pose '{pose_name}'")
        return {'FINISHED'}


class PT_OT_DeletePoseGroup(bpy.types.Operator):
    bl_idname = "pt.delete_pose_group"
    bl_label = "Delete Pose Group"
    bl_description = "Delete the selected pose group"
    if TYPE_CHECKING:
        group_index: int
    else:
        __annotations__ = {"group_index": IntProperty()}

    def execute(self, context):
        armature = context.scene.sim_pt_selected_armature if context.scene.sim_pt_selected_armature else context.active_object
        if not armature or armature.type != 'ARMATURE' or self.group_index >= len(armature.data.sim_pt_pose_groups):
            self.report({'ERROR'}, "Invalid group index or no armature selected")
            return {'CANCELLED'}
        group_name = armature.data.sim_pt_pose_groups[self.group_index].name
        for pose in armature.data.sim_pt_poses:
            if pose.group_name == group_name:
                pose.group_name = ""
        for group in armature.data.sim_pt_pose_groups:
            if group.parent_group == group_name:
                group.parent_group = ""
        armature.data.sim_pt_pose_groups.remove(self.group_index)
        self.report({'INFO'}, f"Group '{group_name}' deleted")
        bpy.ops.ed.undo_push(message=f"Delete group '{group_name}'")
        return {'FINISHED'}


class PT_OT_CreatePoseGroup(bpy.types.Operator):
    bl_idname = "pt.create_pose_group"
    bl_label = "Create Pose Group"
    bl_description = "Create a new pose group"
    if TYPE_CHECKING:
        group_name: str
        parent_group: str
    else:
        __annotations__ = {
            "group_name": StringProperty(name="Group Name", default="New Group"),
            "parent_group": StringProperty(name="Parent Group", default=""),
        }

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "group_name")
        armature = context.scene.sim_pt_selected_armature if context.scene.sim_pt_selected_armature else context.active_object
        if armature and armature.type == 'ARMATURE':
            layout.prop_search(self, "parent_group", armature.data, "sim_pt_pose_groups", text="Parent Group")

    def execute(self, context):
        armature = context.scene.sim_pt_selected_armature if context.scene.sim_pt_selected_armature else context.active_object
        if not armature or armature.type != 'ARMATURE':
            self.report({'ERROR'}, "Select an armature")
            return {'CANCELLED'}
        new_group = armature.data.sim_pt_pose_groups.add()
        new_group.name = self.group_name
        new_group.parent_group = self.parent_group
        self.report({'INFO'}, f"Group '{self.group_name}' created" + (f" under '{self.parent_group}'" if self.parent_group else ""))
        bpy.ops.ed.undo_push(message=f"Create group '{self.group_name}'")
        return {'FINISHED'}


class PT_OT_DuplicatePose(bpy.types.Operator):
    bl_idname = "pt.duplicate_pose"
    bl_label = "Duplicate Pose"
    bl_description = "Duplicate the selected pose"
    if TYPE_CHECKING:
        pose_index: int
    else:
        __annotations__ = {"pose_index": IntProperty()}

    def execute(self, context):
        armature = context.scene.sim_pt_selected_armature if context.scene.sim_pt_selected_armature else context.active_object
        if not armature or armature.type != 'ARMATURE' or self.pose_index >= len(armature.data.sim_pt_poses):
            self.report({'ERROR'}, "Invalid pose index or no armature selected")
            return {'CANCELLED'}
        original_pose = armature.data.sim_pt_poses[self.pose_index]
        new_pose = armature.data.sim_pt_poses.add()
        new_pose.name = original_pose.name + "_Copy"
        new_pose.group_name = original_pose.group_name
        new_pose.is_relative = original_pose.is_relative
        new_pose.is_mirrored = original_pose.is_mirrored
        for bone_data in original_pose.bone_poses:
            new_bone_data = new_pose.bone_poses.add()
            for attr in dir(bone_data):
                if not attr.startswith('_') and hasattr(new_bone_data, attr):
                    setattr(new_bone_data, attr, getattr(bone_data, attr))
        self.report({'INFO'}, f"Pose '{original_pose.name}' duplicated as '{new_pose.name}'")
        bpy.ops.ed.undo_push(message=f"Duplicate pose '{original_pose.name}'")
        return {'FINISHED'}

