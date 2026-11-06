// Sublista de sucursales: al hacer click en "Cines" se abre o se cierra
const menu = document.getElementsByClassName('nav-dropdown')[0];

if (menu) {
  const boton = document.getElementsByClassName('boton-cines')[0];

  boton.addEventListener('click', () => {
    if (menu.classList.contains('abierto')) {
      menu.classList.remove('abierto');
    } else {
      menu.classList.add('abierto');
    }
  });

  // Un click fuera del menú lo cierra.
  document.addEventListener('click', (evento) => {
    if (!menu.contains(evento.target)) menu.classList.remove('abierto');
  });
}

// Cierra una notificacion en dos pasos: primero la anima y despues la saca de la pagina
function cerrarNotificacion(notificacion) {
  notificacion.classList.add('saliendo');
  setTimeout(() => notificacion.remove(), 300);
}

// Se recorre cada notificacion que haya en la pagina y se cierra con la x o automaticamente a los 5 segundos
for (const notificacion of Array.from(document.getElementsByClassName('notificacion'))) {
  const botonCerrar = notificacion.getElementsByClassName('notificacion_cerrar')[0];
  botonCerrar.addEventListener('click', () => cerrarNotificacion(notificacion));
  setTimeout(() => cerrarNotificacion(notificacion), 5000);
}