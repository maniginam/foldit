// FoldIt Robot - Full Assembly Visualization
// All panels shown in home (flat) position
// Use this file to visualize the complete robot
// Scale: 1:4

use <base_plate.scad>
use <left_panel.scad>
use <right_panel.scad>
use <bottom_panel.scad>
use <hinge_bracket.scad>
use <servo_mount.scad>
use <camera_gantry.scad>
use <belt_frame.scad>
use <motor_mount_conv.scad>
use <sensor_bracket.scad>

$fn = 40;

// Base plate dimensions (repeated here for positioning)
base_width = 152.5;
base_length = 190.5;
base_thickness = 5;

// Panel thickness
panel_thickness = 3;

// Hinge bracket dimensions
bracket_width = 20;

// Colors for visualization
base_color = [0.6, 0.6, 0.7, 0.9];
left_color = [0.3, 0.6, 0.9, 0.8];
right_color = [0.3, 0.9, 0.6, 0.8];
bottom_color = [0.9, 0.6, 0.3, 0.8];
bracket_color = [0.4, 0.4, 0.4, 1.0];
servo_color = [0.2, 0.2, 0.2, 1.0];
gantry_color = [0.5, 0.5, 0.5, 1.0];
conveyor_color = [0.3, 0.4, 0.5, 0.9];
motor_color = [0.2, 0.3, 0.2, 1.0];
sensor_color = [0.1, 0.5, 0.4, 1.0];

// Fold angles (0 = flat/home, 180 = fully folded)
left_fold_angle = 0;    // Change to animate folding
right_fold_angle = 0;
bottom_fold_angle = 0;

module assembly() {
    // Base plate - centered at origin for reference
    color(base_color)
        base_plate();

    // Left panel - positioned flush to the left of the base, at base surface height
    color(left_color)
        translate([0, 0, base_thickness])
            rotate([0, left_fold_angle, 0])
                translate([-76, 0, 0])
                    left_panel();

    // Right panel - positioned flush to the right of the base
    color(right_color)
        translate([base_width, 0, base_thickness])
            rotate([0, -right_fold_angle, 0])
                right_panel();

    // Bottom panel - positioned flush to the bottom of the base
    color(bottom_color)
        translate([0, 0, base_thickness])
            rotate([bottom_fold_angle, 0, 0])
                translate([0, -95, 0])
                    bottom_panel();

    // Hinge brackets - left edge (3 brackets)
    // Positioned so horizontal arm holes align with base plate left edge hinge holes
    // Base plate holes at (5, 30+i*60) and (5, 40+i*60)
    color(bracket_color) {
        for (i = [0:2]) {
            y_pos = 30 + i * 60;
            translate([0, y_pos + 15, base_thickness])
                rotate([0, 0, -90])
                    hinge_bracket();
        }
    }

    // Hinge brackets - right edge (3 brackets)
    // Base plate holes at (147.5, 30+i*60) and (147.5, 40+i*60)
    color(bracket_color) {
        for (i = [0:2]) {
            y_pos = 30 + i * 60;
            translate([base_width, y_pos - 5, base_thickness])
                rotate([0, 0, 90])
                    hinge_bracket();
        }
    }

    // Hinge brackets - bottom edge (3 brackets)
    // Base plate holes at (25+i*50, 5) and (35+i*50, 5)
    color(bracket_color) {
        for (i = [0:2]) {
            x_pos = 25 + i * 50;
            translate([x_pos - 5, 0, base_thickness])
                rotate([0, 0, 0])
                    hinge_bracket();
        }
    }

    // Servo mounts (3 total - one per panel)
    color(servo_color) {
        // Left servo mount
        translate([18, base_length / 2 - 25, base_thickness])
            rotate([0, 0, 90])
                servo_mount();

        // Right servo mount
        translate([base_width - 18, base_length / 2 - 25, base_thickness])
            rotate([0, 0, -90])
                servo_mount();

        // Bottom servo mount
        translate([base_width / 2 - 25, 18, base_thickness])
            servo_mount();
    }

    // Camera gantry - positioned behind the folding area
    color(gantry_color)
        translate([(base_width - 160) / 2, base_length - 30, base_thickness])
            camera_gantry();

    // Conveyor belt frame - at front/intake edge, extending outward
    // Frame rear mounting tabs attach to base plate front edge (y=0)
    color(conveyor_color)
        translate([0, -60, 0])
            belt_frame();

    // Conveyor motor mount - on right side wall of belt frame
    color(motor_color)
        translate([base_width - 3, -60 + 60 - 6, 10])
            rotate([0, 0, 90])
                motor_mount_conv();

    // Ultrasonic sensor bracket - at belt exit, facing down toward detection zone
    color(sensor_color)
        translate([base_width / 2 - 9, -3, base_thickness])
            rotate([0, 0, 180])
                sensor_bracket();
}

// Render the full assembly
assembly();
