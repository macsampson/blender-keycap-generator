"""
Blender operators for keycap generation and export
"""

import bpy
import os
import subprocess
from .geometry import KeycapGenerator


class KEYCAP_OT_generate(bpy.types.Operator):
    """Generate a keycap with specified parameters"""

    bl_idname = "keycap.generate"
    bl_label = "Generate Keycap"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        # Set unit system to metric with millimeter scale
        context.scene.unit_settings.system = "METRIC"
        context.scene.unit_settings.scale_length = 0.001  # 1 BU = 1mm
        context.scene.unit_settings.length_unit = "MILLIMETERS"

        for area in bpy.context.screen.areas:
            if area.type == "VIEW_3D":
                space = area.spaces.active
                space.overlay.grid_scale = 0.001  # Each grid square = 1 mm

        props = context.scene.keycap_props

        KeycapGenerator.create_keycap(
            width=float(props.width),
            profile_type=props.profile_type,
            profile_row=int(props.profile_row),
            bevel_vertical=props.bevel_vertical,
            stem_type=props.stem_type,
        )

        self.report({"INFO"}, f"Generated {props.width}U keycap (R{props.profile_row})")
        return {"FINISHED"}


class KEYCAP_OT_bake(bpy.types.Operator):
    """Apply all modifiers to the selected keycap"""

    bl_idname = "keycap.bake"
    bl_label = "Bake Keycap"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        obj = context.active_object

        if not obj:
            self.report({"ERROR"}, "No object selected")
            return {"CANCELLED"}

        if not obj.modifiers:
            self.report({"WARNING"}, "No modifiers to apply")
            return {"CANCELLED"}

        # Apply all modifiers
        modifier_count = len(obj.modifiers)
        bpy.context.view_layer.objects.active = obj

        for mod in list(obj.modifiers):
            try:
                bpy.ops.object.modifier_apply(modifier=mod.name)
            except Exception as e:
                self.report({"ERROR"}, f"Failed to apply modifier {mod.name}: {str(e)}")
                return {"CANCELLED"}

        self.report({"INFO"}, f"Applied {modifier_count} modifier(s)")
        return {"FINISHED"}


class KEYCAP_OT_export(bpy.types.Operator):
    """Export the selected keycap using current export settings"""

    bl_idname = "keycap.export"
    bl_label = "Export Keycap"
    bl_description = "Export the selected keycap using current export settings"

    def execute(self, context):
        obj = context.active_object
        ex = context.scene.export_settings

        if obj is None:
            self.report({"WARNING"}, "No active object to export")
            return {"CANCELLED"}

        export_dir = bpy.path.abspath(ex.export_path)
        os.makedirs(export_dir, exist_ok=True)

        filename = f"{obj.name}.{ex.file_format.lower()}"
        export_path = os.path.join(export_dir, filename)

        if ex.file_format == "STL":
            bpy.ops.wm.stl_export(filepath=export_path, check_existing=True)
        # elif ex.file_format == "OBJ":
        #     bpy.ops.export_scene.obj(filepath=export_path, use_selection=True)
        # elif ex.file_format == "GLB":
        #     bpy.ops.export_scene.gltf(
        #         filepath=export_path, export_format="GLB", use_selection=True
        # )

        self.report({"INFO"}, f"Exported {obj.name} as {ex.file_format}")

        if ex.open_in_slicer and ex.slicer_path:
            try:
                subprocess.Popen([ex.slicer_path, export_path])
            except Exception as e:
                self.report({"ERROR"}, f"Failed to open slicer: {e}")

        return {"FINISHED"}
