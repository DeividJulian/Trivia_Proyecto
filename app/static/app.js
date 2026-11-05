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

function pintarSabotajes(datos) {
  $("adm-sabotajes").innerHTML = "";
  datos.catalogo.forEach((sabotaje) => {
    const li = document.createElement("li");
    li.classList.toggle("activo", sabotaje.activo);
    const info = document.createElement("div");
    const titulo = document.createElement("strong");
    titulo.textContent = `${sabotaje.nombre} (módulo ${sabotaje.modulo})${sabotaje.activo ? " – ACTIVO" : ""}`;
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
