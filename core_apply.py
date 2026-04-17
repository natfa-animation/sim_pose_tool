import bpy  # type: ignore[import-not-found]
from mathutils import Euler, Quaternion, Vector  # type: ignore[import-not-found]

_PREVIEW_SUSPEND = False
_PREVIEW_SESSION = None


def _pose_bone_is_selected(pose_bone):
    try:
        return pose_bone.select
    except AttributeError:
        return pose_bone.bone.select


def _resolve_armature_from_context(context):
    if not context or not getattr(context, "scene", None):
        return None
    return context.scene.sim_pt_selected_armature if context.scene.sim_pt_selected_armature else context.active_object


def _capture_armature_pose_state(armature_obj):
    state = {}
    if not armature_obj or armature_obj.type != 'ARMATURE' or not getattr(armature_obj, "pose", None):
        return state
    for pose_bone in armature_obj.pose.bones:
        state[pose_bone.name] = {
            "location": pose_bone.location.copy(),
            "rotation_mode": pose_bone.rotation_mode,
            "rotation_quaternion": pose_bone.rotation_quaternion.copy(),
            "rotation_euler": pose_bone.rotation_euler.copy(),
            "rotation_axis_angle": tuple(pose_bone.rotation_axis_angle),
            "scale": pose_bone.scale.copy(),
        }
    return state


def _restore_armature_pose_state(armature_obj, state):
    if not armature_obj or armature_obj.type != 'ARMATURE' or not getattr(armature_obj, "pose", None):
        return
    for bone_name, bone_state in state.items():
        if bone_name not in armature_obj.pose.bones:
            continue
        pose_bone = armature_obj.pose.bones[bone_name]
        pose_bone.rotation_mode = bone_state["rotation_mode"]
        pose_bone.location = bone_state["location"]
        pose_bone.rotation_quaternion = bone_state["rotation_quaternion"]
        pose_bone.rotation_euler = bone_state["rotation_euler"]
        pose_bone.rotation_axis_angle = bone_state["rotation_axis_angle"]
        pose_bone.scale = bone_state["scale"]
    armature_obj.update_tag()
    bpy.context.view_layer.update()


def preview_pose_progress(pose, context, progress_value):
    global _PREVIEW_SESSION
    if _PREVIEW_SUSPEND:
        return
    armature = _resolve_armature_from_context(context)
    if not armature or armature.type != 'ARMATURE':
        return
    pose_ptr = pose.as_pointer() if hasattr(pose, "as_pointer") else None
    session_key = (armature.name, pose_ptr)
    if not _PREVIEW_SESSION or _PREVIEW_SESSION.get("key") != session_key:
        _PREVIEW_SESSION = {
            "key": session_key,
            "armature_name": armature.name,
            "pose_ptr": pose_ptr,
            "state": _capture_armature_pose_state(armature),
        }
    _restore_armature_pose_state(armature, _PREVIEW_SESSION.get("state", {}))
    try:
        t = float(progress_value) / 100.0
    except Exception:
        return
    update_pose(pose, context, progress_override=t, insert_keyframes=False, push_undo=False)


def cancel_pose_preview(pose, context):
    global _PREVIEW_SESSION
    armature = _resolve_armature_from_context(context)
    if not _PREVIEW_SESSION:
        return
    pose_ptr = pose.as_pointer() if hasattr(pose, "as_pointer") else None
    if _PREVIEW_SESSION.get("pose_ptr") != pose_ptr:
        return
    if not armature or armature.name != _PREVIEW_SESSION.get("armature_name"):
        armature_name = _PREVIEW_SESSION.get("armature_name")
        armature = bpy.data.objects.get(armature_name) if armature_name else None
    if not armature:
        _PREVIEW_SESSION = None
        return
    _restore_armature_pose_state(armature, _PREVIEW_SESSION.get("state", {}))
    _PREVIEW_SESSION = None


def clear_pose_preview():
    global _PREVIEW_SESSION
    _PREVIEW_SESSION = None


def is_pose_preview_active(pose, context):
    if not _PREVIEW_SESSION:
        return False
    armature = _resolve_armature_from_context(context)
    if not armature:
        return False
    pose_ptr = pose.as_pointer() if hasattr(pose, "as_pointer") else None
    return _PREVIEW_SESSION.get("key") == (armature.name, pose_ptr)


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


def update_pose(pose, context, *, progress_override=None, insert_keyframes=True, push_undo=True):
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
    
    t = progress_override if progress_override is not None else pose.combined_progress
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
                    relative_quat = relative_quat.normalized()
                    axis, angle = relative_quat.to_axis_angle()
                    delta_quat = Quaternion(axis, angle * t)
                    pose_bone.rotation_quaternion = current_quat @ delta_quat
                    if insert_keyframes:
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
                    if insert_keyframes:
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
                if insert_keyframes:
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
                if insert_keyframes:
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
                    if insert_keyframes:
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
                    if insert_keyframes:
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
                if insert_keyframes:
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
                if insert_keyframes:
                    pose_bone.keyframe_insert(data_path="scale", frame=current_frame)
    
    armature.update_tag()
    bpy.context.view_layer.update()
    
    if push_undo:
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
