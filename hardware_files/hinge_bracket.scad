// FoldIt Robot - L-Shaped Hinge Bracket
// Connects folding panels to the base plate via hinge pins
// Dimensions: 20mm x 15mm x 15mm, 3mm wall thickness
// Two M3 holes on each arm, 3mm hinge pin hole

$fn = 40;

// Bracket parameters
bracket_width = 20;      // width (along hinge axis)
bracket_arm_h = 15;      // height of vertical arm
bracket_arm_l = 15;      // length of horizontal arm
wall = 3;                // wall thickness

// Hole parameters
m3_hole = 3.4;           // M3 clearance
pin_hole = 3.2;          // hinge pin diameter (3mm pin + clearance)
hole_inset = 5;          // inset from edges for mounting holes
mount_hole_y = 5;        // Y offset for horizontal arm holes (matches base plate hinge_edge_offset)

module hinge_bracket() {
    difference() {
        // L-shaped body
        union() {
            // Horizontal arm (mounts to base plate)
            cube([bracket_width, bracket_arm_l, wall]);

            // Vertical arm (mounts to panel and holds hinge pin)
            cube([bracket_width, wall, bracket_arm_h]);

            // Fillet/reinforcement at the L junction
            translate([0, 0, 0])
                _corner_fillet();
        }

        // Horizontal arm mounting holes (2 holes for M3 screws into base)
        // Y offset matches base plate hinge_edge_offset for proper alignment
        for (x = [hole_inset, bracket_width - hole_inset]) {
            translate([x, mount_hole_y, -0.5])
                cylinder(d=m3_hole, h=wall + 1);
        }

        // Vertical arm mounting holes (2 holes for M3 screws into panel)
        for (x = [hole_inset, bracket_width - hole_inset]) {
            translate([x, -0.5, bracket_arm_h * 0.6])
                rotate([-90, 0, 0])
                    cylinder(d=m3_hole, h=wall + 1);
        }

        // Hinge pin hole through the top of the vertical arm
        translate([-0.5, wall / 2, bracket_arm_h - 4])
            rotate([0, 90, 0])
                cylinder(d=pin_hole, h=bracket_width + 1);
    }
}

module _corner_fillet() {
    // Triangular reinforcement wedge at the L-joint
    fillet_size = 5;

    // Wedge connecting horizontal and vertical arms
    translate([0, wall, wall])
        hull() {
            // Thin strip along vertical arm
            cube([bracket_width, 0.01, fillet_size]);
            // Thin strip along horizontal arm
            cube([bracket_width, fillet_size, 0.01]);
        }
}

// Render when opened directly
hinge_bracket();
