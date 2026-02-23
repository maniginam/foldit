// FoldIt Robot - Conveyor Belt Frame
// Scale: 1:4 (full-scale conveyor ~240mm / 9.5" long)
// Sits at front/intake edge of the base plate
// Two side walls with roller axle holes, open top for belt
//
// PRINT GUIDANCE: Print upright with side walls vertical.
// Mounting tabs on bed. No supports needed.

$fn = 30;

// Frame dimensions at 1:4 scale
frame_width = 152.5;      // matches base plate width
frame_length = 60;         // conveyor depth (~240mm full / 4)
frame_height = 20;         // raises belt surface to base plate level
wall_thickness = 3;

// Roller parameters
roller_dia = 8;            // roller diameter
axle_dia = 3;              // axle hole diameter (fits M3 rod)
axle_inset = 6;            // axle center distance from front/back edges
axle_z = frame_height / 2; // axle center height

// Mounting tab parameters
tab_width = 12;
tab_length = 10;           // extends beyond frame toward base plate
tab_thickness = 3;
tab_hole_dia = 3.4;        // M3 clearance
tab_count = 3;
tab_spacing = 50;          // spacing between tab centers
tab_x_start = (frame_width - (tab_count - 1) * tab_spacing) / 2;

// Cross brace (bottom, connects side walls)
brace_height = 5;

module belt_frame() {
    difference() {
        union() {
            // Left side wall
            cube([wall_thickness, frame_length, frame_height]);

            // Right side wall
            translate([frame_width - wall_thickness, 0, 0])
                cube([wall_thickness, frame_length, frame_height]);

            // Bottom cross braces (front and rear)
            _cross_brace(y_pos = 0);
            _cross_brace(y_pos = frame_length - wall_thickness);

            // Center cross brace
            _cross_brace(y_pos = (frame_length - wall_thickness) / 2);

            // Mounting tabs along rear edge (attach to base plate front)
            _mounting_tabs();
        }

        // Roller axle holes - left wall
        _axle_holes(x_pos = -0.5, depth = wall_thickness + 1);

        // Roller axle holes - right wall
        _axle_holes(x_pos = frame_width - wall_thickness - 0.5,
                    depth = wall_thickness + 1);
    }
}

module _cross_brace(y_pos) {
    translate([wall_thickness, y_pos, 0])
        cube([frame_width - wall_thickness * 2, wall_thickness, brace_height]);
}

module _axle_holes(x_pos, depth) {
    // Front roller axle
    translate([x_pos, axle_inset, axle_z])
        rotate([0, 90, 0])
            cylinder(d=axle_dia, h=depth);

    // Rear roller axle
    translate([x_pos, frame_length - axle_inset, axle_z])
        rotate([0, 90, 0])
            cylinder(d=axle_dia, h=depth);
}

module _mounting_tabs() {
    for (i = [0 : tab_count - 1]) {
        x_pos = tab_x_start + i * tab_spacing - tab_width / 2;
        difference() {
            // Tab body extending from rear edge
            translate([x_pos, frame_length, 0])
                cube([tab_width, tab_length, tab_thickness]);

            // Mounting hole
            translate([x_pos + tab_width / 2,
                       frame_length + tab_length / 2,
                       -0.5])
                cylinder(d=tab_hole_dia, h=tab_thickness + 1);
        }
    }
}

// Render when opened directly
belt_frame();
