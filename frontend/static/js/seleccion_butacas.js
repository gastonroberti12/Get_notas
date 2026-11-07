const lista = document.getElementById('seleccion-lista');
const vacia = document.getElementById('seleccion-vacia');
const cantidad = document.getElementById('seleccion-cantidad');
const monto = document.getElementById('seleccion-monto');
const boton = document.getElementById('btn-continuar');
const campo = document.getElementById('butacas-input');
const PRECIO = Number(document.getElementById('precio').value);
const avisos = document.getElementById('avisos-butacas');

// Formatea un número como precio: 9500 -> "$ 9.500"
const formatear = (n) => '$ ' + n.toLocaleString('es-AR');

function mostrarAvisoLimite() {
  const notificacion = document.createElement('div');
  notificacion.className = 'notificacion notificacion-error';
  notificacion.innerHTML = `
    <span class="notificacion_icono">!</span>
    <p class="notificacion_texto">Solo puedes seleccionar 5 butacas por reserva.</p>
    <button type="button" class="notificacion_cerrar" aria-label="Cerrar aviso">×</button>
    <span class="notificacion_barra"></span>`;

  avisos.appendChild(notificacion);

  const cerrar = () => {
    if (notificacion.classList.contains('saliendo')) return;
    notificacion.classList.add('saliendo');
    setTimeout(() => notificacion.remove(), 300);
  };

  notificacion.querySelector('.notificacion_cerrar').addEventListener('click', cerrar);
  setTimeout(cerrar, 5000);
}


// Resumen de la selección 
// Reconstruye la lista, el total, el campo oculto y el estado del botón según las butacas elegidas.
function actualizar() {
  const elegidas = Array.from(document.getElementsByClassName('seleccionada')).sort((a, b) => a.id.localeCompare(b.id, 'es', { numeric: true }));
  let total = 0;

  lista.innerHTML = '';
  elegidas.forEach((b) => {
    total += PRECIO;
    const item = document.createElement('li');
    item.innerHTML = `<span>Butaca <b>${b.id}</b></span><span>${formatear(PRECIO)}</span>`;
    lista.appendChild(item);
  });

  vacia.hidden = elegidas.length > 0;
  cantidad.textContent = `${elegidas.length} entrada(s)`;
  monto.textContent = formatear(total);
  campo.value = elegidas.map((b) => b.dataset.butacaId).join(',');
  boton.disabled = elegidas.length === 0;
}


// Click en una butaca 
for (const butaca of document.getElementsByClassName('butaca')) {
  butaca.addEventListener('click', () => {
    if (butaca.classList.contains('ocupada')) return;
    if (!butaca.classList.contains('seleccionada') &&
        document.getElementsByClassName('seleccionada').length >= 5) {
      mostrarAvisoLimite();
      return;
    }

    butaca.classList.toggle('seleccionada');
    actualizar();
  });
}


// Estado inicial (sin butacas elegidas)
actualizar();
