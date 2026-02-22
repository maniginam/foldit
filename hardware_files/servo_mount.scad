// FoldIt Robot - Servo Mount Bracket for MG996R
// MG996R dimensions: 40.7mm x 19.7mm x 42.9mm
// Mounting tab holes: 49.5mm apart (center to center), 4.8mm holes
// Shaft offset: 10mm from one end
// This bracket holds the servo so its horn connects to the folding panel

$fn = 40;

// MG996R servo dimensions
servo_body_w = 19.7;      // width
servo_body_l = 40.7;      // length
servo_body_h = 42.9;      // height (including gear box)
servo_tab_l = 54.5;       // total length including mounting tabs
servo_tab_w = 19.7;       // tab width (same as body)
servo_tab_h = 2.5;        // tab thickness
servo_tab_offset = 27.0;  // distance from bottom to tab underside
servo_hole_spacing = 49.5; // distance between mounting holes
servo_hole_d = 4.8;       // mounting hole diameter
servo_shaft_offset = 10;  // shaft center offset from one end

// Bracket parameters
wall = 3;
bracket_clearance = 0.5;  // clearance around servo body
bracket_inner_w = servo_body_w + bracket_clearance * 2;
bracket_inner_l = servo_body_l + bracket_clearance * 2;
bracket_outer_w = bracket_inner_w + wall * 2;
bracket_outer_l = bracket_inner_l + wall * 2;
bracket_h = servo_tab_offset + servo_tab_h + 2; // height up to tabs + a bit

// Base plate mounting
base_plate_w = bracket_outer_w + 16;  // extra width for mounting flanges
base_plate_l = bracket_outer_l + 10;
base_plate_h = wall;

// Horn clearance
horn_slot_w = 8;
horn_slot_l = 30;

m3_hole = 3.4;

module servo_mount() {
    difference() {
        union() {
            // Base mounting plate
            translate([-(base_plate_w - bracket_outer_w) / 2,
                       -(base_plate_l - bracket_outer_l) / 2, 0])
                cube([base_plate_w, base_plate_l, base_plate_h]);

            // Servo cradle walls
            _servo_cradle();
        }

        // Servo body cavity
        translate([wall, wall, base_plate_h])
            cube([bracket_inner_w, bracket_inner_l, bracket_h]);

        // Tab slots on both sides (so servo drops in from top, tabs rest on cradle)
        _tab_slots();

        // Horn clearance slot on top (for servo horn to protrude)
        translate([bracket_outer_w / 2 - horn_slot_w / 2,
                   wall + bracket_clearance + servo_body_l - servo_shaft_offset - horn_slot_w / 2,
                   -0.5])
            cylinder(d=horn_slot_w + 4, h=base_plate_h + 1);

        // Shaft hole through base plate (so horn can reach below)
        translate([bracket_outer_w / 2,
                   wall + bracket_clearance + servo_body_l - servo_shaft_offset,
                   -0.5])
            cylinder(d=12, h=base_plate_h + 1);

        // Base plate mounting holes (4 corners of the flange)
        _base_mounting_holes();

        // Servo mounting screw holes (through cradle walls into servo tabs)
        _servo_screw_holes();
    }
}

module _servo_cradle() {
    // Four walls forming the cradle
    cradle_total_h = base_plate_h + bracket_h;

    // Left wall
    cube([wall, bracket_outer_l, cradle_total_h]);

    // Right wall
    translate([wall + bracket_inner_w, 0, 0])
        cube([wall, bracket_outer_l, cradle_total_h]);

    // Front wall
    cube([bracket_outer_w, wall, cradle_total_h]);

    // Back wall
    translate([0, wall + bracket_inner_l, 0])
        cube([bracket_outer_w, wall, cradle_total_h]);
}

module _tab_slots() {
    // Horizontal slots for the servo mounting tabs to rest in
    tab_slot_h = servo_tab_h + 1;
    tab_extend = 10;  // how far tabs extend beyond servo body

    // Left and right tab slots
    for (side = [0, 1]) {
        x_pos = side == 0 ? -0.5 : bracket_outer_w - wall + 0.5;
        translate([x_pos,
                   wall + bracket_clearance - tab_extend / 2,
                   base_plate_h + servo_tab_offset])
            cube([wall + 1, bracket_inner_l + tab_extend, tab_slot_h]);
    }
}

module _base_mounting_holes() {
    flange_x = (base_plate_w - bracket_outer_w) / 2;
    flange_y = (base_plate_l - bracket_outer_l) / 2;

    // 4 holes in the mounting flanges
    positions = [
        [-flange_x / 2, -flange_y / 2],
        [bracket_outer_w + flange_x / 2, -flange_y / 2],
        [-flange_x / 2, bracket_outer_l + flange_y / 2],
        [bracket_outer_w + flange_x / 2, bracket_outer_l + flange_y / 2]
    ];

    for (pos = positions) {
        translate([pos[0], pos[1], -0.5])
            cylinder(d=m3_hole, h=base_plate_h + 1);
    }
}

module _servo_screw_holes() {
    // Holes through the cradle walls that align with servo tab holes
    screw_z = base_plate_h + servo_tab_offset + servo_tab_h / 2;
    hole_y1 = wall + bracket_clearance + (servo_body_l - servo_hole_spacing) / 2;
    hole_y2 = hole_y1 + servo_hole_spacing;

    // Through left wall
    for (y = [hole_y1, hole_y2]) {
        translate([-0.5, y, screw_z])
            rotate([0, 90, 0])
                cylinder(d=m3_hole, h=wall + 1);
    }

    // Through right wall
    for (y = [hole_y1, hole_y2]) {
        translate([wall + bracket_inner_w - 0.5, y, screw_z])
            rotate([0, 90, 0])
                cylinder(d=m3_hole, h=wall + 1);
    }
}

// Render when opened directly
servo_mount();
