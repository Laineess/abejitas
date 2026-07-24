// Check del vuelo de las abejas:  node test_vuelo.js
// Saca mezclarAngulo del propio display.html para que no se desincronice.
const assert = require("assert");
const fs = require("fs");

const html = fs.readFileSync("templates/display.html", "utf8");
const src = html.match(/function mezclarAngulo[\s\S]*?\n  }/);
assert.ok(src, "no se encontró mezclarAngulo en templates/display.html");
const mezclarAngulo = new Function(src[0] + "; return mezclarAngulo;")();

const TAU = Math.PI * 2;
const norm = a => ((a % TAU) + TAU) % TAU;

// k=0 no mueve, k=1 llega exacto
assert.strictEqual(mezclarAngulo(1.3, 2.7, 0), 1.3);
assert.ok(Math.abs(norm(mezclarAngulo(1.3, 2.7, 1)) - 2.7) < 1e-9);

// Lo que importa: cruzar la costura 0/2π por el camino CORTO.
// De 349° a 11° son 22° hacia adelante, no 338° hacia atrás.
const a = (349 / 180) * Math.PI, b = (11 / 180) * Math.PI;
const paso = mezclarAngulo(a, b, 0.5);
assert.ok(paso > a, `debía avanzar cruzando 0°, dio ${paso} desde ${a}`);
assert.ok(Math.abs(norm(paso) - norm(a + (22 / 180) * Math.PI * 0.5)) < 1e-9);

// Y al revés: de 11° a 349° son 22° hacia atrás
assert.ok(mezclarAngulo(b, a, 0.5) < b);

// La abeja siempre acaba llegando: la velocidad frena con la distancia
// pero nunca baja de 1.1, así que entra al umbral de 6px.
let dist = 1400, giros = 0;
while (dist >= 6) {
  dist -= Math.max(1.1, Math.min(4, dist * 0.06));
  assert.ok(++giros < 5000, "la abeja nunca llegó a su destino");
}

console.log("ok — vuelo:", giros, "frames para cruzar 1400px");
