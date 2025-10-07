# Procedural Keycap Generator

A Blender addon for generating parametric mechanical keyboard keycaps.

![](https://github.com/macsampson/blender_keycap_generator/example.png)

## Installation

1. Download or clone this repository
2. Open Blender (3.0+)
3. Go to `Edit > Preferences > Add-ons`
4. Click `Install...` and select `__init__.py`
5. Enable the addon by checking the box next to "Procedural Keycap Generator"

## Usage

1. Open the **3D Viewport**
2. Press `N` to open the sidebar
3. Navigate to the **Keycap Gen** tab
4. Configure your keycap parameters:
   - **Width**: Keycap size (1U, 1.25U, 1.5U, etc.)
   - **Profile Type**: Cherry, OEM, or SA
   - **Profile Row**: R1-R4 (keyboard row height)
   - **Corner Bevels**: Edge smoothness (0-2mm)
   - **Stem Type**: Cherry MX or None (more to come)
5. Click **Generate Keycap**
6. (Optional) Adjust parameters - the keycap will update in real-time
7. When satisfied, click **Bake Keycap (Apply Mods)** to finalize the geometry
8. Export directly to STL or straight into a 3D printing slicer software of your choice

## Features

- **Multiple profiles**: Cherry, OEM, and SA keycap profiles
- **Row variations**: R1-R4 row heights for ergonomic keyboard layouts
- **Parametric design**: Adjust bevel radius in real-time using modifiers
- **Hollow construction**: 0.91mm wall thickness for realistic keycaps
- **Cherry MX stem**: Automatic cross-pattern stem generation with boolean union
- **One-click baking**: Apply all modifiers to finalize geometry for export
- **Export ready**: Generated keycaps are suitable for 3D printing

## TODO

- Top curve real time modification
- Stem support generation
- Support for multiple styles of stems (not to be confused with above)
