// FoldIt Robot - Right Folding Panel
// Scale: 1:4
// Dimensions: 76mm x 190.5mm x 3mm
// Mirror of left panel - folds inward from the right side

$fn = 40;

// Panel parameters
panel_width = 76;       // ~half of base width (152.5 / 2)
panel_length = 190.5;   // full base length
panel_thickness = 3;

// Hinge hole parameters
m3_hole = 3.4;
hinge_hole_spacing = 30;
hinge_edge_offset = 5;       // distance from hinge edge to hole center
hinge_pair_gap = 10;

// Rounded edge radius
edge_radius = 3;

module right_panel() {
    difference() {
        // Main panel body with rounded outer edge (mirrored from left)
        _panel_body();

        // Hinge holes along inner (left) edge - matching base plate right edge
        for (i = [0:2]) {
            y_pos = 30 + i * hinge_hole_spacing * 2;
            for (j = [0:1]) {
                translate([hinge_edge_offset, y_pos + j * hinge_pair_gap, -0.5])
                    cylinder(d=m3_hole, h=panel_thickness + 1);
            }
        }
    }
}

module _panel_body() {
    // Panel with rounded right (outer) edge - mirror of left panel
    hull() {
        // Inner edge - square corners
        translate([0, 0, 0])
            cube([0.5, panel_length, panel_thickness]);

        // Outer edge - rounded
        translate([panel_width - edge_radius, edge_radius, 0])
            cylinder(r=edge_radius, h=panel_thickness);
        translate([panel_width - edge_radius, panel_length - edge_radius, 0])
            cylinder(r=edge_radius, h=panel_thickness);

        // Fill the middle
        translate([0, 0, 0])
            cube([panel_width - edge_radius, panel_length, panel_thickness]);
    }
}

// Render when opened directly
right_panel();
