"""
Property definitions and update callbacks
"""

import bpy
from .geometry import KeycapGenerator


def update_keycap(self, context):
    """Regenerate keycap when properties change"""
    # Find existing keycap
    keycap = bpy.data.objects.get("Keycap")
    if keycap:
        # Store other props
        props = context.scene.keycap_props
        # Delete old keycap
        bpy.data.objects.remove(keycap, do_unlink=True)
        # Generate new one
        KeycapGenerator.create_keycap(
            width=float(props.width),
            profile_type=props.profile_type,
            profile_row=int(props.profile_row),
            bevel_vertical=props.bevel_vertical,
            stem_type=props.stem_type,
        )


def update_bevels(self, context):
    """Update bevel modifiers when bevel properties change"""
    obj = context.active_object
    if obj is None:
        return

    props = context.scene.keycap_props

    for mod in obj.modifiers:
        if mod.type == "BEVEL":
            if mod.name == "Bevel_Vert_Mod":
                mod.width = props.bevel_vertical


class KeycapProperties(bpy.types.PropertyGroup):
    """Property group for keycap parameters"""

    profile_type: bpy.props.EnumProperty(
        name="Profile Type",
        description="Keycap profile family",
        items=[
            ("CHERRY", "Cherry", "Cherry profile (low, sculpted)"),
            ("OEM", "OEM", "OEM profile (medium height, sculpted)"),
            ("SA", "SA", "SA profile (tall, spherical top)"),
        ],
        default="CHERRY",
        update=update_keycap,
    )

    width: bpy.props.EnumProperty(
        name="Width",
        description="Keycap width in units",
        items=[
            ("1", "1U - Alphas", "Standard alphanumeric keys"),
            ("1.25", "1.25U - Modifiers", "Ctrl, Alt, Win keys"),
            ("1.5", "1.5U - Tab", "Tab key on some layouts"),
            ("1.75", "1.75U - Caps Lock", "Caps Lock on 65%/HHKB layouts"),
            ("2", "2U - Backspace", "Backspace, numpad 0"),
            ("2.25", "2.25U - Enter/Shift", "Enter, Left Shift on some layouts"),
            ("2.75", "2.75U - Right Shift", "Right Shift on standard layouts"),
            ("6", "6U - Spacebar", "Spacebar on compact layouts"),
            ("6.25", "6.25U - Spacebar", "Standard TKL/full-size spacebar"),
            ("7", "7U - Spacebar", "Spacebar on some custom layouts"),
        ],
        default="1",
        update=update_keycap,
    )

    profile_row: bpy.props.EnumProperty(
        name="Profile Row",
        description="Cherry profile row number",
        items=[
            ("1", "R1 (Top)", "Top row profile"),
            ("2", "R2", "Second row profile"),
            ("3", "R3 (Home)", "Home row profile"),
            ("4", "R4 (Bottom)", "Bottom row profile"),
        ],
        default="3",
        update=update_keycap,
    )

    bevel_vertical: bpy.props.FloatProperty(
        name="Corner Bevels",
        description="Bevel radius for top and vertical edges (mm)",
        default=1.5,
        min=0.0,
        max=2.0,
        step=10,
        update=update_bevels,
    )

    stem_type: bpy.props.EnumProperty(
        name="Stem Type",
        description="Switch stem type",
        items=[
            ("CHERRY_MX", "Cherry MX", "Cherry MX compatible stem"),
            ("None", "None", "No stem"),
        ],
        default="CHERRY_MX",
        update=update_keycap,
    )


class KeycapExportProperties(bpy.types.PropertyGroup):
    """Property group for export settings"""

    export_path: bpy.props.StringProperty(
        name="Export Path",
        description="Where to save exported files",
        subtype="DIR_PATH",
        default="//exports/",
    )

    file_format: bpy.props.EnumProperty(
        name="File Format",
        description="Choose export format",
        items=[
            ("STL", "STL", "Export as STL"),
            # ("OBJ", "OBJ", "Export as OBJ"),
            # ("GLB", "GLB", "Export as GLB"),
        ],
        default="STL",
    )

    open_in_slicer: bpy.props.BoolProperty(
        name="Open in slicer after export",
        description="Automatically open exported file in your slicer",
        default=False,
    )

    slicer_path: bpy.props.StringProperty(
        name="Slicer Executable",
        description="Path to your slicer executable",
        subtype="FILE_PATH",
        default="",
    )
