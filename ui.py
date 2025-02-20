"""
UI Panel for keycap generation
"""

import bpy


class KEYCAP_PT_main(bpy.types.Panel):
    """Main panel for keycap generation"""

    bl_label = "Keycap Generator"
    bl_idname = "KEYCAP_PT_main"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Keycap Gen"

    def draw(self, context):
        layout = self.layout
        props = context.scene.keycap_props

        # Parameters
        box = layout.box()
        box.label(text="Parameters:", icon="PREFERENCES")
        box.prop(props, "width")

        split = box.split(factor=0.5)
        split.label(text="Profile Type: ")
        split.prop(props, "profile_type", text="")

        split = box.split(factor=0.4)
        split.label(text="Profile Row: ")
        split.prop(props, "profile_row", text="")

        split = box.split(factor=0.3)
        split.label(text="Stem Type: ")
        split.prop(props, "stem_type", text="")

        # Bevel settings
        bevel_box = layout.box()
        bevel_box.label(text="Bevels:", icon="MOD_BEVEL")
        bevel_box.prop(props, "bevel_vertical")

        # Generate button
        layout.separator()
        gen_box = layout.box()
        gen_box.operator("keycap.generate", text="Generate Keycap", icon="EVENT_F1")
        # Bake button
        gen_box.operator(
            "keycap.bake", text="Bake Keycap (Apply Mods)", icon="RENDER_RESULT"
        )

        ex = context.scene.export_settings

        # Export Settings
        layout.separator()
        export_box = layout.box()
        export_box.label(text="Export Settings:", icon="EXPORT")
        export_box.prop(ex, "export_path")
        export_box.prop(ex, "file_format")
        export_box.prop(ex, "open_in_slicer")
        if ex.open_in_slicer:
            export_box.prop(ex, "slicer_path")
        export_box.operator("keycap.export", icon="EXPORT")
