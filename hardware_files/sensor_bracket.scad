// FoldIt Robot - HC-SR04 Ultrasonic Sensor Bracket
// Scale: 1:4 (full-size sensor ~45mm x 20mm, at 1:4 ~11mm x 5mm)
// L-bracket that holds sensor facing down toward belt exit/detection zone
// Mounts to belt_frame rear edge or base plate front edge
//
// PRINT GUIDANCE: Print with the vertical arm flat on bed,
// horizontal arm pointing up. No supports needed.

$fn = 30;

// HC-SR04 sensor at 1:4 scale
sensor_width = 11;         // PCB width
sensor_depth = 5;          // PCB depth (front to back)
sensor_thickness = 1.5;    // PCB thickness
transducer_dia = 4;        // transducer cylinder diameter
transducer_spacing = 6.5;  // center-to-center spacing between transducers
transducer_height = 3;     // transducer protrusion from PCB

// Bracket parameters
wall = 2;
bracket_clearance = 0.3;

// Vertical arm (mounts to frame)
vert_arm_width = sensor_width + wall * 2 + 4;  // extra for mounting holes
vert_arm_height = 25;      // tall enough to position sensor above belt
vert_arm_thickness = wall;

// Horizontal arm (holds sensor)
horiz_arm_width = vert_arm_width;
horiz_arm_length = sensor_depth + wall * 2 + bracket_clearance * 2;
horiz_arm_thickness = wall;

// Sensor pocket depth
pocket_depth = sensor_thickness + 0.5;

// Tilt angle (degrees from horizontal, points sensor toward detection zone)
sensor_tilt = 15;

// Hardware
m2_hole = 2.4;             // M2 clearance for sensor PCB
m3_hole = 3.4;             // M3 clearance for frame mounting
mount_hole_spacing = 15;   // vertical spacing of frame mount holes

module sensor_bracket() {
    difference() {
        union() {
            // Vertical mounting arm
            cube([vert_arm_width, vert_arm_thickness, vert_arm_height]);

            // Horizontal sensor arm (angled)
            translate([0, 0, vert_arm_height])
                rotate([sensor_tilt, 0, 0])
                    _sensor_platform();

            // Corner gusset for rigidity
            _corner_gusset();
        }

        // Frame mounting holes (2 holes in vertical arm)
        _frame_mount_holes();
    }
}

module _sensor_platform() {
    difference() {
        // Platform body
        cube([horiz_arm_width, horiz_arm_length, horiz_arm_thickness]);

        // Sensor pocket (recessed area for PCB to sit in)
        translate([(horiz_arm_width - sensor_width) / 2 - bracket_clearance,
                   wall,
                   -0.5])
            cube([sensor_width + bracket_clearance * 2,
                  sensor_depth + bracket_clearance * 2,
                  pocket_depth + 0.5]);

        // Transducer pass-through holes
        sensor_cx = horiz_arm_width / 2;
        sensor_cy = wall + bracket_clearance + sensor_depth / 2;
        for (dx = [-transducer_spacing / 2, transducer_spacing / 2]) {
            translate([sensor_cx + dx, sensor_cy, -0.5])
                cylinder(d=transducer_dia + 0.5, h=horiz_arm_thickness + 1);
        }

        // M2 mounting holes for sensor PCB (2 holes on sides)
        for (dx = [-(sensor_width / 2 - 1), (sensor_width / 2 - 1)]) {
            translate([sensor_cx + dx, sensor_cy, -0.5])
                cylinder(d=m2_hole, h=horiz_arm_thickness + 1);
        }
    }
}

module _corner_gusset() {
    gusset_size = 8;
    translate([0, 0, vert_arm_height - gusset_size])
        hull() {
            cube([vert_arm_width, vert_arm_thickness, 0.01]);
            translate([0, 0, gusset_size])
                cube([vert_arm_width, 0.01, 0.01]);
            translate([0, gusset_size, gusset_size])
                cube([vert_arm_width, 0.01, 0.01]);
        }
}

module _frame_mount_holes() {
    cx = vert_arm_width / 2;
    z_start = (vert_arm_height - mount_hole_spacing) / 2;

    for (z_off = [0, mount_hole_spacing]) {
        translate([cx, -0.5, z_start + z_off])
            rotate([-90, 0, 0])
                cylinder(d=m3_hole, h=vert_arm_thickness + 1);
    }
}

// Render when opened directly
sensor_bracket();
