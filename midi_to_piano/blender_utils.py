"""
Utility functions for adding/manipulating objects in the blender scene.
"""

import bpy  # type: ignore # pylint: disable=import-error

def clear_scene():
    """Delete all objects in the current scene."""
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
