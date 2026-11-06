// Ventana de daño del sabotaje. Solo lee los endpoints del panel de administrador:
//   GET /api/admin/partidas, GET /api/admin/partidas/{pin}/impacto y GET /api/admin/sabotajes.
// Seguridad: el token se lee del campo en cada petición y nunca se guarda en el navegador
// (ni almacenamiento local, ni de sesión, ni cookies). Los textos se escriben con textContent.
"use strict";

const INTERVALO_MS = 2000;
const SVG = "http://www.w3.org/2000/svg";
const NOTAS_SIN_DANO = new Set(["correcta", "incorrecta"]);

const $ = (id) => document.getElementById(id);
let nombresSabotaje = {};
let consultando = false;

// ---------- utilidades ----------

function formatear(numero) {
  return Math.round(numero).toLocaleString("es-CO");
}

function conSigno(numero) {
  if (numero > 0) return `+${formatear(numero)}`;
  if (numero < 0) return `−${formatear(-numero)}`;
  return "0";
}

function nombreSabotaje(clave) {
  return nombresSabotaje[clave] || clave;
}

function crear(etiqueta, texto, clase) {
  const nodo = document.createElement(etiqueta);
  if (texto !== undefined && texto !== null) nodo.textContent = String(texto);
  if (clase) nodo.className = clase;
  return nodo;
}

function svg(etiqueta, atributos = {}, texto) {
  const nodo = document.createElementNS(SVG, etiqueta);
  for (const [nombre, valor] of Object.entries(atributos)) nodo.setAttribute(nombre, String(valor));
  if (texto !== undefined) nodo.textContent = String(texto);
  return nodo;
}

function conTitulo(nodo, texto) {
  // Tooltip nativo del navegador al pasar el puntero sobre la marca.
  nodo.appendChild(svg("title", {}, texto));
  return nodo;
}

function filaTabla(celdas) {
  const fila = document.createElement("tr");
  for (const [texto, clase] of celdas) fila.appendChild(crear("td", texto, clase));
  return fila;
}

function filaVacia(columnas, texto) {
  const fila = document.createElement("tr");
  const celda = crear("td", texto, "vacio");
  celda.colSpan = columnas;
  fila.appendChild(celda);
  return fila;
}

// ---------- red ----------

async function api(ruta) {
  const token = $("token").value.trim();
  const respuesta = await fetch(ruta, { headers: { "X-Admin-Token": token }, cache: "no-store" });
  const datos = await respuesta.json().catch(() => ({}));
  if (!respuesta.ok) {
    const error = new Error(typeof datos.detail === "string" ? datos.detail : `Error ${respuesta.status}`);
    error.estado = respuesta.status;
    throw error;
  }
  return datos;
}

function mostrarAviso(texto) {
  const aviso = $("aviso");
  aviso.textContent = texto;
  aviso.classList.toggle("oculto", !texto);
}

function marcarVivo(activo, texto) {
  const vivo = $("vivo");
  vivo.textContent = texto;
  vivo.classList.toggle("activo", activo);
}

// ---------- cálculos (sin tocar la lógica del juego: solo resumen lo que manda la API) ----------

function danoPorPregunta(respuestas) {
  const total = respuestas.reduce((max, r) => Math.max(max, r.numero_pregunta), 0);
  const porPregunta = Array.from({ length: total }, (_, i) => ({ numero: i + 1, dano: 0, acumulado: 0 }));
  for (const r of respuestas) porPregunta[r.numero_pregunta - 1].dano += Math.abs(r.diferencia);
  let acumulado = 0;
  for (const p of porPregunta) {
    acumulado += p.dano;
    p.acumulado = acumulado;
  }
  return porPregunta;
}

function esRespuestaAfectada(r) {
  return r.diferencia !== 0 || (Boolean(r.nota) && !NOTAS_SIN_DANO.has(r.nota));
}

// ---------- tiles ----------

function pintarTiles(datos) {
  const preguntas = danoPorPregunta(datos.respuestas);
  const danoTotal = preguntas.length ? preguntas[preguntas.length - 1].acumulado : 0;
  const afectadas = datos.respuestas.filter(esRespuestaAfectada).length;
  $("kpi-dano").textContent = formatear(danoTotal);
  $("kpi-respuestas").textContent = formatear(afectadas);
  $("kpi-respuestas-detalle").textContent = `de ${formatear(datos.respuestas.length)} respuestas`;

  const real = datos.jugadores.find((j) => j.posicion_real === 1);
  const mostrado = datos.jugadores.find((j) => j.posicion_mostrada === 1);
  $("ganador-real").textContent = real ? `${real.jugador} · ${formatear(real.puntos_reales)} pts` : "—";
  $("ganador-mostrado").textContent = mostrado ? `${mostrado.jugador} · ${formatear(mostrado.puntos_mostrados)} pts` : "—";
  const cambio = Boolean(real && mostrado && real.jugador !== mostrado.jugador);
  $("tile-ganador").classList.toggle("cambio", cambio);
  let veredicto = "";
  if (cambio) veredicto = "El sabotaje cambió al ganador";
  else if (real && danoTotal > 0) veredicto = "El ganador no cambió, pero los puntos sí";
  else if (real) veredicto = "Sin daño en el resultado";
  $("ganador-veredicto").textContent = veredicto;

  const chips = $("chips-activos");
  chips.replaceChildren();
  if (!datos.sabotajes_activos.length) chips.appendChild(crear("li", "Ninguno", "ninguno"));
  for (const clave of datos.sabotajes_activos) chips.appendChild(crear("li", nombreSabotaje(clave)));
}

// ---------- gráfica 1: puntos por jugador ----------

function pintarJugadores(jugadores) {
  const contenedor = $("grafica-jugadores");
  contenedor.replaceChildren();
  if (!jugadores.length) {
    contenedor.appendChild(crear("p", "Todavía no hay jugadores en la partida.", "vacio"));
    return;
  }
  const ancho = 640;
  const izquierda = 150;
  const derecha = 130;
  const alto_barra = 20;
  const alto_fila = 2 * alto_barra + 2 + 26;
  const arriba = 8;
  const alto = arriba + jugadores.length * alto_fila;
  const maximo = Math.max(1, ...jugadores.flatMap((j) => [j.puntos_reales, j.puntos_mostrados]));
  const util = ancho - izquierda - derecha;
  const escala = (valor) => (Math.max(0, valor) / maximo) * util;

  const lienzo = svg("svg", { viewBox: `0 0 ${ancho} ${alto}`, role: "img", "aria-label": "Puntos reales y mostrados por jugador" });
  lienzo.appendChild(svg("line", { class: "eje", x1: izquierda, x2: izquierda, y1: 0, y2: alto }));

  jugadores.forEach((j, i) => {
    const y = arriba + i * alto_fila;
    lienzo.appendChild(svg("text", { class: "nombre", x: izquierda - 12, y: y + alto_barra + 6, "text-anchor": "end" }, j.jugador));
    const series = [
      ["barra-real", j.puntos_reales, "Reales"],
      ["barra-mostrado", j.puntos_mostrados, "Mostrados"],
    ];
    series.forEach(([clase, valor, etiqueta], k) => {
      const yb = y + k * (alto_barra + 2);
      const largo = Math.max(escala(valor), valor > 0 ? 4 : 0);
      const barra = svg("rect", { class: clase, x: izquierda, y: yb, width: largo, height: alto_barra, rx: 4 });
      lienzo.appendChild(conTitulo(barra, `${j.jugador} · ${etiqueta}: ${formatear(valor)} pts`));
      lienzo.appendChild(svg("text", { class: "valor", x: izquierda + largo + 8, y: yb + alto_barra - 5 }, formatear(valor)));
    });
    let texto = "sin cambio";
    if (j.diferencia > 0) texto = `${conSigno(j.diferencia)} de más`;
    if (j.diferencia < 0) texto = `${conSigno(j.diferencia)} de menos`;
    lienzo.appendChild(svg("text", { class: "diferencia", x: ancho, y: y + alto_barra + 6, "text-anchor": "end" }, texto));
  });
  contenedor.appendChild(lienzo);
}

// ---------- gráfica 2: daño acumulado por pregunta ----------

function pintarPreguntas(respuestas) {
  const contenedor = $("grafica-preguntas");
  contenedor.replaceChildren();
  const preguntas = danoPorPregunta(respuestas);
  if (!preguntas.length) {
    contenedor.appendChild(crear("p", "Todavía no hay respuestas.", "vacio"));
    return;
  }
  const ancho = 640;
  const alto = 300;
  const margen = { arriba: 28, derecha: 16, abajo: 34, izquierda: 64 };
  const util_x = ancho - margen.izquierda - margen.derecha;
  const util_y = alto - margen.arriba - margen.abajo;
  const maximo = Math.max(1, preguntas[preguntas.length - 1].acumulado);
  const y = (valor) => margen.arriba + util_y - (valor / maximo) * util_y;
  const paso = util_x / preguntas.length;
  const ancho_col = Math.min(56, paso * 0.55);

  const lienzo = svg("svg", { viewBox: `0 0 ${ancho} ${alto}`, role: "img", "aria-label": "Daño por pregunta y acumulado" });
  for (const fraccion of [0, 0.5, 1]) {
    const valor = maximo * fraccion;
    lienzo.appendChild(svg("line", { class: fraccion === 0 ? "eje" : "rejilla", x1: margen.izquierda, x2: ancho - margen.derecha, y1: y(valor), y2: y(valor) }));
    lienzo.appendChild(svg("text", { x: margen.izquierda - 10, y: y(valor) + 5, "text-anchor": "end" }, formatear(valor)));
  }

  const puntos = [];
  preguntas.forEach((p, i) => {
    const centro = margen.izquierda + paso * (i + 0.5);
    if (p.dano > 0) {
      const alto_col = Math.max(y(0) - y(p.dano), 4);
      const columna = svg("rect", { class: "barra-mostrado", x: centro - ancho_col / 2, y: y(0) - alto_col, width: ancho_col, height: alto_col, rx: 4 });
      lienzo.appendChild(conTitulo(columna, `Pregunta ${p.numero}: ${formatear(p.dano)} pts de daño · acumulado ${formatear(p.acumulado)}`));
    }
    lienzo.appendChild(svg("text", { x: centro, y: alto - 10, "text-anchor": "middle" }, `P${p.numero}`));
    puntos.push([centro, y(p.acumulado), p]);
  });

  lienzo.appendChild(svg("polyline", { class: "linea-acumulada", points: puntos.map(([px, py]) => `${px},${py}`).join(" ") }));
  for (const [px, py, p] of puntos) {
    lienzo.appendChild(conTitulo(svg("circle", { class: "punto-acumulado", cx: px, cy: py, r: 5 }), `Acumulado tras la pregunta ${p.numero}: ${formatear(p.acumulado)} pts`));
  }
  const [ux, uy, ultimo] = puntos[puntos.length - 1];
  lienzo.appendChild(svg("text", { class: "valor", x: ux, y: uy - 12, "text-anchor": "middle" }, `${formatear(ultimo.acumulado)} pts`));
  contenedor.appendChild(lienzo);
}

// ---------- tabla de posiciones ----------

function pintarPosiciones(jugadores) {
  const cuerpo = $("tabla-posiciones");
  cuerpo.replaceChildren();
  if (!jugadores.length) {
    cuerpo.appendChild(filaVacia(5, "Sin jugadores."));
    return;
  }
  const ordenados = [...jugadores].sort((a, b) => a.posicion_real - b.posicion_real);
  for (const j of ordenados) {
    const salto = j.posicion_real - j.posicion_mostrada;
    let cambio = "= igual";
    if (salto > 0) cambio = `▲ aparece ${salto} arriba`;
    if (salto < 0) cambio = `▼ aparece ${-salto} abajo`;
    const fila = filaTabla([
      [j.jugador],
      [`${j.posicion_real}.º`, "num"],
      [`${j.posicion_mostrada}.º`, "num"],
      [cambio],
      [conSigno(j.diferencia), "num"],
    ]);
    if (salto !== 0) fila.classList.add("cambio");
    cuerpo.appendChild(fila);
  }
}

// ---------- gráfica 3: daño por sabotaje ----------

function pintarSabotajes(resumen, activos) {
  const contenedor = $("grafica-sabotajes");
  contenedor.replaceChildren();
  const filas = Object.entries(resumen)
    .filter(([clave, datos]) => datos.respuestas_afectadas > 0 || activos.includes(clave))
    .map(([clave, datos]) => ({ clave, ...datos }))
    .sort((a, b) => Math.abs(b.puntos_de_diferencia) - Math.abs(a.puntos_de_diferencia));
  if (!filas.length) {
    contenedor.appendChild(crear("p", "Ningún sabotaje ha afectado la partida.", "vacio"));
    return;
  }
  const ancho = 640;
  const izquierda = 210;
  const derecha = 190;
  const alto_fila = 44;
  const alto = filas.length * alto_fila;
  const maximo = Math.max(1, ...filas.map((f) => Math.abs(f.puntos_de_diferencia)));
  const util = ancho - izquierda - derecha;

  const lienzo = svg("svg", { viewBox: `0 0 ${ancho} ${alto}`, role: "img", "aria-label": "Puntos de diferencia por sabotaje" });
  lienzo.appendChild(svg("line", { class: "eje", x1: izquierda, x2: izquierda, y1: 0, y2: alto }));
  filas.forEach((f, i) => {
    const y = i * alto_fila + 8;
    const largo = f.puntos_de_diferencia === 0 ? 0 : Math.max((Math.abs(f.puntos_de_diferencia) / maximo) * util, 4);
    lienzo.appendChild(svg("text", { class: "nombre", x: izquierda - 12, y: y + 19, "text-anchor": "end" }, nombreSabotaje(f.clave)));
    if (largo > 0) {
      const barra = svg("rect", { class: "barra-sabotaje", x: izquierda, y, width: largo, height: 26, rx: 4 });
      lienzo.appendChild(conTitulo(barra, `${nombreSabotaje(f.clave)}: ${conSigno(f.puntos_de_diferencia)} pts en ${f.respuestas_afectadas} respuestas`));
    }
    const respuestas = f.respuestas_afectadas === 1 ? "1 respuesta" : `${f.respuestas_afectadas} respuestas`;
    lienzo.appendChild(svg("text", { class: "valor", x: izquierda + largo + 8, y: y + 19 }, `${conSigno(f.puntos_de_diferencia)} pts · ${respuestas}`));
  });
  contenedor.appendChild(lienzo);
}

// ---------- tabla de respuestas afectadas ----------

function pintarRespuestas(respuestas) {
  const cuerpo = $("tabla-respuestas");
  cuerpo.replaceChildren();
  const afectadas = respuestas.filter(esRespuestaAfectada).reverse();
  if (!afectadas.length) {
    cuerpo.appendChild(filaVacia(8, "Ninguna respuesta afectada todavía."));
    return;
  }
  for (const r of afectadas) {
    cuerpo.appendChild(
      filaTabla([
        [r.numero_pregunta, "num"],
        [r.jugador],
        [r.correcta ? "Correcta" : "Incorrecta"],
        [formatear(r.puntos_mostrados), "num"],
        [formatear(r.puntos_reales), "num"],
        [conSigno(r.diferencia), "num"],
        [r.sabotajes_activos.map(nombreSabotaje).join(", ") || "—"],
        [r.nota || "—", "nota"],
      ])
    );
  }
}

// ---------- ciclo de actualización ----------

async function cargarCatalogo() {
  if (Object.keys(nombresSabotaje).length) return;
  const datos = await api("/api/admin/sabotajes");
  nombresSabotaje = Object.fromEntries(datos.catalogo.map((s) => [s.clave, s.nombre]));
}

async function cargarPartidas() {
  const partidas = await api("/api/admin/partidas");
  const selector = $("partida");
  const elegida = selector.value;
  selector.replaceChildren();
  const primera = crear("option", partidas.length ? "Elige una partida…" : "No hay partidas activas");
  primera.value = "";
  selector.appendChild(primera);
  for (const p of partidas) {
    const opcion = crear("option", `${p.pin} · ${p.estado} · ${p.jugadores.length} jugadores · pregunta ${p.pregunta_actual}/${p.total_preguntas}`);
    opcion.value = p.pin;
    selector.appendChild(opcion);
  }
  const sigue = partidas.some((p) => p.pin === elegida);
  if (sigue) selector.value = elegida;
  else if (partidas.length === 1) selector.value = partidas[0].pin;
}

async function actualizar() {
  if (consultando || document.hidden || !$("token").value.trim()) return;
  consultando = true;
  try {
    await cargarCatalogo();
    await cargarPartidas();
    const pin = $("partida").value;
    if (pin) {
      const datos = await api(`/api/admin/partidas/${encodeURIComponent(pin)}/impacto`);
      pintarTiles(datos);
      pintarJugadores(datos.jugadores);
      pintarPreguntas(datos.respuestas);
      pintarPosiciones(datos.jugadores);
      pintarSabotajes(datos.resumen_por_sabotaje, datos.sabotajes_activos);
      pintarRespuestas(datos.respuestas);
    }
    mostrarAviso("");
    const hora = new Date().toLocaleTimeString("es-CO");
    marcarVivo(true, pin ? `En vivo · actualizado ${hora}` : "Conectado · elige una partida");
  } catch (error) {
    if (error.estado === 403) {
      nombresSabotaje = {};
      mostrarAviso("Token de administrador incorrecto.");
    } else if (error.estado === 404) {
      mostrarAviso("La partida ya no existe o el panel está desactivado.");
    } else {
      mostrarAviso(`No se pudo actualizar: ${error.message}`);
    }
    marcarVivo(false, "Sin datos");
  } finally {
    consultando = false;
  }
}

function iniciar() {
  $("controles").addEventListener("submit", (evento) => evento.preventDefault());
  $("token").addEventListener("change", () => {
    nombresSabotaje = {};
    void actualizar();
  });
  $("partida").addEventListener("change", () => void actualizar());
  document.addEventListener("visibilitychange", () => void actualizar());
  setInterval(() => void actualizar(), INTERVALO_MS);
  void actualizar();
}

iniciar();
