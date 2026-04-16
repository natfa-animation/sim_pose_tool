import bpy  # type: ignore[import-not-found]
import os


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
        row.prop(pose, "preview_progress", text="Progress", slider=True)
        row.operator("pt.confirm_progress_preview", text="", icon='CHECKMARK').pose_index = pose_index
        row.operator("pt.cancel_progress_preview", text="", icon='CANCEL').pose_index = pose_index
