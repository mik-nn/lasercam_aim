/**
 * LaserMark.jsx  — Illustrator Extension for LaserCam Markers
 *
 * Design: Unified Solid Circle + White Direction Line
 *   Both M1 and M2 are identical solid black circles (5mm diameter)
 *   with a white direction line pointing toward the other marker.
 *
 * The white direction line is a thin rectangle drawn from the shape centre
 * toward the other marker.  It prints as a white shape, ensuring a reliable
 * detection feature at camera resolution.
 *
 * Placement:
 *   M1 is placed at the top-right corner of the selection bounding box,
 *   offset 8 mm outward.
 *   M2 is placed at the bottom-left corner of the selection bounding box,
 *   offset 8 mm outward.
 *
 * After placing both markers the artboard is expanded so both markers
 * are fully inside it.
 */

var MM = 2.834645669291339;   // Illustrator points per mm (72 pt / 25.4 mm)
var SHAPE_MM   = 5.0;          // circle diameter (mm)
var LINE_LEN   = 2.0;          // direction line length from center (mm)
var LINE_WIDTH = 0.7;          // direction line width (mm)
var CANVAS_MM  = 16.0;         // bounding canvas for each marker (mm)
var OFFSET_MM  = 8.0;          // placement offset beyond selection corner (mm)

// ── helpers ──────────────────────────────────────────────────────────────────

function blackColor() {
    var c = new CMYKColor();
    c.cyan = 0; c.magenta = 0; c.yellow = 0; c.black = 100;
    return c;
}

function whiteColor() {
    var c = new CMYKColor();
    c.cyan = 0; c.magenta = 0; c.yellow = 0; c.black = 0;
    return c;
}

/**
 * Draw a solid filled black circle marker with a white direction line.
 * cx, cy  : centre of the circle in document points (Y-up Illustrator coords)
 * angle   : direction toward the other marker in Illustrator radians (Y-up,
 *           0 = east, positive = counter-clockwise)
 */
function drawCircleMarker(layer, cx, cy, angle) {
    var r = (SHAPE_MM / 2) * MM;

    // Solid black circle
    var el = layer.pathItems.ellipse(
        cy + r,   // top
        cx - r,   // left
        SHAPE_MM * MM,
        SHAPE_MM * MM
    );
    el.filled = true;
    el.fillColor = blackColor();
    el.stroked = false;

    // White direction line
    drawLineIndicator(layer, cx, cy, angle);
}

/**
 * Draw the white direction line as a solid white filled rectangle.
 * The rectangle starts at the shape centre and extends LINE_LEN mm in
 * the given angle direction, with width LINE_WIDTH mm.
 *
 * Note: Illustrator uses Y-up coordinates, so Math.sin gives the correct
 * vertical component without negation.
 */
function drawLineIndicator(layer, cx, cy, angle) {
    var len = LINE_LEN   * MM;
    var hw  = (LINE_WIDTH / 2) * MM;

    var ca  = Math.cos(angle);
    var sa  = Math.sin(angle);

    // Unit perpendicular vector (left of the direction vector in Y-up space)
    var px  = -sa;
    var py  =  ca;

    // Four corners of the white rectangle (Illustrator [x, y] arrays)
    var p1 = [cx + px * hw,            cy + py * hw           ];  // start-left
    var p2 = [cx + ca * len + px * hw, cy + sa * len + py * hw];  // end-left
    var p3 = [cx + ca * len - px * hw, cy + sa * len - py * hw];  // end-right
    var p4 = [cx - px * hw,            cy - py * hw           ];  // start-right

    var rect = layer.pathItems.add();
    rect.setEntirePath([p1, p2, p3, p4]);
    rect.closed = true;
    rect.filled = true;
    rect.fillColor = whiteColor();
    rect.stroked = false;
}

// ── placement ─────────────────────────────────────────────────────────────────

function run() {
    var doc = app.activeDocument;
    var sel = doc.selection;

    if (!sel || sel.length === 0) {
        alert("Please select artwork before running LaserMark.");
        return;
    }

    // Compute bounding box of the entire selection
    var bounds = sel[0].visibleBounds;  // [left, top, right, bottom]
    for (var i = 1; i < sel.length; i++) {
        var b = sel[i].visibleBounds;
        if (b[0] < bounds[0]) bounds[0] = b[0];  // left
        if (b[1] > bounds[1]) bounds[1] = b[1];  // top
        if (b[2] > bounds[2]) bounds[2] = b[2];  // right
        if (b[3] < bounds[3]) bounds[3] = b[3];  // bottom
    }

    var selLeft   = bounds[0];
    var selTop    = bounds[1];
    var selRight  = bounds[2];
    var selBottom = bounds[3];

    var offset = OFFSET_MM * MM;
    var half   = (SHAPE_MM / 2) * MM;

    // M1 (circle) : top-right corner, offset outward (+x, +y)
    var m1x = selRight  + offset;
    var m1y = selTop    + offset;

    // M2 (circle) : bottom-left corner, offset outward (-x, -y)
    var m2x = selLeft   - offset;
    var m2y = selBottom - offset;

    // Angles in Illustrator radians (Y-up)
    // M1 direction line points TOWARD M2
    var m1angle = Math.atan2(m2y - m1y, m2x - m1x);
    // M2 direction line points TOWARD M1
    var m2angle = Math.atan2(m1y - m2y, m1x - m2x);

    // Create a dedicated layer for the markers
    var markerLayer;
    try {
        markerLayer = doc.layers.getByName("LaserCam Markers");
    } catch (e) {
        markerLayer = doc.layers.add();
        markerLayer.name = "LaserCam Markers";
    }
    markerLayer.locked = false;
    markerLayer.visible = true;

    // Draw M1 and M2 (both are identical circles with direction lines)
    drawCircleMarker(markerLayer, m1x, m1y, m1angle);
    drawCircleMarker(markerLayer, m2x, m2y, m2angle);

    // ── Expand artboard so both markers are fully inside ──────────────────
    var pad = CANVAS_MM * MM;  // use the marker canvas as padding

    var allBounds = [
        Math.min(selLeft,  m1x - pad, m2x - pad),   // new left
        Math.max(selTop,   m1y + pad, m2y + pad),   // new top
        Math.max(selRight, m1x + pad, m2x + pad),   // new right
        Math.min(selBottom, m1y - pad, m2y - pad)   // new bottom
    ];

    var ab = doc.artboards[0];
    ab.artboardRect = allBounds;

    alert(
        "LaserCam markers placed.\n\n" +
        "M1 (solid circle) : top-right, direction toward M2\n" +
        "M2 (solid circle) : bottom-left, direction toward M1\n\n" +
        "Both markers are identical 5mm circles with white direction lines.\n" +
        "Both markers are on layer 'LaserCam Markers'.\n" +
        "Print at 100% scale."
    );
}

run();
