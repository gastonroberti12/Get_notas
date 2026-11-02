const form = document.getElementsByClassName('formulario-login')[0] || document.getElementsByClassName('formulario-registro')[0] || document.getElementsByClassName('formulario-perfil')[0];

if (form) {
  // evita enviar dos veces si se hace doble click
  form.addEventListener('submit', () => {
    const btn = form.getElementsByClassName('boton')[0];
    btn.disabled = true;
    btn.textContent = 'Enviando...';
  });
}