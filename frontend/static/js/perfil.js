// Muestra solo el elemento que esta en la posicion indicada y oculta los demas.
// Se usa en las pestañas (Proximas / Historial)
function mostrarSoloElElemento(botones, elementos, posicionAMostrar) {
  for (let posicion = 0; posicion < botones.length; posicion++) {
    const esElElegido = posicion === posicionAMostrar;
    botones[posicion].classList.toggle('activa', esElElegido);
    elementos[posicion].classList.toggle('oculto', !esElElegido);
  }
}


// Activa o desactiva el modo edicion del formulario de datos personales.
function cambiarModoEdicion(formularioPerfil, valoresOriginales, quiereEditar) {
  const campos = formularioPerfil.getElementsByTagName('input');
  const avisoDeError = formularioPerfil.getElementsByClassName('formulario_alerta')[0];

  formularioPerfil.classList.toggle('editando', quiereEditar);
  avisoDeError.classList.add('oculto');

  for (const campo of campos) {
    campo.disabled = !quiereEditar;
    if (!quiereEditar) campo.value = valoresOriginales[campo.name] || '';
  }

  if (quiereEditar) campos[0].focus();
}


// guarda los valores originales del formulario y conecta los botones Editar y Cancelar.
function configurarFormularioPerfil() {
  const formularioPerfil = document.getElementsByClassName('formulario-perfil')[0];
  if (!formularioPerfil) return;

  const botonEditar = formularioPerfil.getElementsByClassName('perfil_editar')[0];
  const botonCancelar = formularioPerfil.getElementsByClassName('perfil_cancelar')[0];

  // Se guardan los valores del servidor para restaurarlos si el usuario cancela
  const valoresOriginales = {};
  for (const campo of formularioPerfil.getElementsByTagName('input')) {
    valoresOriginales[campo.name] = campo.value;
  }

  botonEditar.addEventListener('click', () => {
    cambiarModoEdicion(formularioPerfil, valoresOriginales, true);
  });
  botonCancelar.addEventListener('click', () => {
    cambiarModoEdicion(formularioPerfil, valoresOriginales, false);
  });
}

// cambiar entre pestañas proximas / historial
function configurarPestanas() {
  const botonesDePestana = document.getElementsByClassName('tab');
  const panelesDePestana = document.getElementsByClassName('panel-tab');

  for (let posicion = 0; posicion < botonesDePestana.length; posicion++) {
    botonesDePestana[posicion].addEventListener('click', () => {
      mostrarSoloElElemento(botonesDePestana, panelesDePestana, posicion);
    });
  }

  // Al cargar la pagina se muestra la primera pestaña proximas
  mostrarSoloElElemento(botonesDePestana, panelesDePestana, 0);
}

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

  // Cada boton "Cancelar reserva" abre el modal y conecta el boton de confirmar con el formulario de esa reserva
  for (const botonCancelar of document.getElementsByClassName('reserva_cancelar')) {
    botonCancelar.addEventListener('click', () => {
      botonConfirmar.setAttribute('form', botonCancelar.form.id);
      modal.classList.remove('oculto');
    });
  }

  // cuando el formulario se envia, se bloquean los botones para evitar el doble click
  for (const formularioCancelar of document.getElementsByClassName('form-cancelar-reserva')) {
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


/* main */

configurarFormularioPerfil();
configurarPestanas();
configurarModalCancelar();
