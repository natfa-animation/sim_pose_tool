# SIM posetool (Blender Add-on)

## Description

**SIM posetool** is a Blender add-on for managing armature pose presets: recording poses from selected bones, organizing them into groups, and applying them with an adjustable progress value for interpolation.

It appears in:

- **3D Viewport → Sidebar (N) → “SIM anima” tab → “SIM posetool” panel**

## Features

### Pose management

- **Record Pose**: create a new pose from the currently selected pose bones.
- **Update Pose**: refresh an existing pose’s stored bone transforms from the currently selected pose bones (and rebuild which bones participate).
- **Duplicate Pose**: duplicate a pose (creates a `*_Copy`).
- **Delete Pose**: delete a single pose.
- **Delete All Poses**: clear all poses on the selected armature.

### Pose grouping

- **Create Pose Group**: create a group (optionally nested under a parent group).
- **Group hierarchy UI**: expand/collapse groups and view nested groups.
- **Delete Pose Group**: removes the group and clears group links from poses and child groups.

### Progress system (`combined_progress`)

- Each pose has a **progress value** (`combined_progress`, range `-1.0 .. 1.0`) used when applying the pose.
- Quick buttons in the UI: **-1**, **-0.25**, **-0.1**, **+0.1**, **+0.25**, **+1**, plus **Reset**.

### Mirror functionality

- Per-pose **Mirror toggle**.
- Mirror name resolution supports common suffixes like:
  - `_Left` / `_Right`
  - `.L` / `.R`

### Import / Export / Merge (JSON)

- **Export** poses + groups to a `.json` file.
- **Import** poses + groups from a `.json` file (replaces existing).
- **Merge** poses + groups from a `.json` file (adds to existing).

### Presets system (folder-based)

- Choose a **Presets Folder**.
- Dropdown lists `.json` files in that folder.
- **Load Preset** loads the selected preset file (replaces current poses/groups on the armature).

### Armature selection behavior

- Uses **Scene → Selected Armature** when set.
- Otherwise falls back to the **active object** (must be an Armature).

### Toggles

- **Rotation / Location / Scale** toggles for pose application behavior.
- **Apply to All Bones** toggle (otherwise uses selected bones).

## Installation

### 1) Create the ZIP correctly

You must zip the **add-on folder**, not the individual files.

Correct structure:

```text
my_addon.zip
└── my_addon/
    ├── __init__.py
    ├── constants.py
    ├── props_types.py
    ├── core_apply.py
    ├── scene_props.py
    ├── operators_pose.py
    ├── operators_io.py
    ├── operators_progress.py
    ├── ui_panel.py
    └── LICENSE
```

### 2) Install in Blender

1. **Edit → Preferences → Add-ons**
2. Click **Install…**
3. Select your `my_addon.zip`
4. Enable the add-on (checkbox)

### What to zip / what NOT to zip

- Zip: the **folder that contains `__init__.py`**
- Do NOT zip: the files directly at the ZIP root (Blender expects a top-level folder)

## Usage

### Select an armature

1. Open **3D Viewport → Sidebar (N) → SIM anima → SIM posetool**
2. Set **Armature** (or make your armature the active object)

### Create a pose

1. Select bones in **Pose Mode**
2. Click **Add** (Record Pose)
3. Enter a name and confirm

### Apply a pose (via progress)

- Use the per-pose progress buttons (**-1 … +1**) to set the pose progress value.
- Use **Reset** to return the progress value to its default.

### Update an existing pose

1. Select the bones that should be part of the pose
2. Click **Update** on that pose

### Organize poses into groups

1. Click **Create Group**
2. (Optional) pick a parent group to nest it
3. Assign poses to groups using the group field next to each pose name

### Import / export / merge

- Expand **Settings**
- Use:
  - **Export** to save poses/groups to JSON
  - **Import** to replace current poses/groups from JSON
  - **Merge** to add poses/groups from JSON into the current set

### Use presets (folder dropdown)

1. Expand **Presets**
2. Set **Presets Folder**
3. Choose a preset from the dropdown
4. Click **Load Preset**

## UI Overview

The **SIM posetool** panel includes:

- **Armature selector**
- **Top actions**
  - Record Pose (Add)
  - Delete All Poses
  - Create Pose Group
- **Settings (expandable)**
  - Rotation / Location / Scale toggles
  - Apply to All Bones toggle
  - Export / Import / Merge buttons
- **Presets (expandable)**
  - Presets Folder path
  - Preset dropdown (lists `.json` files)
  - Load Preset button
- **Pose list**
  - Ungrouped poses
  - Group hierarchy (nested groups)
  - Per-pose controls: select bones, update, relative/absolute toggle, mirror toggle, delete, duplicate, progress buttons

## Compatibility

- Blender version: **Blender 5+** (tested in Blender 5).
- Many actions are **context-sensitive** (armature selection, Pose Mode availability). The add-on may switch modes internally when needed.

## Known Issues / Notes

- Most operators require a valid **Armature** (Selected Armature or active object).
- Some actions depend on Blender context (mode switching, selection state); if Blender cannot switch to **Pose Mode**, an operation may cancel.
- Applying poses is **keyframe-driven** (pose application inserts keyframes on the current frame for enabled channels).

## Developer Notes (optional)

Module layout:

- `__init__.py`: `bl_info`, registration, preferences, class list
- `constants.py`: shared constants (default presets path)
- `props_types.py`: PropertyGroup types (pose item / bone data / groups)
- `core_apply.py`: pose application logic (`update_pose`) + mirror name helper
- `scene_props.py`: Scene properties (toggles, armature pointer, presets)
- `operators_*.py`: operators grouped by purpose
- `ui_panel.py`: View3D sidebar panel

`update_pose()` is the core behavior: it evaluates pose data, respects toggles, and applies transforms/keyframes based on the pose’s current progress value.

## License

See `LICENSE`.
