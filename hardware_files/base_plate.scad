// FoldIt Robot - Base Plate
// Scale: 1:4 (full size 24" x 30")
// Dimensions: 152.5mm x 190.5mm x 5mm
//
// PRINT SETTINGS: Print flat on bed. Use slicer elephant's foot
// compensation (-0.2mm initial layer horizontal expansion) for
// accurate bottom-edge dimensions and hole clearances.

$fn = 40;

// Base plate parameters
base_width = 152.5;   // 24" at 1:4 scale
base_length = 190.5;  // 30" at 1:4 scale
base_thickness = 5;

// Mounting hole parameters
m3_hole = 3.4;        // M3 clearance hole
m3_countersink = 6.0; // M3 countersink diameter

// Corner standoff holes - inset from edges
corner_inset = 8;

// Hinge bracket mounting holes
hinge_hole_spacing = 30;  // spacing between hinge bracket pairs
hinge_edge_offset = 5;    // distance from edge to hole center
hinge_pair_gap = 10;      // gap between the two holes in a pair

// Servo mount holes
servo_mount_width = 10;
servo_mount_length = 50;

module base_plate() {
    difference() {
        // Main plate
        cube([base_width, base_length, base_thickness]);

        // Corner standoff holes (4 corners)
        for (x = [corner_inset, base_width - corner_inset])
            for (y = [corner_inset, base_length - corner_inset])
                translate([x, y, -0.5])
                    cylinder(d=m3_hole, h=base_thickness + 1);

        // Left edge hinge bracket holes (3 brackets along left edge)
        for (i = [0:2]) {
            y_pos = 30 + i * hinge_hole_spacing * 2;
            // Two holes per bracket
            for (j = [0:1]) {
                translate([hinge_edge_offset, y_pos + j * hinge_pair_gap, -0.5])
                    cylinder(d=m3_hole, h=base_thickness + 1);
            }
        }

        // Right edge hinge bracket holes (3 brackets along right edge)
        for (i = [0:2]) {
            y_pos = 30 + i * hinge_hole_spacing * 2;
            for (j = [0:1]) {
                translate([base_width - hinge_edge_offset, y_pos + j * hinge_pair_gap, -0.5])
                    cylinder(d=m3_hole, h=base_thickness + 1);
            }
        }

        // Bottom edge hinge bracket holes (3 brackets along bottom edge)
        for (i = [0:2]) {
            x_pos = 25 + i * 50;
            for (j = [0:1]) {
                translate([x_pos + j * hinge_pair_gap, hinge_edge_offset, -0.5])
                    cylinder(d=m3_hole, h=base_thickness + 1);
            }
        }

        // Left servo mount holes (near left edge, centered vertically)
        translate([20, base_length / 2, 0])
            _servo_mount_holes();

        // Right servo mount holes (near right edge, centered vertically)
        translate([base_width - 20, base_length / 2, 0])
            _servo_mount_holes();

        // Bottom servo mount holes (centered horizontally, near bottom edge)
        translate([base_width / 2, 20, 0])
            rotate([0, 0, 90])
                _servo_mount_holes();

        // Camera gantry mounting holes (2 holes on each side, behind folding area)
        for (x = [corner_inset + 5, base_width - corner_inset - 5]) {
            for (y_off = [0, 15]) {
                translate([x, base_length - 15 - y_off, -0.5])
                    cylinder(d=m3_hole, h=base_thickness + 1);
            }
        }
    }
}

module _servo_mount_holes() {
    // 4 holes in a rectangle for servo mount bracket
    for (dx = [-servo_mount_width/2, servo_mount_width/2])
        for (dy = [-servo_mount_length/4, servo_mount_length/4])
            translate([dx, dy, -0.5])
                cylinder(d=m3_hole, h=base_thickness + 1);
}

// Render when opened directly
base_plate();
