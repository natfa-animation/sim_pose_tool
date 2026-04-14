bl_info = {
    "name": "SIM posetool",
    "version": (1, 27),
    "blender": (4, 3, 2),
    "category": "SIM anima",
    "description": "A tool for managing, interpolating, and loading pose presets in Blender",
}

from typing import TYPE_CHECKING, Any

import bpy  # type: ignore[import-not-found]
from bpy.props import (  # type: ignore[import-not-found]
    BoolProperty,
    CollectionProperty,
    EnumProperty,
    FloatProperty,
    IntProperty,
    PointerProperty,
    StringProperty,
)
from mathutils import Euler, Quaternion, Vector  # type: ignore[import-not-found]
import json
from bpy_extras.io_utils import ExportHelper, ImportHelper  # type: ignore[import-not-found]
import os
from pathlib import Path

# Class for bone pose data
class PTBonePoseData(bpy.types.PropertyGroup):
    if TYPE_CHECKING:
        bone_name: str
        target_rotation_x: float
        target_rotation_y: float
        target_rotation_z: float
        target_quat_w: float
        target_quat_x: float
        target_quat_y: float
        target_quat_z: float
        rotation_mode: str
        target_location_x: float
        target_location_y: float
        target_location_z: float
        target_scale_x: float
        target_scale_y: float
        target_scale_z: float
        use_quaternion: bool
    else:
        __annotations__ = {
            "bone_name": StringProperty(name="Bone Name", default=""),
            "target_rotation_x": FloatProperty(name="Target Rotation X", default=0.0),
            "target_rotation_y": FloatProperty(name="Target Rotation Y", default=0.0),
            "target_rotation_z": FloatProperty(name="Target Rotation Z", default=0.0),
            "target_quat_w": FloatProperty(name="Target Quaternion W", default=1.0),
            "target_quat_x": FloatProperty(name="Target Quaternion X", default=0.0),
            "target_quat_y": FloatProperty(name="Target Quaternion Y", default=0.0),
            "target_quat_z": FloatProperty(name="Target Quaternion Z", default=0.0),
            "rotation_mode": StringProperty(name="Rotation Mode", default="XYZ"),
            "target_location_x": FloatProperty(name="Target Location X", default=0.0),
            "target_location_y": FloatProperty(name="Target Location Y", default=0.0),
            "target_location_z": FloatProperty(name="Target Location Z", default=0.0),
            "target_scale_x": FloatProperty(name="Target Scale X", default=1.0),
            "target_scale_y": FloatProperty(name="Target Scale Y", default=1.0),
            "target_scale_z": FloatProperty(name="Target Scale Z", default=1.0),
            "use_quaternion": BoolProperty(name="Use Quaternion", default=False),
        }

# Class for pose group
class PTPoseGroup(bpy.types.PropertyGroup):
    if TYPE_CHECKING:
        name: str
        is_expanded: bool
        parent_group: str
    else:
        __annotations__ = {
            "name": StringProperty(name="Group Name", default="Group"),
            "is_expanded": BoolProperty(name="Expanded", default=True),
            "parent_group": StringProperty(name="Parent Group", default=""),
        }

# Class for pose
class PTPoseItem(bpy.types.PropertyGroup):
    if TYPE_CHECKING:
        name: str
        bone_poses: Any
        combined_progress: float
        is_active: bool
        is_relative: bool
        is_mirrored: bool
        group_name: str
    else:
        __annotations__ = {
            "name": StringProperty(name="Pose Name", default="Pose"),
            "bone_poses": CollectionProperty(type=PTBonePoseData),
            "combined_progress": FloatProperty(
                name="Progress",
                description="Percentage of the pose to apply",
                default=0.1,
                min=-1.0,
                max=1.0,
                update=lambda self, context: update_pose(self, context),
            ),
            "is_active": BoolProperty(default=False),
            "is_relative": BoolProperty(default=False),
            "is_mirrored": BoolProperty(default=False),
            "group_name": StringProperty(name="Group", default=""),
        }

# Helper function to get mirror bone name
from sim_posetool_utils import get_mirror_bone_name

# Function for pose interpolation
def update_pose(pose, context):
    if not context or not context.scene:
        return
    armature = context.scene.sim_pt_selected_armature if context.scene.sim_pt_selected_armature else context.active_object
    if not armature or armature.type != 'ARMATURE':
        return
    
    current_mode = armature.mode
    original_active = context.active_object
    original_selected = context.selected_objects[:]
    
    if armature.mode != 'POSE':
        try:
            bpy.ops.object.mode_set(mode='POSE')
        except:
            return
    
    mirror_pose = pose.is_mirrored
    apply_to_all = context.scene.sim_pt_apply_to_all_bones
    selected_bones = {pose_bone.name for pose_bone in armature.pose.bones if pose_bone.bone.select}
    
    target_bones = []
    debug_info = []
    for bone_data in pose.bone_poses:
        if bone_data.bone_name not in armature.pose.bones:
            debug_info.append(f"Skipping {bone_data.bone_name}: not in armature")
            continue
        if mirror_pose:
            mirror_name = get_mirror_bone_name(bone_data.bone_name)
            if mirror_name and mirror_name in armature.pose.bones:
                if apply_to_all or mirror_name in selected_bones:
                    target_bones.append((armature.pose.bones[mirror_name], bone_data.bone_name))
                    debug_info.append(f"Mirrored: {bone_data.bone_name} -> {mirror_name}")
                else:
                    debug_info.append(f"Skipping mirrored {mirror_name}: not selected and apply_to_all is False")
            else:
                debug_info.append(f"No mirror for {bone_data.bone_name}: mirror_name={mirror_name}")
        else:
            if apply_to_all or bone_data.bone_name in selected_bones:
                target_bones.append((armature.pose.bones[bone_data.bone_name], bone_data.bone_name))
                debug_info.append(f"Original: {bone_data.bone_name}")
            else:
                debug_info.append(f"Skipping {bone_data.bone_name}: not selected and apply_to_all is False")
    
    if not target_bones:
        if debug_info:
            print(f"No target bones for pose '{pose.name}': {'; '.join(debug_info)}")
        if current_mode != armature.mode:
            try:
                bpy.ops.object.mode_set(mode=current_mode)
            except:
                pass
        if context.active_object != original_active:
            context.view_layer.objects.active = original_active
        context.view_layer.update()
        return
    
    print(f"Applying pose '{pose.name}' to bones: {'; '.join(debug_info)}")
    
    t = pose.combined_progress
    use_rotation = context.scene.sim_pt_use_rotation
    use_location = context.scene.sim_pt_use_location
    use_scale = context.scene.sim_pt_use_scale
    current_frame = context.scene.frame_current
    
    for bone_entry in target_bones:
        pose_bone, original_bone_name = bone_entry
        bone_data = next((bd for bd in pose.bone_poses if bd.bone_name == original_bone_name), None)
        is_mirror = mirror_pose and original_bone_name != pose_bone.name
        
        if not bone_data:
            continue
        
        if pose.is_relative:
            if use_rotation:
                if bone_data.use_quaternion:
                    current_quat = pose_bone.rotation_quaternion.copy()
                    relative_quat = Quaternion((bone_data.target_quat_w,
                                                bone_data.target_quat_x,
                                                bone_data.target_quat_y,
                                                bone_data.target_quat_z))
                    if is_mirror:
                        relative_quat = Quaternion((relative_quat.w, relative_quat.x, -relative_quat.y, -relative_quat.z))
                    identity_quat = Quaternion((1.0, 0.0, 0.0, 0.0))
                    delta_quat = identity_quat.slerp(relative_quat if t >= 0 else relative_quat.conjugated(), abs(t))
                    pose_bone.rotation_quaternion = current_quat @ delta_quat
                    pose_bone.keyframe_insert(data_path="rotation_quaternion", frame=current_frame)
                else:
                    current_euler = pose_bone.rotation_euler.copy()
                    relative_euler = Euler((bone_data.target_rotation_x,
                                            bone_data.target_rotation_y,
                                            bone_data.target_rotation_z), bone_data.rotation_mode)
                    if is_mirror:
                        relative_euler = Euler((relative_euler.x, -relative_euler.y, -relative_euler.z), bone_data.rotation_mode)
                    delta_euler = Euler((relative_euler.x * t,
                                         relative_euler.y * t,
                                         relative_euler.z * t), bone_data.rotation_mode)
                    pose_bone.rotation_euler = Euler((current_euler.x + delta_euler.x,
                                                      current_euler.y + delta_euler.y,
                                                      current_euler.z + delta_euler.z), bone_data.rotation_mode)
                    pose_bone.keyframe_insert(data_path="rotation_euler", frame=current_frame)
            if use_location:
                current_location = pose_bone.location.copy()
                relative_location = Vector((bone_data.target_location_x,
                                            bone_data.target_location_y,
                                            bone_data.target_location_z))
                if is_mirror:
                    relative_location = Vector((-relative_location.x, relative_location.y, relative_location.z))
                delta_location = relative_location * t
                pose_bone.location = Vector((current_location.x + delta_location.x,
                                             current_location.y + delta_location.y,
                                             current_location.z + delta_location.z))
                pose_bone.keyframe_insert(data_path="location", frame=current_frame)
            if use_scale:
                current_scale = pose_bone.scale.copy()
                relative_scale = Vector((bone_data.target_scale_x,
                                         bone_data.target_scale_y,
                                         bone_data.target_scale_z))
                if relative_scale == Vector((1.0, 1.0, 1.0)):
                    continue
                delta_scale = Vector((relative_scale.x - 1.0,
                                      relative_scale.y - 1.0,
                                      relative_scale.z - 1.0)) * t
                pose_bone.scale = Vector((current_scale.x + delta_scale.x,
                                          current_scale.y + delta_scale.y,
                                          current_scale.z + delta_scale.z))
                pose_bone.keyframe_insert(data_path="scale", frame=current_frame)
        else:
            if use_rotation:
                if bone_data.use_quaternion:
                    current_quat = pose_bone.rotation_quaternion.copy()
                    target_quat = Quaternion((bone_data.target_quat_w,
                                              bone_data.target_quat_x,
                                              bone_data.target_quat_y,
                                              bone_data.target_quat_z))
                    if is_mirror:
                        target_quat = Quaternion((target_quat.w, target_quat.x, -target_quat.y, -target_quat.z))
                    if t < 0:
                        target_quat = target_quat.conjugated()
                        t_local = -t
                    else:
                        t_local = t
                    pose_bone.rotation_quaternion = current_quat.slerp(target_quat, abs(t_local))
                    pose_bone.keyframe_insert(data_path="rotation_quaternion", frame=current_frame)
                else:
                    current_euler = pose_bone.rotation_euler.copy()
                    target_euler = Euler((bone_data.target_rotation_x,
                                          bone_data.target_rotation_y,
                                          bone_data.target_rotation_z), bone_data.rotation_mode)
                    if is_mirror:
                        target_euler = Euler((target_euler.x, -target_euler.y, -target_euler.z), bone_data.rotation_mode)
                    if t < 0:
                        target_euler = Euler((-target_euler.x,
                                              -target_euler.y,
                                              -target_euler.z), bone_data.rotation_mode)
                        t_local = -t
                    else:
                        t_local = t
                    interpolated_euler = current_euler.to_quaternion().slerp(target_euler.to_quaternion(), abs(t_local)).to_euler(bone_data.rotation_mode)
                    pose_bone.rotation_euler = interpolated_euler
                    pose_bone.keyframe_insert(data_path="rotation_euler", frame=current_frame)
            if use_location:
                current_location = pose_bone.location.copy()
                target_location = Vector((bone_data.target_location_x,
                                          bone_data.target_location_y,
                                          bone_data.target_location_z))
                if is_mirror:
                    target_location = Vector((-target_location.x, target_location.y, target_location.z))
                if t < 0:
                    target_location = -target_location
                    t_local = -t
                else:
                    t_local = t
                pose_bone.location = current_location.lerp(target_location, abs(t_local))
                pose_bone.keyframe_insert(data_path="location", frame=current_frame)
            if use_scale:
                current_scale = pose_bone.scale.copy()
                target_scale = Vector((bone_data.target_scale_x,
                                       bone_data.target_scale_y,
                                       bone_data.target_scale_z))
                if target_scale == Vector((1.0, 1.0, 1.0)):
                    continue
                safe_target_scale = Vector((max(target_scale.x, 0.0001),
                                            max(target_scale.y, 0.0001),
                                            max(target_scale.z, 0.0001)))
                if t < 0:
                    adjusted_scale = Vector((1.0 / safe_target_scale.x,
                                             1.0 / safe_target_scale.y,
                                             1.0 / safe_target_scale.z))
                    t_local = -t
                else:
                    adjusted_scale = safe_target_scale
                    t_local = t
                pose_bone.scale = current_scale.lerp(adjusted_scale, abs(t_local))
                pose_bone.keyframe_insert(data_path="scale", frame=current_frame)
    
    armature.update_tag()
    bpy.context.view_layer.update()
    
    bpy.ops.ed.undo_push(message=f"Pose '{pose.name}' progress set to {t}")
    
    if current_mode != armature.mode:
        try:
            bpy.ops.object.mode_set(mode=current_mode)
        except:
            pass
    if context.active_object != original_active:
        context.view_layer.objects.active = original_active
    for obj in bpy.context.scene.objects:
        obj.select_set(obj in original_selected)

# Operator to toggle mirror for a specific pose
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

# Operators for setting progress values
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

# Operator to toggle pose mode (Relative/Absolute)
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

# Operator to reset progress for a specific pose
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

# Modified Operator to update a specific pose with current bone transforms and manage participating bones
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
        selected_bones = [pose_bone for pose_bone in armature.pose.bones if pose_bone.bone.select]
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

# Operator to select bones in a pose
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
            bone.bone.select = False
        mirror_pose = pose.is_mirrored
        debug_info = []
        for bone_data in pose.bone_poses:
            if bone_data.bone_name not in armature.pose.bones:
                debug_info.append(f"Skipping {bone_data.bone_name}: not in armature")
                continue
            if mirror_pose:
                mirror_name = get_mirror_bone_name(bone_data.bone_name)
                if mirror_name and mirror_name in armature.pose.bones:
                    armature.pose.bones[mirror_name].bone.select = True
                    debug_info.append(f"Selected mirrored: {bone_data.bone_name} -> {mirror_name}")
                else:
                    debug_info.append(f"No mirror for {bone_data.bone_name}: mirror_name={mirror_name}")
            else:
                armature.pose.bones[bone_data.bone_name].bone.select = True
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

# Operator to toggle apply to all bones
class PT_OT_ToggleApplyToAllBones(bpy.types.Operator):
    bl_idname = "pt.toggle_apply_to_all_bones"
    bl_label = "Toggle Apply to All Bones"
    bl_description = "Apply pose to all bones or only selected"

    def execute(self, context):
        context.scene.sim_pt_apply_to_all_bones = not context.scene.sim_pt_apply_to_all_bones
        bpy.ops.ed.undo_push(message="Toggle apply to all bones")
        return {'FINISHED'}

# Operators to toggle global settings
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

# Operator to record a new pose
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
        
        selected_bones = [pose_bone for pose_bone in armature.pose.bones if pose_bone.bone.select]
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

# Operator to delete all poses
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

# Operator to delete a specific pose
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

# Operator to delete a specific group
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

# Operator to export poses and groups
class PT_OT_ExportPoses(bpy.types.Operator, ExportHelper):
    bl_idname = "pt.export_poses"
    bl_label = "Export Poses"
    bl_description = "Export poses and groups to a JSON file"
    filename_ext = ".json"
    
    def execute(self, context):
        armature = context.scene.sim_pt_selected_armature if context.scene.sim_pt_selected_armature else context.active_object
        if not armature or armature.type != 'ARMATURE':
            self.report({'ERROR'}, "Select an armature")
            return {'CANCELLED'}
        data = {"poses": [], "groups": []}
        for pose in armature.data.sim_pt_poses:
            pose_dict = {
                "name": pose.name,
                "group_name": pose.group_name,
                "is_mirrored": pose.is_mirrored,
                "bone_poses": [
                    {
                        "bone_name": bd.bone_name,
                        "target_rotation_x": bd.target_rotation_x,
                        "target_rotation_y": bd.target_rotation_y,
                        "target_rotation_z": bd.target_rotation_z,
                        "target_quat_w": bd.target_quat_w,
                        "target_quat_x": bd.target_quat_x,
                        "target_quat_y": bd.target_quat_y,
                        "target_quat_z": bd.target_quat_z,
                        "rotation_mode": bd.rotation_mode,
                        "target_location_x": bd.target_location_x,
                        "target_location_y": bd.target_location_y,
                        "target_location_z": bd.target_location_z,
                        "target_scale_x": bd.target_scale_x,
                        "target_scale_y": bd.target_scale_y,
                        "target_scale_z": bd.target_scale_z,
                        "use_quaternion": bd.use_quaternion
                    } for bd in pose.bone_poses
                ]
            }
            data["poses"].append(pose_dict)
        for group in armature.data.sim_pt_pose_groups:
            group_dict = {
                "name": group.name,
                "parent_group": group.parent_group,
                "is_expanded": group.is_expanded
            }
            data["groups"].append(group_dict)
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
            self.report({'INFO'}, f"Poses and groups exported to {self.filepath}")
            bpy.ops.ed.undo_push(message="Export poses")
        except Exception as e:
            self.report({'ERROR'}, f"Failed to export poses: {str(e)}")
            return {'CANCELLED'}
        return {'FINISHED'}

# Operator to import poses and groups (replaces existing)
class PT_OT_ImportPoses(bpy.types.Operator, ImportHelper):
    bl_idname = "pt.import_poses"
    bl_label = "Import Poses"
    bl_description = "Import poses and groups, replacing existing"
    filename_ext = ".json"
    
    def execute(self, context):
        armature = context.scene.sim_pt_selected_armature if context.scene.sim_pt_selected_armature else context.active_object
        if not armature or armature.type != 'ARMATURE':
            self.report({'ERROR'}, "Select an armature")
            return {'CANCELLED'}
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            self.report({'ERROR'}, f"Failed to load JSON file: {str(e)}")
            return {'CANCELLED'}
        
        armature.data.sim_pt_poses.clear()
        armature.data.sim_pt_pose_groups.clear()
        for group_data in data.get("groups", []):
            new_group = armature.data.sim_pt_pose_groups.add()
            new_group.name = group_data.get("name", "Group")
            new_group.parent_group = group_data.get("parent_group", "")
            new_group.is_expanded = group_data.get("is_expanded", True)
        for pose_data in data.get("poses", []):
            new_pose = armature.data.sim_pt_poses.add()
            new_pose.name = pose_data.get("name", "Pose")
            new_pose.group_name = pose_data.get("group_name", "")
            new_pose.is_mirrored = pose_data.get("is_mirrored", False)
            for bd_data in pose_data.get("bone_poses", []):
                bone_data = new_pose.bone_poses.add()
                for key, value in bd_data.items():
                    if hasattr(bone_data, key):
                        setattr(bone_data, key, value)
        self.report({'INFO'}, f"Poses and groups imported from {self.filepath}")
        bpy.ops.ed.undo_push(message="Import poses")
        return {'FINISHED'}

# Operator to merge poses and groups (adds to existing)
class PT_OT_MergePoses(bpy.types.Operator, ImportHelper):
    bl_idname = "pt.merge_poses"
    bl_label = "Merge Poses"
    bl_description = "Merge poses and groups from a JSON file"
    filename_ext = ".json"
    
    def execute(self, context):
        armature = context.scene.sim_pt_selected_armature if context.scene.sim_pt_selected_armature else context.active_object
        if not armature or armature.type != 'ARMATURE':
            self.report({'ERROR'}, "Select an armature")
            return {'CANCELLED'}
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            self.report({'ERROR'}, f"Failed to load JSON file: {str(e)}")
            return {'CANCELLED'}
        
        existing_groups = {g.name for g in armature.data.sim_pt_pose_groups}
        for group_data in data.get("groups", []):
            if group_data.get("name", "Group") not in existing_groups:
                new_group = armature.data.sim_pt_pose_groups.add()
                new_group.name = group_data.get("name", "Group")
                new_group.parent_group = group_data.get("parent_group", "")
                new_group.is_expanded = group_data.get("is_expanded", True)
        for pose_data in data.get("poses", []):
            new_pose = armature.data.sim_pt_poses.add()
            new_pose.name = pose_data.get("name", "Pose")
            new_pose.group_name = pose_data.get("group_name", "")
            new_pose.is_mirrored = pose_data.get("is_mirrored", False)
            for bd_data in pose_data.get("bone_poses", []):
                bone_data = new_pose.bone_poses.add()
                for key, value in bd_data.items():
                    if hasattr(bone_data, key):
                        setattr(bone_data, key, value)
        self.report({'INFO'}, f"Poses and groups merged from {self.filepath}")
        bpy.ops.ed.undo_push(message="Merge poses")
        return {'FINISHED'}

# Operator to create a new pose group
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

# Operator to duplicate a pose
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

# Operator to load presets from a specific folder
class PT_OT_LoadPreset(bpy.types.Operator):
    bl_idname = "pt.load_preset"
    bl_label = "Load Preset"
    bl_description = "Load a pose preset from the presets folder"
    if TYPE_CHECKING:
        preset_name: str
    else:
        __annotations__ = {"preset_name": StringProperty(name="Preset Name", default="")}

    def execute(self, context):
        armature = context.scene.sim_pt_selected_armature if context.scene.sim_pt_selected_armature else context.active_object
        if not armature or armature.type != 'ARMATURE':
            self.report({'ERROR'}, "Select an armature")
            return {'CANCELLED'}
        presets_path = context.scene.sim_pt_presets_path
        preset_filepath = os.path.join(presets_path, self.preset_name)
        if not os.path.exists(preset_filepath):
            self.report({'ERROR'}, f"Preset file '{preset_filepath}' does not exist")
            return {'CANCELLED'}
        try:
            with open(preset_filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            armature.data.sim_pt_poses.clear()
            armature.data.sim_pt_pose_groups.clear()
            for group_data in data.get("groups", []):
                new_group = armature.data.sim_pt_pose_groups.add()
                new_group.name = group_data.get("name", "Group")
                new_group.parent_group = group_data.get("parent_group", "")
                new_group.is_expanded = group_data.get("is_expanded", True)
            for pose_data in data.get("poses", []):
                new_pose = armature.data.sim_pt_poses.add()
                new_pose.name = pose_data.get("name", "Pose")
                new_pose.group_name = pose_data.get("group_name", "")
                new_pose.is_mirrored = pose_data.get("is_mirrored", False)
                for bd_data in pose_data.get("bone_poses", []):
                    bone_data = new_pose.bone_poses.add()
                    for key, value in bd_data.items():
                        if hasattr(bone_data, key):
                            setattr(bone_data, key, value)
            self.report({'INFO'}, f"Preset '{self.preset_name}' loaded successfully")
            bpy.ops.ed.undo_push(message=f"Load preset '{self.preset_name}'")
        except Exception as e:
            self.report({'ERROR'}, f"Failed to load preset: {str(e)}")
            return {'CANCELLED'}
        return {'FINISHED'}

# Panel for Pose Tool
class PTPosePanel(bpy.types.Panel):
    bl_label = "SIM posetool"
    bl_idname = "OBJECT_PT_pose_tool"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "SIM anima"

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        row = box.row()
        row.prop(context.scene, "sim_pt_selected_armature", text="Armature")
        
        armature = context.scene.sim_pt_selected_armature if context.scene.sim_pt_selected_armature else context.active_object
        if not armature or armature.type != 'ARMATURE':
            layout.label(text="Select an armature", icon='ERROR')
            return
        
        box = layout.box()
        row = box.row(align=True)
        row.operator("pt.record_pose", text="", icon='ADD')
        row.operator("pt.delete_poses", text="", icon='TRASH')
        row.operator("pt.create_pose_group", text="", icon='OUTLINER_OB_GROUP_INSTANCE')
        
        box = layout.box()
        row = box.row()
        row.prop(context.scene, "sim_pt_settings_expanded", icon='TRIA_DOWN' if context.scene.sim_pt_settings_expanded else 'TRIA_RIGHT', text="Settings", emboss=False)
        if context.scene.sim_pt_settings_expanded:
            row = box.row(align=True)
            row.operator("pt.toggle_rotation", text=f"Rot {'On' if context.scene.sim_pt_use_rotation else 'Off'}", depress=context.scene.sim_pt_use_rotation)
            row.operator("pt.toggle_location", text=f"Loc {'On' if context.scene.sim_pt_use_location else 'Off'}", depress=context.scene.sim_pt_use_location)
            row.operator("pt.toggle_scale", text=f"Scale {'On' if context.scene.sim_pt_use_scale else 'Off'}", depress=context.scene.sim_pt_use_scale)
            row.operator("pt.toggle_apply_to_all_bones", text=f"All {'On' if context.scene.sim_pt_apply_to_all_bones else 'Off'}", depress=context.scene.sim_pt_apply_to_all_bones)
            row = box.row(align=True)
            row.operator("pt.export_poses", text="", icon='EXPORT')
            row.operator("pt.import_poses", text="", icon='IMPORT')
            row.operator("pt.merge_poses", text="", icon='DUPLICATE')
        
        box = layout.box()
        row = box.row()
        row.prop(context.scene, "sim_pt_presets_expanded", icon='TRIA_DOWN' if context.scene.sim_pt_presets_expanded else 'TRIA_RIGHT', text="Presets", emboss=False)
        if context.scene.sim_pt_presets_expanded:
            row = box.row(align=True)
            row.prop(context.scene, "sim_pt_presets_path", text="Presets Folder")
            presets_path = context.scene.sim_pt_presets_path
            preset_items = []
            if os.path.exists(presets_path):
                preset_items = [(f, f, "") for f in os.listdir(presets_path) if f.endswith('.json')]
            if preset_items:
                row = box.row(align=True)
                row.prop(context.scene, "sim_pt_selected_preset", text="")
                row.operator("pt.load_preset", text="", icon='IMPORT').preset_name = context.scene.sim_pt_selected_preset
            else:
                box.label(text="No presets found in folder", icon='INFO')
        
        box = layout.box()
        if not armature.data.sim_pt_pose_groups and not armature.data.sim_pt_poses:
            box.label(text="No poses or groups", icon='INFO')
        else:
            ungrouped_poses = sorted([pose for pose in armature.data.sim_pt_poses if not pose.group_name], key=lambda p: p.name.lower())
            if ungrouped_poses:
                sub_box = box.box()
                for pose in ungrouped_poses:
                    self.draw_pose(context, sub_box, pose, armature.data.sim_pt_poses.find(pose.name))
            self.draw_group_hierarchy(box, armature)

    def draw_group_hierarchy(self, layout, armature, group_name="", indent=0):
        for i, group in enumerate(armature.data.sim_pt_pose_groups):
            if group.parent_group == group_name:
                box = layout.box()
                row = box.row(align=True)
                row.label(text="  " * indent)
                row.prop(group, "name", text="", emboss=True)
                row.prop(group, "is_expanded", icon='TRIA_DOWN' if group.is_expanded else 'TRIA_RIGHT', text="", emboss=False)
                sub_row = row.row(align=True)
                sub_row.scale_x = 0.8
                sub_row.operator("pt.delete_pose_group", text="", icon='X').group_index = i
                if group.is_expanded:
                    group_poses = sorted([pose for pose in armature.data.sim_pt_poses if pose.group_name == group.name], key=lambda p: p.name.lower())
                    for pose in group_poses:
                        self.draw_pose(bpy.context, box, pose, armature.data.sim_pt_poses.find(pose.name))
                    self.draw_group_hierarchy(box, armature, group.name, indent + 1)

    def draw_pose(self, context, layout, pose, pose_index):
        box = layout.box()
        row = box.row(align=True)
        split = row.split(factor=0.6)
        split.prop(pose, "name", text="", emboss=True)
        split.prop_search(pose, "group_name", context.active_object.data if not context.scene.sim_pt_selected_armature else context.scene.sim_pt_selected_armature.data, "sim_pt_pose_groups", text="")
        row.operator("pt.select_pose_bones", text="", icon='BONE_DATA').pose_index = pose_index
        row.operator("pt.update_pose", text="", icon='ARROW_LEFTRIGHT').pose_index = pose_index
        row.operator("pt.toggle_pose_mode", text="+" if pose.is_relative else "A").pose_index = pose_index
        row.operator("pt.toggle_pose_mirror", text="", icon='OUTLINER_OB_MESH', depress=pose.is_mirrored).pose_index = pose_index
        row.operator("pt.delete_pose", text="", icon='TRASH').pose_index = pose_index
        row.operator("pt.duplicate_pose", text="", icon='DUPLICATE').pose_index = pose_index
        row = box.row(align=True)
        row.operator("pt.reset_progress", text="", icon='FILE_REFRESH').pose_index = pose_index
        row.operator("pt.set_progress_minus1", text="-1").pose_index = pose_index
        row.operator("pt.set_progress_minus025", text="-0.25").pose_index = pose_index
        row.operator("pt.set_progress_minus01", text="-0.1").pose_index = pose_index
        row.separator()
        row.operator("pt.set_progress_plus01", text="+0.1").pose_index = pose_index
        row.operator("pt.set_progress_plus025", text="+0.25").pose_index = pose_index
        row.operator("pt.set_progress_plus1", text="+1").pose_index = pose_index

# Preferences panel for Pose Tool
class PTPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__
    if TYPE_CHECKING:
        presets_path: str
    else:
        __annotations__ = {
            "presets_path": StringProperty(
                name="Presets Path",
                description="Default path to the folder containing pose presets",
                default="p:\\- - - - - SCRIPTS\\- - - - PRESETS\\4_Pose_presets",
                subtype="DIR_PATH",
            )
        }

    def draw(self, context):
        layout = self.layout
        layout.label(text="SIM posetool Settings")
        layout.prop(self, "presets_path", text="Default Presets Path")

# Register global properties
def register_properties():
    bpy.types.Scene.sim_pt_use_rotation = BoolProperty(name="Use Rotation", default=True)
    bpy.types.Scene.sim_pt_use_location = BoolProperty(name="Use Location", default=True)
    bpy.types.Scene.sim_pt_use_scale = BoolProperty(name="Use Scale", default=True)
    bpy.types.Scene.sim_pt_settings_expanded = BoolProperty(name="Settings Expanded", default=True)
    bpy.types.Scene.sim_pt_apply_to_all_bones = BoolProperty(name="Apply to All Bones", default=False)
    bpy.types.Scene.sim_pt_presets_path = StringProperty(
        name="Presets Path",
        description="Path to the folder containing pose presets",
        default="p:\\- - - - - SCRIPTS\\- - - - PRESETS\\4_Pose_presets",
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
        items=lambda self, context: [(f, f, "") for f in os.listdir(context.scene.sim_pt_presets_path) if f.endswith('.json')] if os.path.exists(context.scene.sim_pt_presets_path) else []
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

# Registration
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

if __name__ == "__main__":
    register()
