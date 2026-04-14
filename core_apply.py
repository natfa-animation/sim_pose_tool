import bpy  # type: ignore[import-not-found]
from mathutils import Euler, Quaternion, Vector  # type: ignore[import-not-found]


def _pose_bone_is_selected(pose_bone):
    try:
        return pose_bone.select
    except AttributeError:
        return pose_bone.bone.select


def get_mirror_bone_name(bone_name):
    bone_name_lower = bone_name.lower()
    if bone_name_lower.endswith('_left'):
        return bone_name[:-5] + '_Right'
    elif bone_name_lower.endswith('_right'):
        return bone_name[:-6] + '_Left'
    elif bone_name_lower.endswith('.l'):
        return bone_name[:-2] + '.R'
    elif bone_name_lower.endswith('.r'):
        return bone_name[:-2] + '.L'
    return None


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
    selected_bones = {pose_bone.name for pose_bone in armature.pose.bones if _pose_bone_is_selected(pose_bone)}
    
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

