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

