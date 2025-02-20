"""
Procedural Keycap Generator for Blender
A tool for generating parametric keycaps for mechanical keyboards
"""

bl_info = {
    "name": "Procedural Keycap Generator",
    "author": "Mackenzie Sampson",
    "version": (1, 0, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > Keycap Gen",
    "description": "Generate parametric keycaps for mechanical keyboards",
    "category": "Add Mesh",
}

import bpy

# Import submodules
from . import geometry
from . import properties
from . import operators
from . import ui

# Collect all classes that need to be registered
classes = (
    properties.KeycapProperties,
    properties.KeycapExportProperties,
    operators.KEYCAP_OT_generate,
    operators.KEYCAP_OT_bake,
    operators.KEYCAP_OT_export,
    ui.KEYCAP_PT_main,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.keycap_props = bpy.props.PointerProperty(
        type=properties.KeycapProperties
    )
    bpy.types.Scene.export_settings = bpy.props.PointerProperty(
        type=properties.KeycapExportProperties
    )


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.keycap_props
    del bpy.types.Scene.export_settings


if __name__ == "__main__":
    register()
