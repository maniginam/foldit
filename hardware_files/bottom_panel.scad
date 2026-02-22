// FoldIt Robot - Bottom Folding Panel
// Scale: 1:4
// Dimensions: 152.5mm x 95mm x 3mm
// Folds upward from the bottom edge to fold the bottom of clothing

$fn = 40;

// Panel parameters
panel_width = 152.5;    // full base width
panel_length = 95;      // ~half of base length (190.5 / 2)
panel_thickness = 3;

// Hinge hole parameters
m3_hole = 3.4;
hinge_pair_gap = 10;

// Rounded edge radius
edge_radius = 3;

module bottom_panel() {
    difference() {
        // Main panel body with rounded bottom edge
        _panel_body();

        // Hinge holes along top (inner) edge - matching base plate bottom edge
        for (i = [0:2]) {
            x_pos = 25 + i * 50;
            for (j = [0:1]) {
                translate([x_pos + j * hinge_pair_gap, panel_length - 5, -0.5])
                    cylinder(d=m3_hole, h=panel_thickness + 1);
            }
        }
    }
}

module _panel_body() {
    // Panel with rounded bottom (outer) edge
    hull() {
        // Top (inner) edge - square corners
        translate([0, panel_length - 0.5, 0])
            cube([panel_width, 0.5, panel_thickness]);

        // Bottom edge - rounded corners
        translate([edge_radius, edge_radius, 0])
            cylinder(r=edge_radius, h=panel_thickness);
        translate([panel_width - edge_radius, edge_radius, 0])
            cylinder(r=edge_radius, h=panel_thickness);

        // Fill the middle
        translate([0, edge_radius, 0])
            cube([panel_width, panel_length - edge_radius, panel_thickness]);
    }
}

// Render when opened directly
bottom_panel();
