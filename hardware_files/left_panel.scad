// FoldIt Robot - Left Folding Panel
// Scale: 1:4
// Dimensions: 76mm x 190.5mm x 3mm
// Folds inward (flips 180 degrees) to fold left side of clothing

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

module left_panel() {
    difference() {
        // Main panel body with rounded outer edge
        _panel_body();

        // Hinge holes along inner (right) edge - matching base plate left edge
        for (i = [0:2]) {
            y_pos = 30 + i * hinge_hole_spacing * 2;
            for (j = [0:1]) {
                translate([panel_width - hinge_edge_offset, y_pos + j * hinge_pair_gap, -0.5])
                    cylinder(d=m3_hole, h=panel_thickness + 1);
            }
        }
    }
}

module _panel_body() {
    // Panel with rounded left (outer) edge
    hull() {
        // Inner edge - square corners
        translate([panel_width - 0.5, 0, 0])
            cube([0.5, panel_length, panel_thickness]);

        // Outer edge - rounded
        translate([edge_radius, edge_radius, 0])
            cylinder(r=edge_radius, h=panel_thickness);
        translate([edge_radius, panel_length - edge_radius, 0])
            cylinder(r=edge_radius, h=panel_thickness);

        // Fill the middle
        translate([edge_radius, 0, 0])
            cube([panel_width - edge_radius, panel_length, panel_thickness]);
    }
}

// Render when opened directly
left_panel();
