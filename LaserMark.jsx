// MarkerDiagonal_Final.jsx
// Метки 8 мм: квадрат (правый верхний) и круг (левый нижний)
// Метки располагаются СНАРУЖИ общего bounding box выделения
// Стрелки указывают друг на друга, треугольники вынесены
// Метки всегда внутри артборда (минимальное расширение)
// Всё рисуется spot-цветом

(function () {

    if (app.documents.length === 0) return;
    var doc = app.activeDocument;

    if (!doc.selection || doc.selection.length === 0) {
        alert("Выдели объекты.");
        return;
    }

    // --- Константы ---
    var MM = 2.834645;
    var markerSize = 8 * MM;
    var shapeSize  = 4 * MM;
    var arrowLen   = 3 * MM;
    var arrowThick = 0.6 * MM;
    var arrowHead  = 1.2 * MM;
    var outsideGap = 2 * MM; // расстояние от объекта наружу
    var tipOffset  = 0.8 * MM; // вынос треугольника

    // --- Общий bounding box выделения ---
    var sel = doc.selection;
    var L = sel[0].geometricBounds[0];
    var T = sel[0].geometricBounds[1];
    var R = sel[0].geometricBounds[2];
    var B = sel[0].geometricBounds[3];

    for (var i = 1; i < sel.length; i++) {
        var gb = sel[i].geometricBounds;
        if (gb[0] < L) L = gb[0];
        if (gb[1] > T) T = gb[1];
        if (gb[2] > R) R = gb[2];
        if (gb[3] < B) B = gb[3];
    }

    // --- Слой Markers ---
    var layerName = "Markers";
    var markersLayer = null;

    for (var i = 0; i < doc.layers.length; i++) {
        if (doc.layers[i].name === layerName) {
            markersLayer = doc.layers[i];
            break;
        }
    }
    if (!markersLayer) {
        markersLayer = doc.layers.add();
        markersLayer.name = layerName;
    }

    // --- SPOT-цвет ---
    function getSpotColor() {
        var spotName = "MarkerSpot";
        var spot = null;

        for (var i = 0; i < doc.spots.length; i++) {
            if (doc.spots[i].name === spotName) {
                spot = doc.spots[i];
                break;
            }
        }

        if (!spot) {
            spot = doc.spots.add();
            spot.name = spotName;

            var c = new CMYKColor();
            c.cyan = 0;
            c.magenta = 0;
            c.yellow = 0;
            c.black = 100;

            spot.color = c;
        }

        var sc = new SpotColor();
        sc.spot = spot;
        sc.tint = 100;
        return sc;
    }

    var spotColor = getSpotColor();

    // --- Стрелка ---
    function drawArrow(layer, cx, cy, tx, ty) {

        var angle = Math.atan2(ty - cy, tx - cx);

        // Линия стрелки
        var x1 = cx;
        var y1 = cy;

        var x2 = cx + arrowLen * Math.cos(angle);
        var y2 = cy + arrowLen * Math.sin(angle);

        var line = layer.pathItems.add();
        line.stroked = true;
        line.strokeWidth = arrowThick;
        line.strokeColor = spotColor;
        line.filled = false;
        line.setEntirePath([[x1, y1], [x2, y2]]);

        // Вынесенный треугольник
        var hx = x2 + tipOffset * Math.cos(angle);
        var hy = y2 + tipOffset * Math.sin(angle);

        var leftAngle  = angle + Math.PI * 0.75;
        var rightAngle = angle - Math.PI * 0.75;

        var lx = hx + arrowHead * Math.cos(leftAngle);
        var ly = hy + arrowHead * Math.sin(leftAngle);

        var rx = hx + arrowHead * Math.cos(rightAngle);
        var ry = hy + arrowHead * Math.sin(rightAngle);

        var head = layer.pathItems.add();
        head.stroked = false;
        head.filled = true;
        head.fillColor = spotColor;
        head.setEntirePath([[hx, hy], [lx, ly], [rx, ry]]);
    }

    // --- Квадрат ---
    function drawSquare(cx, cy) {
        var leftPos = cx - shapeSize / 2;
        var topPos  = cy + shapeSize / 2;

        var sq = markersLayer.pathItems.rectangle(
            topPos,
            leftPos,
            shapeSize,
            shapeSize
        );
        sq.stroked = true;
        sq.strokeWidth = 0.25 * MM;
        sq.strokeColor = spotColor;
        sq.filled = false;
    }

    // --- Круг ---
    function drawCircle(cx, cy) {
        var leftPos = cx - shapeSize / 2;
        var topPos  = cy + shapeSize / 2;

        var circle = markersLayer.pathItems.ellipse(
            topPos,
            leftPos,
            shapeSize,
            shapeSize
        );
        circle.stroked = true;
        circle.strokeWidth = 0.25 * MM;
        circle.strokeColor = spotColor;
        circle.filled = false;
    }

    // --- Центры меток (снаружи bounding box) ---
    var sqX = R + outsideGap;
    var sqY = T - outsideGap;

    var crX = L - outsideGap;
    var crY = B + outsideGap;

    // --- Артборд ---
    var ab = doc.artboards[doc.artboards.getActiveArtboardIndex()];

    function ensureInsideArtboard(x, y) {
        var rect = ab.artboardRect;
        var abL = rect[0];
        var abT = rect[1];
        var abR = rect[2];
        var abB = rect[3];

        var half = markerSize / 2;

        var needL = x - half;
        var needT = y + half;
        var needR = x + half;
        var needB = y - half;

        if (needL < abL) abL = needL;
        if (needT > abT) abT = needT;
        if (needR > abR) abR = needR;
        if (needB < abB) abB = needB;

        ab.artboardRect = [abL, abT, abR, abB];
    }

    ensureInsideArtboard(sqX, sqY);
    ensureInsideArtboard(crX, crY);

    // --- Рисуем метки ---
    drawSquare(sqX, sqY);
    drawCircle(crX, crY);

    // --- Стрелки указывают друг на друга ---
    drawArrow(markersLayer, sqX, sqY, crX, crY);
    drawArrow(markersLayer, crX, crY, sqX, sqY);

})();