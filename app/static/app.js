"use strict";

// ---------------------------------------------------------------------------------------------
// Utilidades
// ---------------------------------------------------------------------------------------------
const $ = (id) => document.getElementById(id);

function aviso(texto) {
  const caja = $("aviso");
  caja.textContent = texto;
  caja.classList.remove("oculto");
  clearTimeout(aviso.temporizador);
  aviso.temporizador = setTimeout(() => caja.classList.add("oculto"), 3500);
}

function mostrar(elemento, visible) {
  elemento.classList.toggle("oculto", !visible);
}

async function api(metodo, ruta, cuerpo, cabeceras = {}) {
  const opciones = { method: metodo, headers: { ...cabeceras } };
  if (cuerpo !== undefined) {
    opciones.headers["Content-Type"] = "application/json";
    opciones.body = JSON.stringify(cuerpo);
  }
  const respuesta = await fetch(ruta, opciones);
  const datos = await respuesta.json().catch(() => ({}));
  if (!respuesta.ok) {
    const detalle = Array.isArray(datos.detail) ? datos.detail.map((d) => d.msg).join("; ") : datos.detail;
    throw new Error(detalle || `Error ${respuesta.status}`);
  }
  return datos;
}

function conectarSocket(pin, alRecibir) {
  const protocolo = location.protocol === "https:" ? "wss" : "ws";
  const socket = new WebSocket(`${protocolo}://${location.host}/ws/${pin}`);
  socket.onmessage = (evento) => {
    const mensaje = JSON.parse(evento.data);
    if (mensaje.tipo === "estado") alRecibir(mensaje.datos);
  };
  socket.onclose = (evento) => {
    if (evento.code === 4404) aviso("La partida no existe o ya se cerró.");
  };
  return socket;
}

// Cuenta regresiva local a partir del tiempo_restante que manda el servidor.
function iniciarReloj(elemento, segundos) {
  clearInterval(elemento.intervalo);
  const fin = Date.now() + segundos * 1000;
  const pintar = () => {
    const resto = Math.max(0, (fin - Date.now()) / 1000);
    elemento.textContent = resto.toFixed(1);
    if (resto <= 0) clearInterval(elemento.intervalo);
  };
  pintar();
  elemento.intervalo = setInterval(pintar, 100);
}

function detenerReloj(elemento) {
  clearInterval(elemento.intervalo);
}

// ---------------------------------------------------------------------------------------------
// Pestañas
// ---------------------------------------------------------------------------------------------
document.querySelectorAll(".pestana").forEach((boton) => {
  boton.addEventListener("click", () => {
    document.querySelectorAll(".pestana").forEach((b) => b.classList.toggle("activa", b === boton));
    document.querySelectorAll(".vista").forEach((v) => mostrar(v, v.id === `vista-${boton.dataset.vista}`));
  });
});

// ---------------------------------------------------------------------------------------------
// Profesor
// ---------------------------------------------------------------------------------------------
const profesor = { pin: null, token: null, socket: null };

function pintarProfesor(estado) {
  $("prof-estado").textContent = estado.estado;
  $("prof-total-jugadores").textContent = estado.jugadores.length;
  $("prof-jugadores").innerHTML = "";
  estado.jugadores.forEach((nombre) => {
    const li = document.createElement("li");
    li.textContent = nombre;
    $("prof-jugadores").appendChild(li);
  });

  const hayPregunta = estado.pregunta !== null;
  mostrar($("prof-pregunta"), hayPregunta);
  if (hayPregunta) {
    $("prof-num").textContent = `${estado.numero_pregunta} de ${estado.total_preguntas}`;
    $("prof-texto").textContent = estado.pregunta.texto;
    $("prof-opciones").innerHTML = "";
    estado.pregunta.opciones.forEach((opcion, indice) => {
      const li = document.createElement("li");
      li.textContent = opcion;
      if (estado.correcta === indice) li.classList.add("correcta");
      $("prof-opciones").appendChild(li);
    });
    $("prof-respondieron").textContent = `${estado.respondieron} de ${estado.jugadores.length}`;
    if (estado.estado === "PREGUNTA") iniciarReloj($("prof-reloj"), estado.tiempo_restante);
    else detenerReloj($("prof-reloj"));
  }

  const hayRanking = Array.isArray(estado.ranking);
  mostrar($("prof-ranking"), hayRanking);
  if (hayRanking) {
    $("prof-tabla").innerHTML = "";
    estado.ranking.forEach((fila) => {
      const tr = document.createElement("tr");
      [fila.posicion, fila.nombre, fila.puntos, fila.tiempo_total].forEach((valor) => {
        const td = document.createElement("td");
        td.textContent = valor;
        tr.appendChild(td);
      });
      $("prof-tabla").appendChild(tr);
    });
    $("prof-ganador").textContent = estado.ganador ? `Ganador: ${estado.ganador.nombre} 🏆` : "Resultados";
  }

  $("prof-btn-iniciar").disabled = estado.estado !== "LOBBY";
  $("prof-btn-siguiente").disabled = !["PREGUNTA", "RESULTADOS"].includes(estado.estado);
  $("prof-btn-siguiente").textContent = estado.estado === "PREGUNTA" ? "Cerrar pregunta" : "Siguiente";
}

$("prof-btn-crear").addEventListener("click", async () => {
  try {
    const creada = await api("POST", "/api/partidas", { categoria: $("prof-categoria").value });
    profesor.pin = creada.pin;
    profesor.token = creada.token_host;
    $("prof-pin").textContent = creada.pin;
    mostrar($("prof-crear"), false);
    mostrar($("prof-juego"), true);
    if (profesor.socket) profesor.socket.close();
    profesor.socket = conectarSocket(creada.pin, pintarProfesor);
  } catch (error) {
    aviso(error.message);
  }
});

async function accionProfesor(accion) {
  try {
    await api("POST", `/api/partidas/${profesor.pin}/${accion}`, undefined, { "X-Host-Token": profesor.token });
  } catch (error) {
    aviso(error.message);
  }
}

$("prof-btn-iniciar").addEventListener("click", () => accionProfesor("iniciar"));
$("prof-btn-siguiente").addEventListener("click", () => accionProfesor("siguiente"));
$("prof-btn-nueva").addEventListener("click", () => {
  if (profesor.socket) profesor.socket.close();
  detenerReloj($("prof-reloj"));
  mostrar($("prof-juego"), false);
  mostrar($("prof-crear"), true);
});

// ---------------------------------------------------------------------------------------------
// Jugador
// ---------------------------------------------------------------------------------------------
const jugador = { pin: null, nombre: null, socket: null, respondida: -1 };

async function actualizarMarcador() {
  try {
    const yo = await api("GET", `/api/partidas/${jugador.pin}/jugadores/${encodeURIComponent(jugador.nombre)}`);
    $("jug-puntos").textContent = yo.puntos;
    $("jug-racha").textContent = yo.racha;
    $("jug-posicion").textContent = yo.posicion;
  } catch (error) {
    aviso(error.message);
  }
}

function pintarJugador(estado) {
  $("jug-estado").textContent = estado.estado;
  const enPregunta = estado.estado === "PREGUNTA";
  mostrar($("jug-pregunta"), estado.pregunta !== null && estado.estado !== "FINALIZADA");

  if (estado.estado === "LOBBY") $("jug-mensaje").textContent = `Esperando a que el profesor inicie… (${estado.jugadores.length} jugadores)`;
  if (estado.estado === "FINALIZADA") {
    $("jug-mensaje").textContent = estado.ganador ? `¡Fin! Ganó ${estado.ganador.nombre} 🏆` : "Fin de la partida";
  }

  if (estado.pregunta) {
    $("jug-num").textContent = `${estado.numero_pregunta} de ${estado.total_preguntas}`;
    $("jug-texto").textContent = estado.pregunta.texto;
    const nueva = jugador.respondida !== estado.numero_pregunta;
    $("jug-opciones").innerHTML = "";
    estado.pregunta.opciones.forEach((opcion, indice) => {
      const boton = document.createElement("button");
      boton.textContent = opcion;
      boton.disabled = !enPregunta || !nueva;
      if (estado.correcta === indice) boton.textContent = `✔ ${opcion}`;
      boton.addEventListener("click", () => responder(indice, estado.numero_pregunta));
      $("jug-opciones").appendChild(boton);
    });
    if (enPregunta) {
      iniciarReloj($("jug-reloj"), estado.tiempo_restante);
      if (nueva) $("jug-mensaje").textContent = "¡Responde rápido!";
    } else {
      detenerReloj($("jug-reloj"));
      $("jug-mensaje").textContent = "Resultados de la pregunta";
    }
  }
  if (["RESULTADOS", "FINALIZADA"].includes(estado.estado)) actualizarMarcador();
}

async function responder(opcion, numero) {
  jugador.respondida = numero;
  document.querySelectorAll("#jug-opciones button").forEach((b) => (b.disabled = true));
  try {
    const resultado = await api("POST", `/api/partidas/${jugador.pin}/respuestas`, { nombre: jugador.nombre, opcion });
    // No se dice "¡Correcto!": la correcta se revela en los resultados (y con un sabotaje activo
    // una respuesta incorrecta podría sumar puntos).
    $("jug-mensaje").textContent = `Respuesta enviada: +${resultado.puntos} puntos`;
    $("jug-puntos").textContent = resultado.puntos_totales;
    $("jug-racha").textContent = resultado.racha;
  } catch (error) {
    aviso(error.message);
  }
}

$("jug-btn-unirse").addEventListener("click", async () => {
  const pin = $("jug-pin").value.trim();
  try {
    const unido = await api("POST", `/api/partidas/${pin}/jugadores`, { nombre: $("jug-nombre").value });
    jugador.pin = pin;
    jugador.nombre = unido.nombre;
    jugador.respondida = -1;
    $("jug-yo").textContent = unido.nombre;
    mostrar($("jug-unirse"), false);
    mostrar($("jug-juego"), true);
    if (jugador.socket) jugador.socket.close();
    jugador.socket = conectarSocket(pin, pintarJugador);
  } catch (error) {
    aviso(error.message);
  }
});

// ---------------------------------------------------------------------------------------------
// Saboteador (panel de administrador)
// ---------------------------------------------------------------------------------------------
const cabecerasAdmin = () => ({ "X-Admin-Token": $("adm-token").value });

let ultimoResumenSabotajes = {};
let ultimoCatalogo = null;

function pintarSabotajes(datos, resumenSabotajes = ultimoResumenSabotajes) {
  if (datos) ultimoCatalogo = datos;
  else datos = ultimoCatalogo;
  if (!datos) return;
  if (resumenSabotajes) ultimoResumenSabotajes = resumenSabotajes;

  $("adm-sabotajes").innerHTML = "";
  datos.catalogo.forEach((sabotaje) => {
    const li = document.createElement("li");
    li.classList.toggle("activo", sabotaje.activo);
    const info = document.createElement("div");
    const titulo = document.createElement("strong");
    titulo.textContent = `${sabotaje.nombre} (módulo ${sabotaje.modulo})${sabotaje.activo ? " – ACTIVO" : ""}`;
    const res = ultimoResumenSabotajes[sabotaje.clave];
    if (res && res.respuestas_afectadas > 0) {
      const badge = document.createElement("span");
      badge.className = "resumen-impacto";
      const signo = res.puntos_de_diferencia > 0 ? "+" : "";
      badge.textContent = ` · afectó ${res.respuestas_afectadas} respuesta${res.respuestas_afectadas === 1 ? "" : "s"} · ${signo}${res.puntos_de_diferencia} pts`;
      titulo.appendChild(badge);
    }
    const detalle = document.createElement("dl");
    detalle.className = "detalle-sabotaje";
    [
      ["Qué sabotea", sabotaje.que_sabotea],
      ["Lo correcto", sabotaje.comportamiento_correcto],
      ["Con el sabotaje", sabotaje.comportamiento_saboteado],
      ["Cómo notarlo", sabotaje.como_notarlo],
      ["Prueba que lo detecta", sabotaje.nivel_que_lo_detecta],
    ].forEach(([etiqueta, texto]) => {
      const dt = document.createElement("dt");
      dt.textContent = etiqueta;
      const dd = document.createElement("dd");
      dd.textContent = texto;
      detalle.append(dt, dd);
    });
    info.append(titulo, detalle);
    const boton = document.createElement("button");
    boton.textContent = sabotaje.activo ? "Desactivar" : "Activar";
    boton.className = sabotaje.activo ? "secundario" : "primario";
    boton.addEventListener("click", () => cambiarSabotaje(sabotaje.clave, sabotaje.activo ? "desactivar" : "activar"));
    li.append(info, boton);
    $("adm-sabotajes").appendChild(li);
  });
}

async function cargarSabotajes() {
  try {
    pintarSabotajes(await api("GET", "/api/admin/sabotajes", undefined, cabecerasAdmin()));
  } catch (error) {
    aviso(error.message);
  }
}

async function cambiarSabotaje(clave, accion) {
  try {
    pintarSabotajes(await api("POST", `/api/admin/sabotajes/${clave}/${accion}`, undefined, cabecerasAdmin()));
  } catch (error) {
    aviso(error.message);
  }
}

$("adm-btn-cargar").addEventListener("click", cargarSabotajes);
$("adm-btn-reparar").addEventListener("click", async () => {
  try {
    pintarSabotajes(await api("POST", "/api/admin/sabotajes/reparar", undefined, cabecerasAdmin()));
    aviso("Sabotajes desactivados");
  } catch (error) {
    aviso(error.message);
  }
});

function describirModulo(datos) {
  if (datos.fallidas.length) {
    return `${datos.fallidas.length} de ${datos.total} fallan`;
  }
  if (datos.en_riesgo_por.length) {
    return `depende de ${datos.en_riesgo_por.join(", ")}`;
  }
  return `${datos.total} pruebas OK`;
}

$("adm-btn-pruebas").addEventListener("click", async () => {
  const niveles = [...document.querySelectorAll(".niveles input:checked")].map((c) => c.value);
  const boton = $("adm-btn-pruebas");
  boton.disabled = true;
  $("adm-resumen").textContent = "Ejecutando pruebas… (puede tardar unos segundos)";
  $("adm-tablero").innerHTML = "";
  try {
    const resultado = await api("POST", "/api/admin/pruebas", { niveles }, cabecerasAdmin());
    const resumen = resultado.tablero.resumen;
    $("adm-resumen").textContent =
      `Sabotajes: ${resultado.sabotajes.join(", ") || "ninguno"} · ${resumen.pruebas} pruebas · ` +
      `${resumen.fallidas} fallidas · ${resultado.duracion_s} s`;
    Object.entries(resultado.tablero.modulos).forEach(([modulo, datos]) => {
      const caja = document.createElement("div");
      caja.className = `modulo ${datos.estado}`;
      const nombre = document.createElement("strong");
      nombre.textContent = modulo;
      const estado = document.createElement("small");
      estado.textContent = datos.estado.replace("_", " ");
      const detalle = document.createElement("small");
      detalle.textContent = describirModulo(datos);
      caja.append(nombre, estado, detalle);
      $("adm-tablero").appendChild(caja);
    });
  } catch (error) {
    $("adm-resumen").textContent = "";
    aviso(error.message);
  } finally {
    boton.disabled = false;
  }
});

// ---------------------------------------------------------------------------------------------
// Impacto en la partida
// ---------------------------------------------------------------------------------------------
async function actualizarListaPartidas() {
  const token = $("adm-token").value.trim();
  if (!token) return;
  try {
    const partidas = await api("GET", "/api/admin/partidas", undefined, cabecerasAdmin());
    const select = $("adm-sel-partida");
    const seleccionPrevia = select.value;
    select.innerHTML = '<option value="">Selecciona una partida activa…</option>';
    partidas.forEach((p) => {
      const opt = document.createElement("option");
      opt.value = p.pin;
      opt.textContent = `PIN ${p.pin} – ${p.estado} (${p.jugadores.length} jugadores)`;
      if (p.pin === seleccionPrevia) opt.selected = true;
      select.appendChild(opt);
    });
    if (seleccionPrevia && select.value !== seleccionPrevia) {
      mostrar($("adm-impacto-contenido"), false);
      $("adm-impacto-estado").textContent = "La partida seleccionada ya no está activa.";
    }
  } catch (_e) {
    // Si no está autorizado o falló, no interrumpir el ciclo
  }
}

async function cargarImpacto() {
  const pin = $("adm-sel-partida").value;
  if (!pin) {
    mostrar($("adm-impacto-contenido"), false);
    $("adm-impacto-estado").textContent = "Selecciona una partida activa para ver el impacto.";
    return;
  }
  try {
    const impacto = await api("GET", `/api/admin/partidas/${pin}/impacto`, undefined, cabecerasAdmin());
    mostrar($("adm-impacto-contenido"), true);
    $("adm-impacto-estado").textContent = `Monitoreando PIN ${pin} · Sabotajes activos: ${impacto.sabotajes_activos.join(", ") || "ninguno"}`;

    if (impacto.resumen_por_sabotaje && ultimoCatalogo) {
      pintarSabotajes(ultimoCatalogo, impacto.resumen_por_sabotaje);
    }

    const tbody = $("adm-tabla-impacto").querySelector("tbody");
    tbody.innerHTML = "";
    if (impacto.jugadores.length === 0) {
      const tr = document.createElement("tr");
      const td = document.createElement("td");
      td.colSpan = 6;
      td.textContent = "Aún no hay jugadores en esta partida.";
      tr.appendChild(td);
      tbody.appendChild(tr);
    } else {
      impacto.jugadores.forEach((item) => {
        const tr = document.createElement("tr");

        const tdJugador = document.createElement("td");
        tdJugador.textContent = item.jugador;

        const tdMostrados = document.createElement("td");
        tdMostrados.textContent = item.puntos_mostrados;

        const tdReales = document.createElement("td");
        tdReales.textContent = item.puntos_reales;

        const tdDif = document.createElement("td");
        if (item.diferencia < 0) {
          tdDif.className = "dif-negativa";
          tdDif.textContent = `${item.diferencia}`;
        } else if (item.diferencia > 0) {
          tdDif.className = "dif-positiva";
          tdDif.textContent = `+${item.diferencia}`;
        } else {
          tdDif.textContent = "0";
        }

        const tdPos = document.createElement("td");
        if (item.posicion_mostrada !== item.posicion_real) {
          tdPos.className = "pos-cambiada";
          tdPos.textContent = `${item.posicion_mostrada} → ${item.posicion_real}`;
        } else {
          tdPos.textContent = `${item.posicion_mostrada}`;
        }

        const tdRacha = document.createElement("td");
        tdRacha.textContent = `${item.racha_mostrada} / ${item.racha_real}`;

        tr.append(tdJugador, tdMostrados, tdReales, tdDif, tdPos, tdRacha);
        tbody.appendChild(tr);
      });
    }

    const listaResp = $("adm-lista-respuestas");
    listaResp.innerHTML = "";
    const afectadas = impacto.respuestas.filter(
      (r) => r.diferencia !== 0 || (r.nota && !r.nota.startsWith("correcta") && !r.nota.startsWith("incorrecta"))
    );
    if (afectadas.length === 0) {
      const li = document.createElement("li");
      li.textContent = "Sin respuestas afectadas por sabotajes hasta el momento.";
      listaResp.appendChild(li);
    } else {
      afectadas
        .slice(-10)
        .reverse()
        .forEach((r) => {
          const li = document.createElement("li");
          li.className = r.diferencia < 0 ? "negativa" : "positiva";
          const difTxt = r.diferencia > 0 ? `+${r.diferencia}` : `${r.diferencia}`;
          li.textContent = `Pregunta ${r.numero_pregunta} · ${r.jugador} (${difTxt} pts) · ${r.nota}`;
          listaResp.appendChild(li);
        });
    }
  } catch (error) {
    $("adm-impacto-estado").textContent = error.message;
  }
}

async function cicloMonitoreoImpacto() {
  await actualizarListaPartidas();
  if ($("adm-sel-partida").value) {
    await cargarImpacto();
  }
}

$("adm-sel-partida").addEventListener("change", cargarImpacto);
$("adm-btn-refrescar-impacto").addEventListener("click", cicloMonitoreoImpacto);

setInterval(cicloMonitoreoImpacto, 2000);
