// FoldIt Robot - Camera Gantry
// Overhead mount for Pi Camera v2
// Two vertical posts with horizontal crossbar and camera mount plate
// Scale: 1:4 (posts ~50mm tall representing ~200mm full scale)
//
// PRINT GUIDANCE: This model renders as one piece for visualization but
// should be printed as separate components and assembled:
//   1. Two post-with-foot pieces (print upright, foot on bed)
//   2. Crossbar (print flat)
//   3. Camera mount plate (print flat)
// The 140mm crossbar span at 50mm height cannot bridge without supports.
// Glue or friction-fit joints at post-to-crossbar interfaces.

$fn = 40;

// Gantry parameters
post_height = 50;         // vertical post height (200mm full / 4)
post_width = 10;          // square post cross-section
post_depth = 10;
crossbar_length = 140;    // span between posts (slightly less than base width)
crossbar_width = 10;
crossbar_height = 10;

// Base foot parameters
foot_length = 30;         // depth of the base foot
foot_width = 20;          // width of the base foot
foot_height = 5;          // thickness of the base foot
foot_spacing = 15;        // hole spacing on foot (matches base plate gantry holes)

// Pi Camera v2 mount plate
cam_plate_w = 25;         // camera board width
cam_plate_l = 24;         // camera board length
cam_plate_h = 2;          // mount plate thickness
cam_hole_spacing_w = 21;  // horizontal hole spacing on Pi Cam v2
cam_hole_spacing_l = 12.5; // vertical hole spacing on Pi Cam v2
cam_hole_d = 2.2;         // M2 holes for Pi Camera

// Hardware
m3_hole = 3.4;

module camera_gantry() {
    // Left post with foot
    translate([0, 0, 0])
        _post_with_foot();

    // Right post with foot
    translate([crossbar_length + post_width, 0, 0])
        _post_with_foot();

    // Horizontal crossbar connecting the two posts at the top
    translate([post_width, (post_depth - crossbar_width) / 2, post_height + foot_height])
        _crossbar();

    // Camera mount plate at center of crossbar
    translate([(crossbar_length + post_width * 2) / 2,
               post_depth / 2,
               post_height + foot_height + crossbar_height])
        _camera_mount();
}

module _post_with_foot() {
    // Base foot
    difference() {
        translate([-(foot_width - post_width) / 2, -(foot_length - post_depth) / 2, 0])
            cube([foot_width, foot_length, foot_height]);

        // Mounting holes in foot (2 holes matching base plate)
        for (y_off = [0, foot_spacing]) {
            translate([post_width / 2,
                       post_depth / 2 - foot_spacing / 2 + y_off,
                       -0.5])
                cylinder(d=m3_hole, h=foot_height + 1);
        }
    }

    // Vertical post
    translate([0, 0, foot_height])
        cube([post_width, post_depth, post_height]);

    // Triangular gussets for rigidity (front and back)
    for (side = [0, 1]) {
        y_pos = side == 0 ? 0 : post_depth;
        mirror_y = side == 0 ? 0 : 1;
        translate([0, 0, foot_height])
            _gusset(side);
    }
}

module _gusset(side) {
    gusset_h = 15;
    gusset_l = 15;
    gusset_w = post_width;

    if (side == 0) {
        // Front gusset
        translate([0, -gusset_l + post_depth / 2, 0])
            hull() {
                cube([gusset_w, 0.01, gusset_h]);
                cube([gusset_w, gusset_l, 0.01]);
            }
    } else {
        // Back gusset
        translate([0, post_depth / 2, 0])
            hull() {
                cube([gusset_w, 0.01, gusset_h]);
                cube([gusset_w, gusset_l, 0.01]);
            }
    }
}

module _crossbar() {
    difference() {
        cube([crossbar_length, crossbar_width, crossbar_height]);

        // Weight reduction slots (optional, for less material)
        slot_count = 3;
        slot_width = (crossbar_length - 20) / (slot_count * 2);
        for (i = [0:slot_count - 1]) {
            translate([15 + i * slot_width * 2, 2, -0.5])
                cube([slot_width, crossbar_width - 4, crossbar_height + 1]);
        }
    }
}

module _camera_mount() {
    // Small platform for Pi Camera v2
    difference() {
        // Mount plate centered at origin
        translate([-cam_plate_w / 2, -cam_plate_l / 2, 0])
            cube([cam_plate_w, cam_plate_l, cam_plate_h]);

        // Pi Camera v2 mounting holes (M2, 4 holes)
        for (x = [-cam_hole_spacing_w / 2, cam_hole_spacing_w / 2])
            for (y = [-cam_hole_spacing_l / 2, cam_hole_spacing_l / 2])
                translate([x, y, -0.5])
                    cylinder(d=cam_hole_d, h=cam_plate_h + 1);

        // Center hole for camera lens
        translate([0, 0, -0.5])
            cylinder(d=8, h=cam_plate_h + 1);
    }
}

// Render when opened directly
camera_gantry();
