from typing import TYPE_CHECKING, Any

import bpy  # type: ignore[import-not-found]
from bpy.props import (  # type: ignore[import-not-found]
    BoolProperty,
    CollectionProperty,
    FloatProperty,
    StringProperty,
)

from .core_apply import preview_pose_progress, update_pose


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


class PTPoseItem(bpy.types.PropertyGroup):
    if TYPE_CHECKING:
        name: str
        bone_poses: Any
        combined_progress: float
        preview_progress: float
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
            "preview_progress": FloatProperty(
                name="Progress",
                description="Preview pose progress before confirming",
                default=0.1,
                min=-1.0,
                max=1.0,
                update=lambda self, context: preview_pose_progress(self, context, self.preview_progress),
            ),
            "is_active": BoolProperty(default=False),
            "is_relative": BoolProperty(default=False),
            "is_mirrored": BoolProperty(default=False),
            "group_name": StringProperty(name="Group", default=""),
        }
