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
import bmesh
from mathutils import Vector
from math import radians
import math


# Keycap geometry generator
class KeycapGenerator:
    """Generates keycap geometry with parametric controls"""

    @staticmethod
    def create_keycap(
        width=1.0, profile_row=3, corner_radius=0.5, stem_type="CHERRY_MX"
    ):
        """
        Generate a keycap mesh

        Args:
            width: Keycap width in units (1.0 = 1U)
            profile_row: Row number for Cherry profile (1-4)
            corner_radius: Fillet radius in mm
            stem_type: Type of stem ('CHERRY_MX', 'TOPRE')
        """
        # Create new mesh and object
        mesh = bpy.data.meshes.new("Keycap")
        obj = bpy.data.objects.new("Keycap", mesh)
        bpy.context.collection.objects.link(obj)

        # Create bmesh
        bm = bmesh.new()

        # Cherry profile measurements (in mm, converted to Blender units)
        base_width = width * 18.0  # 1U = 18mm
        base_height = 18.0
        wall_thickness = 0.91  # Wall thickness in mm

        # Top dimensions (sculpted)
        top_width = base_width - 4.0
        top_height = base_height - 4.0

        # Height varies by row for Cherry profile
        row_heights = {
            1: 11.5,  # R1 (top row)
            2: 9.5,  # R2
            3: 8.5,  # R3 (home row)
            4: 9.5,  # R4
        }
        keycap_height = row_heights.get(profile_row, 8.5)

        # Outer shell vertices
        # Create base vertices (bottom outer)
        base_outer = [
            bm.verts.new((-base_width / 2, -base_height / 2, 0)),
            bm.verts.new((base_width / 2, -base_height / 2, 0)),
            bm.verts.new((base_width / 2, base_height / 2, 0)),
            bm.verts.new((-base_width / 2, base_height / 2, 0)),
        ]

        # Create top vertices (outer)
        top_outer = [
            bm.verts.new((-top_width / 2, -top_height / 2, keycap_height)),
            bm.verts.new((top_width / 2, -top_height / 2, keycap_height)),
            bm.verts.new((top_width / 2, top_height / 2, keycap_height)),
            bm.verts.new((-top_width / 2, top_height / 2, keycap_height)),
        ]

        # Inner shell vertices (offset by wall thickness)
        # Calculate inner dimensions
        base_inner_width = base_width - (wall_thickness * 2)
        base_inner_height = base_height - (wall_thickness * 2)
        top_inner_width = top_width - (wall_thickness * 2)
        top_inner_height = top_height - (wall_thickness * 2)
        inner_top_z = keycap_height - wall_thickness

        # Create base inner vertices (just above bottom)
        base_inner = [
            bm.verts.new(
                (-base_inner_width / 2, -base_inner_height / 2, wall_thickness)
            ),
            bm.verts.new(
                (base_inner_width / 2, -base_inner_height / 2, wall_thickness)
            ),
            bm.verts.new((base_inner_width / 2, base_inner_height / 2, wall_thickness)),
            bm.verts.new(
                (-base_inner_width / 2, base_inner_height / 2, wall_thickness)
            ),
        ]

        # Create top inner vertices
        top_inner = [
            bm.verts.new((-top_inner_width / 2, -top_inner_height / 2, inner_top_z)),
            bm.verts.new((top_inner_width / 2, -top_inner_height / 2, inner_top_z)),
            bm.verts.new((top_inner_width / 2, top_inner_height / 2, inner_top_z)),
            bm.verts.new((-top_inner_width / 2, top_inner_height / 2, inner_top_z)),
        ]

        # Create faces - Outer shell
        # Top face (outer)
        bm.faces.new(top_outer)

        # Outer side faces
        for i in range(4):
            next_i = (i + 1) % 4
            bm.faces.new(
                [base_outer[i], base_outer[next_i], top_outer[next_i], top_outer[i]]
            )

        # Create faces - Inner shell
        # Top face (inner) - reversed to face inward
        bm.faces.new(top_inner[::-1])

        # Inner side faces
        for i in range(4):
            next_i = (i + 1) % 4
            bm.faces.new(
                [base_inner[i], top_inner[i], top_inner[next_i], base_inner[next_i]]
            )

        # Connect bottom edges (rim where outer meets inner)
        for i in range(4):
            next_i = (i + 1) % 4
            # Bottom rim face
            bm.faces.new(
                [base_outer[i], base_inner[i], base_inner[next_i], base_outer[next_i]]
            )

        # Apply corner radius (bevel)
        if corner_radius > 0:
            edges_to_bevel = [
                e for e in bm.edges if e.verts[0].co.z > 0 and e.verts[1].co.z > 0
            ]
            bmesh.ops.bevel(
                bm, geom=edges_to_bevel, offset=corner_radius / 10, segments=3
            )

        # Write bmesh to mesh
        bm.to_mesh(mesh)
        bm.free()

        # Set object as active
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)

        # Add stem using boolean modifier (after mesh is created)
        if stem_type == "CHERRY_MX":
            KeycapGenerator._add_cherry_stem(obj)

        # Add smooth shading with auto-smooth
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.shade_smooth()

        # Enable auto-smooth for better shading
        obj.data.use_auto_smooth = True
        obj.data.auto_smooth_angle = radians(30)  # 30 degree threshold

        return obj

    @staticmethod
    def _add_cherry_stem(keycap_obj):
        """Add Cherry MX stem cylinder with cross cutout to the bottom of keycap using boolean modifier"""
        # Cherry MX stem dimensions (in mm)
        stem_outer_radius = 5.6 / 2  # Outer cylinder diameter ~5.5mm
        stem_height = 7.7  # Height of stem extending down
        cross_length = 4.15  # Cross arm length
        cross_width = 1.29  # Cross arm width

        # Create stem cylinder
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=64,
            radius=stem_outer_radius,
            depth=stem_height,
            location=(0, 0, stem_height / 2),
        )
        stem_cylinder = bpy.context.active_object
        stem_cylinder.name = "Stem_Cylinder"

        # Create vertical bar of cross
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, stem_height / 2))
        v_cross = bpy.context.active_object
        v_cross.name = "Cross_Vertical"
        v_cross.scale = (cross_width, cross_length, stem_height + 0.2)

        # Create horizontal bar of cross
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, stem_height / 2))
        h_cross = bpy.context.active_object
        h_cross.name = "Cross_Horizontal"
        h_cross.scale = (cross_length, cross_width, stem_height + 0.2)

        # TODO: join cross object and then apply boolean difference

        # Apply boolean difference to cut vertical cross from cylinder
        bool_mod_v = stem_cylinder.modifiers.new(name="Boolean_V", type="BOOLEAN")
        bool_mod_v.operation = "DIFFERENCE"
        bool_mod_v.object = v_cross
        bool_mod_v.solver = "FAST"

        # Apply boolean difference to cut horizontal cross from cylinder
        bool_mod_h = stem_cylinder.modifiers.new(name="Boolean_H", type="BOOLEAN")
        bool_mod_h.operation = "DIFFERENCE"
        bool_mod_h.object = h_cross
        bool_mod_h.solver = "FAST"

        # Apply modifiers
        bpy.context.view_layer.objects.active = stem_cylinder
        bpy.ops.object.modifier_apply(modifier="Boolean_V")
        bpy.ops.object.modifier_apply(modifier="Boolean_H")

        # Delete cross objects
        bpy.data.objects.remove(v_cross, do_unlink=True)
        bpy.data.objects.remove(h_cross, do_unlink=True)

        # Triangulate stem faces to avoid n-gons
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.quads_convert_to_tris(quad_method="BEAUTY", ngon_method="BEAUTY")
        bpy.ops.mesh.normals_make_consistent(inside=False)
        bpy.ops.object.mode_set(mode="OBJECT")

        # Deselect all first
        bpy.ops.object.select_all(action="DESELECT")

        # Join stem with keycap
        keycap_obj.select_set(True)
        stem_cylinder.select_set(True)
        bpy.context.view_layer.objects.active = keycap_obj
        bpy.ops.object.join()

        # Fix normals after joining
        bpy.context.view_layer.objects.active = keycap_obj
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.normals_make_consistent(inside=False)
        bpy.ops.object.mode_set(mode="OBJECT")


# Operator to generate keycap
class KEYCAP_OT_generate(bpy.types.Operator):
    """Generate a keycap with specified parameters"""

    bl_idname = "keycap.generate"
    bl_label = "Generate Keycap"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        props = context.scene.keycap_props

        KeycapGenerator.create_keycap(
            width=props.width,
            profile_row=int(props.profile_row),
            corner_radius=props.corner_radius,
            stem_type=props.stem_type,
        )

        self.report({"INFO"}, f"Generated {props.width}U keycap (R{props.profile_row})")
        return {"FINISHED"}


# Property group for keycap parameters
class KeycapProperties(bpy.types.PropertyGroup):
    width: bpy.props.FloatProperty(
        name="Width",
        description="Keycap width in units",
        default=1.0,
        min=1.0,
        max=6.25,
        step=25,
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
    )

    corner_radius: bpy.props.FloatProperty(
        name="Corner Radius",
        description="Fillet radius for edges (mm)",
        default=0.5,
        min=0.0,
        max=2.0,
        step=10,
    )

    stem_type: bpy.props.EnumProperty(
        name="Stem Type",
        description="Switch stem type",
        items=[
            ("CHERRY_MX", "Cherry MX", "Cherry MX compatible stem"),
            ("TOPRE", "Topre", "Topre compatible stem (WIP)"),
        ],
        default="CHERRY_MX",
    )


# UI Panel
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

        # Title
        layout.label(text="Phase 1 - Core Functionality", icon="MESH_CUBE")

        # Parameters
        box = layout.box()
        box.label(text="Parameters:", icon="PREFERENCES")
        box.prop(props, "width")
        box.prop(props, "profile_row")
        box.prop(props, "corner_radius")
        box.prop(props, "stem_type")

        # Generate button
        layout.separator()
        layout.operator("keycap.generate", text="Generate Keycap", icon="MESH_CUBE")


# Registration
classes = (
    KeycapProperties,
    KEYCAP_OT_generate,
    KEYCAP_PT_main,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.keycap_props = bpy.props.PointerProperty(type=KeycapProperties)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.keycap_props


if __name__ == "__main__":
    register()
