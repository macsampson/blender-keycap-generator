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

    def add_bevel_modifiers(obj):
        for name in ["Bevel_Top_Mod", "Bevel_Vert_Mod", "Bevel_Dish_Mod"]:
            if obj.modifiers.get(name):
                continue  # don't recreate if already exists

        top_mod = obj.modifiers.new("Bevel_Top_Mod", "BEVEL")
        top_mod.limit_method = "VGROUP"
        top_mod.vertex_group = "Bevel_Top_Rim"
        top_mod.segments = 3
        top_mod.use_clamp_overlap = True
        top_mod.width = bpy.context.scene.keycap_props.bevel_top_rim

        vert_mod = obj.modifiers.new("Bevel_Vert_Mod", "BEVEL")
        vert_mod.limit_method = "VGROUP"
        vert_mod.vertex_group = "Bevel_Vertical"
        vert_mod.segments = 3
        vert_mod.use_clamp_overlap = True
        vert_mod.width = bpy.context.scene.keycap_props.bevel_vertical

    #        dish_mod = obj.modifiers.new("Bevel_Dish_Mod", 'BEVEL')
    #        dish_mod.limit_method = 'VGROUP'
    #        dish_mod.vertex_group = "Bevel_Dish"
    #        dish_mod.segments = 3
    #        dish_mod.use_clamp_overlap = True
    #        dish_mod.width = bpy.context.scene.keycap_props.bevel_dish

    @staticmethod
    def create_keycap(
        width=1.0,
        profile_row=3,
        bevel_top_rim=0.3,
        bevel_vertical=0.5,
        stem_type="CHERRY_MX",
    ):
        """
        Generate a keycap mesh

        Args:
            width: Keycap width in units (1.0 = 1U)
            profile_row: Row number for Cherry profile (1-4)
            bevel_top_rim: Bevel radius for top rim edges in mm
            bevel_vertical: Bevel radius for vertical corner edges in mm
            stem_type: Type of stem ('CHERRY_MX', 'TOPRE')
        """
        # Create new mesh and object
        mesh = bpy.data.meshes.new("Keycap")
        obj = bpy.data.objects.new("Keycap", mesh)
        bpy.context.collection.objects.link(obj)

        # Create bmesh
        bm = bmesh.new()

        # Create edge tracking sets
        top_rim_edges = []
        vertical_edges = []

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
            bm.verts.new((-base_inner_width / 2, -base_inner_height / 2, 0)),
            bm.verts.new((base_inner_width / 2, -base_inner_height / 2, 0)),
            bm.verts.new((base_inner_width / 2, base_inner_height / 2, 0)),
            bm.verts.new((-base_inner_width / 2, base_inner_height / 2, 0)),
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
        top_face = bm.faces.new(top_outer)

        # Track top rim edges
        for edge in top_face.edges:
            top_rim_edges.append(edge)

        # Outer side faces
        for i in range(4):
            next_i = (i + 1) % 4
            face = bm.faces.new(
                [base_outer[i], base_outer[next_i], top_outer[next_i], top_outer[i]]
            )

            # Track vertical edges (corners)
            for edge in face.edges:
                v1, v2 = edge.verts
                # Vertical edge if both verts have same x,y but different z
                if abs(v1.co.x - v2.co.x) < 0.001 and abs(v1.co.y - v2.co.y) < 0.001:
                    if edge not in vertical_edges:
                        vertical_edges.append(edge)

        # Create faces - Inner shell
        # Top face (inner) - reversed to face inward
        bm.faces.new(top_inner[::-1])

        # Inner side faces
        for i in range(4):
            next_i = (i + 1) % 4
            face = bm.faces.new(
                [base_inner[i], top_inner[i], top_inner[next_i], base_inner[next_i]]
            )

            # Track inner vertical edges (corners)
            for edge in face.edges:
                v1, v2 = edge.verts
                # Vertical edge if both verts have same x,y but different z
                if abs(v1.co.x - v2.co.x) < 0.001 and abs(v1.co.y - v2.co.y) < 0.001:
                    if edge not in vertical_edges:
                        vertical_edges.append(edge)

        # Connect bottom edges (rim where outer meets inner)
        for i in range(4):
            next_i = (i + 1) % 4
            # Bottom rim face
            bm.faces.new(
                [base_outer[i], base_inner[i], base_inner[next_i], base_outer[next_i]]
            )

        # Mark top rim
        top_rim_verts = [v.index for e in top_rim_edges for v in e.verts]
        # Mark verticals
        vert_verts = [v.index for e in vertical_edges for v in e.verts]

        # Write bmesh to mesh
        bm.to_mesh(mesh)
        bm.free()

        # Create vertex group for top bevel
        obj.vertex_groups.new(name="Bevel_Top")
        obj.vertex_groups["Bevel_Top"].add(top_rim_verts, 1.0, "REPLACE")

        # Create vertex group for vertical bevels
        obj.vertex_groups.new(name="Bevel_Vertical")
        obj.vertex_groups["Bevel_Vertical"].add(vert_verts, 1.0, "REPLACE")

        KeycapGenerator.add_bevel_modifiers(obj)

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

        # Apply boolean modifiers
        bpy.context.view_layer.objects.active = stem_cylinder
        bpy.ops.object.modifier_apply(modifier="Boolean_V")
        bpy.ops.object.modifier_apply(modifier="Boolean_H")

        # Delete cross objects
        bpy.data.objects.remove(v_cross, do_unlink=True)
        bpy.data.objects.remove(h_cross, do_unlink=True)


# Operator to generate keycap
class KEYCAP_OT_generate(bpy.types.Operator):
    """Generate a keycap with specified parameters"""

    bl_idname = "keycap.generate"
    bl_label = "Generate Keycap"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        props = context.scene.keycap_props

        KeycapGenerator.create_keycap(
            width=float(props.width),
            profile_row=int(props.profile_row),
            bevel_top_rim=props.bevel_top_rim,
            bevel_vertical=props.bevel_vertical,
            stem_type=props.stem_type,
        )

        self.report({"INFO"}, f"Generated {props.width}U keycap (R{props.profile_row})")
        return {"FINISHED"}


def update_bevels(self, context):
    obj = context.active_object
    if obj is None:
        return

    props = context.scene.keycap_props

    for mod in obj.modifiers:
        if mod.type == "BEVEL":
            if mod.name == "Bevel_Top_Mod":
                mod.width = props.bevel_top_rim
            elif mod.name == "Bevel_Vert_Mod":
                mod.width = props.bevel_vertical


#            elif mod.name == "Bevel_Dish_Mod":
#                mod.width = props.bevel_dish


# Property group for keycap parameters
class KeycapProperties(bpy.types.PropertyGroup):

    width: bpy.props.EnumProperty(
        name="Width",
        description="Keycap width in units",
        items=[
            ("1", "1U", "Standard single unit keycap"),
            ("1.25", "1.25U", "1.25 unit keycap (Tab, Caps Lock)"),
            ("1.5", "1.5U", "1.5 unit keycap (Tab on some layouts)"),
            ("1.75", "1.75U", "1.75 unit keycap (Caps Lock on HHKB)"),
            ("2", "2U", "2 unit keycap (Backspace, Enter)"),
            ("2.25", "2.25U", "2.25 unit keycap (Left Shift, Enter)"),
            ("2.75", "2.75U", "2.75 unit keycap (Right Shift)"),
            ("6", "6U", "6 unit spacebar"),
            ("6.25", "6.25U", "6.25 unit spacebar (most common)"),
            ("7", "7U", "7 unit spacebar"),
        ],
        default="1",
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

    bevel_top_rim: bpy.props.FloatProperty(
        name="Top Rim Bevel",
        description="Bevel radius for top rim edges (mm)",
        default=0.3,
        min=0.0,
        max=2.0,
        step=10,
        update=update_bevels,
    )

    bevel_vertical: bpy.props.FloatProperty(
        name="Vertical Corner Bevel",
        description="Bevel radius for vertical corner edges (mm)",
        default=0.5,
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
        #        layout.label(text="Phase 1 - Core Functionality", icon="MESH_CUBE")

        # Parameters
        box = layout.box()
        box.label(text="Parameters:", icon="PREFERENCES")
        box.prop(props, "width")
        split = box.split(factor=0.4)
        split.label(text="Profile Row: ")
        split.prop(props, "profile_row", text="")

        split = box.split(factor=0.3)
        split.label(text="Stem Type: ")
        split.prop(props, "stem_type", text="")

        # Bevel settings
        bevel_box = layout.box()
        bevel_box.label(text="Bevels:", icon="MOD_BEVEL")
        bevel_box.prop(props, "bevel_top_rim")
        bevel_box.prop(props, "bevel_vertical")

        # Generate button
        layout.separator()
        layout.operator("keycap.generate", text="Generate Keycap", icon="EVENT_F1")


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
