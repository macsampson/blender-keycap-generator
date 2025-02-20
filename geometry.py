"""
Keycap geometry generation
"""

import bpy
import bmesh
from mathutils import Vector
from math import radians
import math


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
        vert_mod.profile = 0.64
        vert_mod.width = bpy.context.scene.keycap_props.bevel_vertical

    @staticmethod
    def create_keycap(
        width=1.0,
        profile_type="CHERRY",
        profile_row=3,
        bevel_vertical=1.5,
        stem_type="CHERRY_MX",
    ):

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
            front_taper = 3.4  # mm pulled in on top face compared to base
            row_heights = {1: 11.5, 2: 9.5, 3: 8.5, 4: 9.5}

        elif profile_type == "OEM":
            top_width = base_width - 3.0
            front_taper = 3.0
            row_heights = {1: 12.5, 2: 11.0, 3: 9.5, 4: 10.5}

        elif profile_type == "SA":
            top_width = base_width - 2.5
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

        return obj

    @staticmethod
    def _add_cherry_stem(keycap_obj, keycap_height):

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
