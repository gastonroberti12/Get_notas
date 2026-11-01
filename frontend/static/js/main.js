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