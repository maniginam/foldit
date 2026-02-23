// FoldIt Robot - Conveyor Motor Mount (N20 DC Gear Motor)
// Scale: 1:4
// Cradle bracket for N20 micro gear motor, mounts to belt_frame side wall
// Motor shaft aligns with rear roller axle
//
// PRINT GUIDANCE: Print flat with base plate on bed. No supports needed.

$fn = 30;

// N20 motor dimensions at 1:4 scale
motor_body_w = 12;         // motor body width
motor_body_h = 10;         // motor body height
motor_body_l = 16;         // motor body length (including gearbox)
motor_shaft_dia = 3;       // output shaft diameter
motor_shaft_offset_z = 5;  // shaft center height from motor bottom

// Bracket parameters
wall = 2;
clearance = 0.3;           // clearance around motor body
bracket_inner_w = motor_body_w + clearance * 2;
bracket_inner_h = motor_body_h + clearance * 2;
bracket_outer_w = bracket_inner_w + wall * 2;
bracket_outer_h = bracket_inner_h + wall * 2;
bracket_length = motor_body_l + wall;

// Mounting flange (attaches to belt_frame side wall)
flange_width = bracket_outer_w + 8;
flange_height = bracket_outer_h + 8;
flange_thickness = 3;

// Hardware
m2_hole = 2.4;             // M2 clearance hole
m2_spacing_w = bracket_outer_w + 4;
m2_spacing_h = bracket_outer_h + 4;

module motor_mount_conv() {
    difference() {
        union() {
            // Mounting flange
            translate([-(flange_width - bracket_outer_w) / 2,
                       0,
                       -(flange_height - bracket_outer_h) / 2])
                cube([flange_width, flange_thickness, flange_height]);

            // Motor cradle (U-shaped, open top for motor insertion)
            translate([0, flange_thickness, 0])
                _motor_cradle();
        }

        // Motor cavity
        translate([wall, flange_thickness, wall])
            cube([bracket_inner_w, motor_body_l + 1, bracket_inner_h]);

        // Open top for motor insertion
        translate([wall, flange_thickness, wall + bracket_inner_h - 1])
            cube([bracket_inner_w, motor_body_l + 1, wall + 2]);

        // Shaft pass-through hole in flange
        translate([bracket_outer_w / 2,
                   -0.5,
                   wall + clearance + motor_shaft_offset_z])
            rotate([-90, 0, 0])
                cylinder(d=motor_shaft_dia + 1, h=flange_thickness + 1);

        // M2 mounting holes in flange (4 corners)
        _flange_holes();
    }
}

module _motor_cradle() {
    // Bottom wall
    cube([bracket_outer_w, bracket_length, wall]);

    // Left wall
    cube([wall, bracket_length, bracket_outer_h]);

    // Right wall
    translate([wall + bracket_inner_w, 0, 0])
        cube([wall, bracket_length, bracket_outer_h]);

    // Back wall (motor stop)
    translate([0, bracket_length - wall, 0])
        cube([bracket_outer_w, wall, bracket_outer_h]);
}

module _flange_holes() {
    cx = bracket_outer_w / 2;
    cz = bracket_outer_h / 2;

    positions = [
        [cx - m2_spacing_w / 2, cz - m2_spacing_h / 2],
        [cx + m2_spacing_w / 2, cz - m2_spacing_h / 2],
        [cx - m2_spacing_w / 2, cz + m2_spacing_h / 2],
        [cx + m2_spacing_w / 2, cz + m2_spacing_h / 2]
    ];

    for (pos = positions) {
        translate([pos[0], -0.5, pos[1]])
            rotate([-90, 0, 0])
                cylinder(d=m2_hole, h=flange_thickness + 1);
    }
}

// Render when opened directly
motor_mount_conv();
