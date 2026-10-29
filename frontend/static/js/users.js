document.addEventListener('DOMContentLoaded', () => {
  const form = document.querySelector('.formulario-login, .formulario-registro');
  if (!form) return;

  // evita enviar dos veces si se hace doble click
  form.addEventListener('submit', () => {
    const btn = form.querySelector('button[type="submit"]');
    btn.disabled = true;
    btn.textContent = 'Enviando...';
  });
});