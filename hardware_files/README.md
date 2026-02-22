# FoldIt Robot - 3D Printable Hardware Files

## Overview

1:4 scale prototype of the FoldIt clothes-folding robot. All dimensions are in millimeters. The full-size robot base is 24" x 30"; these files produce a 152.5mm x 190.5mm tabletop prototype.

## Parts List

| File | Part | Qty | Notes |
|------|------|-----|-------|
| `base_plate.scad` | Base plate | 1 | Main platform |
| `left_panel.scad` | Left folding panel | 1 | Hinges on left edge |
| `right_panel.scad` | Right folding panel | 1 | Hinges on right edge |
| `bottom_panel.scad` | Bottom folding panel | 1 | Hinges on bottom edge |
| `hinge_bracket.scad` | L-shaped hinge bracket | 9 | 3 per panel edge (left, right, bottom) |
| `servo_mount.scad` | MG996R servo mount | 3 | One per folding panel |
| `camera_gantry.scad` | Camera gantry | 1 | Overhead Pi Camera v2 mount |

**Total printed parts: 17**

## Recommended Print Settings

| Setting | Value |
|---------|-------|
| Material | PLA (PETG for higher durability) |
| Layer height | 0.2mm |
| Infill | 20% (30% for servo mounts and hinge brackets) |
| Walls/perimeters | 3 |
| Top/bottom layers | 4 |
| Supports | Required for camera gantry only |
| Bed adhesion | Brim recommended for panels |
| Nozzle | 0.4mm |

### Per-Part Notes

- **Base plate**: Print flat. No supports needed.
- **Left/Right/Bottom panels**: Print flat. No supports needed. Use brim if edges curl.
- **Hinge brackets**: Print with the L-shape standing upright (vertical arm pointing up). No supports needed.
- **Servo mounts**: Print upright (open end facing up). No supports needed.
- **Camera gantry**: Print in the orientation shown (feet on bed). Supports required for the crossbar overhang and camera mount plate.

## Hardware Required

| Item | Spec | Qty | Purpose |
|------|------|-----|---------|
| M3 x 8mm socket head cap screws | M3 | 36 | Hinge brackets to base/panels |
| M3 x 10mm socket head cap screws | M3 | 12 | Servo mounts to base plate |
| M3 x 12mm socket head cap screws | M3 | 12 | Servo tab screws |
| M3 nuts | M3 | 60 | All M3 screw connections |
| M2 x 6mm screws | M2 | 4 | Pi Camera v2 mounting |
| M2 nuts | M2 | 4 | Pi Camera v2 mounting |
| M3 x 6mm screws | M3 | 4 | Corner standoffs |
| Steel rod / pins, 3mm dia x 25mm | 3mm | 9 | Hinge pins |
| MG996R servo motors | - | 3 | Panel actuation |
| Raspberry Pi Camera v2 | - | 1 | Vision system |
| Rubber feet / standoffs | - | 4 | Base plate feet |

## Assembly Order

### Step 1: Prepare hinge brackets
1. Insert 3mm hinge pins through the pin holes in each hinge bracket
2. Verify pins rotate freely

### Step 2: Attach hinge brackets to base plate
1. Attach 3 hinge brackets along the left edge of the base plate using M3 x 8mm screws and nuts
2. Attach 3 hinge brackets along the right edge
3. Attach 3 hinge brackets along the bottom edge
4. Ensure all brackets are oriented with the vertical arm pointing upward and outward

### Step 3: Attach folding panels
1. Connect the left panel to the left-edge hinge brackets using M3 x 8mm screws
2. Connect the right panel to the right-edge hinge brackets
3. Connect the bottom panel to the bottom-edge hinge brackets
4. Verify all panels fold smoothly through 180 degrees

### Step 4: Install servo mounts
1. Mount the left servo bracket to the base plate near the left edge using M3 x 10mm screws
2. Mount the right servo bracket near the right edge
3. Mount the bottom servo bracket near the bottom edge
4. Insert MG996R servos into each mount bracket, securing with M3 x 12mm screws through the tab holes

### Step 5: Connect servos to panels
1. Attach servo horns to the servo shafts
2. Connect each horn to its respective panel using linkage arms (custom cut or printed)
3. Verify each servo can drive its panel through the full fold range

### Step 6: Install camera gantry
1. Position the gantry behind the folding area, aligning foot holes with the base plate gantry holes
2. Secure with M3 x 8mm screws and nuts
3. Mount the Pi Camera v2 to the camera mount plate using M2 screws and nuts
4. Ensure the camera lens points straight down through the center hole

### Step 7: Install feet
1. Attach rubber feet or standoffs to the four corner holes of the base plate

## Assembly Visualization

Open `assembly.scad` in OpenSCAD to see the complete robot with all parts positioned. You can modify the fold angle variables at the top of the file to visualize folding:

```
left_fold_angle = 0;    // 0 = flat, 180 = fully folded
right_fold_angle = 0;
bottom_fold_angle = 0;
```

## File Dependencies

All `.scad` files are self-contained and can be rendered independently. The `assembly.scad` file uses `use` statements to import all other files for the combined visualization.

## Scaling

These files are at 1:4 scale. To produce full-size parts, apply a `scale([4, 4, 4])` transform in OpenSCAD, or scale by 400% in your slicer. Note that full-size parts will likely exceed most consumer printer bed sizes and will need to be printed in sections.
