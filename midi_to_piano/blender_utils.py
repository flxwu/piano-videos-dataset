"""
Utility functions for adding/manipulating objects in the blender scene.
"""

import bpy  # type: ignore # pylint: disable=import-error


def build_key(
    name: str,
    width: float,
    height: float,
    length: float,
    left: float,
    top: float,
    is_black: bool,
):
    """Create a key whose **left edge** sits at *left* and **top edge** sits at *top* and return the object.
    note: length = "tiefe"
    """
    cube_x = left + width / 2
    cube_y = top - length / 2
    bpy.ops.mesh.primitive_cube_add(size=1, location=(cube_x, cube_y, height))

    key = bpy.context.object
    key.name = name
    key.scale = (width, length, height)
    key.rotation_mode = "XYZ"

    # UNIQUE material per key -------------------------------------
    mat = bpy.data.materials.new(f"{name}_Mat")
    base_colour = (0, 0, 0, 1) if is_black else (0.9, 0.9, 0.9, 1)
    mat.diffuse_color = base_colour
    key.data.materials.append(mat)

    set_origin_at_back(key, length)
    return key


def clear_scene():
    """Delete all objects in the current scene."""
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def set_origin_at_back(obj, length):
    """Move cursor to the rear edge of *obj* and set that as the origin."""
    x, y, _ = obj.location
    bpy.context.scene.cursor.location = (x, y + length / 2, 0)
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR", center="MEDIAN")
