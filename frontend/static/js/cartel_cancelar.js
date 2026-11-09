// Muestra el mensaje de confirmacion, solo si se confirma se envia el formulario de cancelar reserva
function configurarModalCancelar() {
  const modal = document.getElementById('modal-cancelar');
  if (!modal) return;

  const botonVolver = modal.getElementsByClassName('modal_volver')[0];
  const botonConfirmar = modal.getElementsByClassName('modal_confirmar')[0];

  function cerrarModal() {
    if (botonConfirmar.disabled) return;
    modal.classList.add('oculto');
  }

  // Cada boton "Cancelar reserva" abre el cartel
  for (const formularioCancelar of document.getElementsByClassName('form-cancelar-reserva')) {
    // conecta el boton de confirmar con ese formulario de reservas
    const botonCancelar = formularioCancelar.querySelector('button[type="button"]');
    botonCancelar.addEventListener('click', () => {
      botonConfirmar.setAttribute('form', formularioCancelar.id);
      modal.classList.remove('oculto');
    });

    // Cuando el formulario se envia, se bloquean los botones para evitar el doble click
    formularioCancelar.addEventListener('submit', () => {
      botonConfirmar.disabled = true;
      botonVolver.disabled = true;
      botonConfirmar.textContent = 'Cancelando...';
    });
  }

  botonVolver.addEventListener('click', cerrarModal);

  // Click en el fondo oscuro
  modal.addEventListener('click', (evento) => {
    if (evento.target === modal) cerrarModal();
  });
}

configurarModalCancelar();