# Agent Instructions (pose_tool)

## Project summary

This repository is a Blender add-on package (**SIM posetool**) split across multiple Python modules at the add-on root (folder add-on with `__init__.py`).

## Goals / priorities

- Preserve existing add-on behavior unless the user explicitly requests a change.
- Keep compatibility fixes **small and isolated** (one issue per change when possible).
- Do not rename operators, classes, properties, or `bl_idname` values unless required for Blender/package safety.
- Treat registration/unregistration order as **behavior-critical**.

## Add-on structure (expected)

- `__init__.py`: `bl_info`, `PTPreferences`, `CLASSES`, `register()` / `unregister()`
- `constants.py`: shared constants (paths/literals)
- `props_types.py`: `PropertyGroup` types (pose data / pose item / groups)
- `core_apply.py`: pose application logic (`update_pose`) + helpers
- `scene_props.py`: Scene properties + Enum callbacks
- `operators_pose.py`: pose CRUD + selection-related operators + toggles
- `operators_io.py`: JSON import/export/merge + preset loading
- `operators_progress.py`: progress operators + mirror/mode toggles + reset
- `ui_panel.py`: View3D sidebar panel

## Blender-specific safety notes

- Avoid doing `bpy.ops.*` in property update callbacks unless unavoidable.
- Be defensive in dynamic callbacks (e.g. `EnumProperty(items=...)`) because Blender may evaluate them with `context=None`.
- Bone selection APIs can differ across Blender versions; prefer PoseBone-safe access patterns.

## Editing guidelines

- Keep diffs minimal and focused.
- Don’t “cleanup” formatting, naming, or logic opportunistically.
- Prefer adding tiny compatibility shims over large rewrites.
- Preserve Windows line endings if the repo is using CRLF (Git may warn about LF→CRLF).

## Verification checklist (manual)

- Install add-on from a ZIP that contains a single top-level folder with `__init__.py`.
- Enable add-on without errors in the Blender system console.
- Confirm panel appears: View3D → Sidebar → “SIM anima” tab.
- Smoke test: record pose, update pose, progress buttons, import/export, load preset.

