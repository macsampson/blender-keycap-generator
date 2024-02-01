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
        for name in ["Bevel_Vert_Mod", "Bevel_Dish_Mod"]:
            if obj.modifiers.get(name):
                continue  # don't recreate if already exists

        vert_mod = obj.modifiers.new("Bevel_Vert_Mod", "BEVEL")
        vert_mod.limit_method = "WEIGHT"
        vert_mod.segments = 8
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
        profile_type="CHERRY",
        profile_row=3,
        bevel_vertical=1.5,
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
        inner_vertical_edges = []

        # Cherry profile measurements (in mm, converted to Blender units)
        base_width = width * 18.0  # 1U = 18mm
        base_height = 18.0
        wall_thickness = 0.91  # Wall thickness in mm

        # Profile-specific dimensions
        if profile_type == "CHERRY":
            top_width = base_width - 5.5
            #            top_height = 11.2
            front_taper = 3.4  # mm pulled in on top face compared to base
            row_heights = {1: 11.5, 2: 9.5, 3: 8.5, 4: 9.5}

        elif profile_type == "OEM":
            top_width = base_width - 3.0
            #            top_height = base_height - 3.0
            front_taper = 3.0
            row_heights = {1: 12.5, 2: 11.0, 3: 9.5, 4: 10.5}

        elif profile_type == "SA":
            top_width = base_width - 2.5
            #            top_height = base_height - 2.5
            front_taper = 2.5
            row_heights = {1: 14.89, 2: 13.49, 3: 12.925, 4: 13.49}

        keycap_height = row_heights.get(profile_row, row_heights[3])

        # Outer shell vertices
        # Create base vertices (bottom outer)
        base_outer = [
            bm.verts.new((-base_width / 2, -base_height / 2, 0)),
            bm.verts.new((base_width / 2, -base_height / 2, 0)),
            bm.verts.new((base_width / 2, base_height / 2, 0)),
            bm.verts.new((-base_width / 2, base_height / 2, 0)),
        ]

        back_y = base_height / 2
        front_y = (base_height / 2) - front_taper

        # Create top vertices (outer)
        top_outer = [
            bm.verts.new((-top_width / 2, -back_y, keycap_height)),
            bm.verts.new((top_width / 2, -back_y, keycap_height)),
            bm.verts.new((top_width / 2, front_y, keycap_height)),
            bm.verts.new((-top_width / 2, front_y, keycap_height)),
        ]

        # Inner shell vertices (offset by wall thickness)
        # Calculate inner dimensions
        base_inner_width = base_width - (wall_thickness * 2)
        base_inner_height = base_height - (wall_thickness * 2)
        top_inner_width = top_width - (wall_thickness * 2)
        #        top_inner_height = top_height - (wall_thickness * 2)
        front_inner_taper = front_taper
        inner_top_z = keycap_height - wall_thickness

        # Create base inner vertices (just above bottom)
        base_inner = [
            bm.verts.new((-base_inner_width / 2, -base_inner_height / 2, 0)),
            bm.verts.new((base_inner_width / 2, -base_inner_height / 2, 0)),
            bm.verts.new((base_inner_width / 2, base_inner_height / 2, 0)),
            bm.verts.new((-base_inner_width / 2, base_inner_height / 2, 0)),
        ]

        back_inner_y = base_inner_height / 2
        front_inner_y = (base_inner_height / 2) - front_inner_taper

        # Create top inner vertices
        top_inner = [
            bm.verts.new((-top_inner_width / 2, -back_inner_y, inner_top_z)),
            bm.verts.new((top_inner_width / 2, -back_inner_y, inner_top_z)),
            bm.verts.new((top_inner_width / 2, front_inner_y, inner_top_z)),
            bm.verts.new((-top_inner_width / 2, front_inner_y, inner_top_z)),
        ]

        # Create faces - Outer shell
        # Top face (outer)
        top_face = bm.faces.new(top_outer)

        # Outer side faces
        for i in range(4):
            next_i = (i + 1) % 4
            face = bm.faces.new(
                [base_outer[i], base_outer[next_i], top_outer[next_i], top_outer[i]]
            )

        # Track only the 4 corner edges (not all vertical edges)
        bevel_weight_layer = bm.edges.layers.float.get("bevel_weight_edge")
        if bevel_weight_layer is None:
            bevel_weight_layer = bm.edges.layers.float.new("bevel_weight_edge")

        corner_edges = []

        for i in range(4):
            # Each corner has exactly one vertical edge connecting base_outer[i] to top_outer[i]
            for edge in base_outer[i].link_edges:
                v1, v2 = edge.verts
                if (v1 == base_outer[i] and v2 == top_outer[i]) or (
                    v2 == base_outer[i] and v1 == top_outer[i]
                ):
                    edge.select = True
                    corner_edges.append(edge)
                    edge[bevel_weight_layer] = 1.0
                    break

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
                # Check if edge connects bottom to top (different z values)
                if abs(v1.co.z - v2.co.z) > 0.001:
                    if edge not in inner_vertical_edges:
                        inner_vertical_edges.append(edge)
                        edge.select = True

        # Connect bottom edges (rim where outer meets inner)
        for i in range(4):
            next_i = (i + 1) % 4
            # Bottom rim face
            bm.faces.new(
                [base_outer[i], base_inner[i], base_inner[next_i], base_outer[next_i]]
            )

        # bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.normal_update()

        # Track top rim edges
        top_faces = [
            f
            for f in bm.faces
            if abs(sum(v.co.z for v in f.verts) / len(f.verts) - keycap_height) < 0.001
            and abs(f.normal.z) > 0.9
        ]

        rim_edges = []

        if top_faces:
            top_face = top_faces[0]
            # any edge of the top face that is shared with a non-horizontal face -> rim
            for e in top_face.edges:
                for lf in e.link_faces:
                    if lf is top_face:
                        continue
                    if abs(lf.normal.z) < 0.99:  # linked face isn't horizontal
                        rim_edges.append(e)
                        e[bevel_weight_layer] = 0.5
                        break

        # Create deform layer for vertex groups
        deform_layer = bm.verts.layers.deform.verify()

        # Write bmesh to mesh
        bm.to_mesh(mesh)
        bm.free()

        KeycapGenerator.add_bevel_modifiers(obj)

        # Add stem using boolean modifier (after mesh is created)
        if stem_type == "CHERRY_MX":
            KeycapGenerator._add_cherry_stem(obj, keycap_height)

        # Add smooth shading (need object mode)
        # bpy.ops.object.mode_set(mode="OBJECT")
        # bpy.ops.object.shade_smooth()

        return obj

    @staticmethod
    def _add_cherry_stem(keycap_obj, keycap_height):
        """Add Cherry MX stem cylinder with cross cutout to the bottom of keycap using boolean modifier"""
        # Cherry MX stem dimensions (in mm)
        stem_outer_radius = 5.6 / 2  # Outer cylinder diameter ~5.5mm
        stem_height = keycap_height - 0.5  # Height of stem extending down
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

        # Add boolean union modifier to keycap
        union_mod = keycap_obj.modifiers.new(name="Boolean_Stem_Union", type="BOOLEAN")
        union_mod.operation = "UNION"
        union_mod.object = stem_cylinder
        union_mod.solver = "FAST"

        # Apply the union modifier to merge stem into keycap
        bpy.context.view_layer.objects.active = keycap_obj
        bpy.ops.object.modifier_apply(modifier="Boolean_Stem_Union")

        # Delete the stem object now that it's merged
        bpy.data.objects.remove(stem_cylinder, do_unlink=True)

        keycap_obj.select_set(True)
        bpy.context.view_layer.objects.active = keycap_obj

        # # Add an edge split modifier
        # edge_split_mod = keycap_obj.modifiers.new(
        #     name="Edge_Split_Mod", type="EDGE_SPLIT"
        # )
        # edge_split_mod.split_angle = radians(30.0)

        # # Apply edge split
        # bpy.ops.object.modifier_apply(modifier="Edge_Split_Mod")


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
            profile_type=props.profile_type,
            profile_row=int(props.profile_row),
            bevel_vertical=props.bevel_vertical,
            stem_type=props.stem_type,
        )

        self.report({"INFO"}, f"Generated {props.width}U keycap (R{props.profile_row})")
        return {"FINISHED"}


def update_keycap(self, context):
    # Find existing keycap
    keycap = bpy.data.objects.get("Keycap")
    if keycap:
        # Store other properties
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
    obj = context.active_object
    if obj is None:
        return

    props = context.scene.keycap_props

    for mod in obj.modifiers:
        if mod.type == "BEVEL":
            if mod.name == "Bevel_Vert_Mod":
                mod.width = props.bevel_vertical


# Property group for keycap parameters
class KeycapProperties(bpy.types.PropertyGroup):

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
            #            ("TOPRE", "Topre", "Topre compatible stem (WIP)"),
        ],
        default="CHERRY_MX",
        update=update_keycap,
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
        # bevel_box.prop(props, "bevel_top_rim")
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
