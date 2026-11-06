// Menú hamburguesa (pantallas chicas): abre y cierra la barra de navegación
const barra = document.getElementsByClassName('navbar')[0];
const botonMenu = document.getElementsByClassName('nav-toggle')[0];

if (barra && botonMenu) {
  botonMenu.addEventListener('click', () => {
    const abierto = barra.classList.toggle('menu-abierto');
    botonMenu.setAttribute('aria-expanded', abierto ? 'true' : 'false');
    botonMenu.setAttribute('aria-label', abierto ? 'Cerrar menú' : 'Abrir menú');
  });

  // Al pasar a pantalla ancha el menú vuelve a su estado normal
  window.addEventListener('resize', () => {
    if (window.innerWidth > 860) {
      barra.classList.remove('menu-abierto');
      botonMenu.setAttribute('aria-expanded', 'false');
    }
  });
}


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