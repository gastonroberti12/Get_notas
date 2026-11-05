const form = document.getElementById('form-checkout');
const entradas = Number(document.getElementById('entradas').value);
const precioEntrada = Number(document.getElementById('precio-entrada').value);
const resumenServicios = document.getElementById('resumen-servicios');
const errorBox = document.getElementById('checkout-error');

// Formatea un número como precio: 9500 -> "$ 9.500"
const formatear = (n) => '$ ' + n.toLocaleString('es-AR');


// Resumen y total 
// Recalcula las líneas de servicios, el subtotal de entradas y el total.
function actualizarResumen() {
  const subtotalEntradas = entradas * precioEntrada;
  let total = subtotalEntradas;
  resumenServicios.innerHTML = '';

  for (const fila of document.getElementsByClassName('servicio')) {
    const cantidad = Number(fila.querySelector('.cantidad').value);
    if (cantidad === 0) continue;

    const subtotal = cantidad * Number(fila.querySelector('.precio').value);
    total += subtotal;

    const linea = document.createElement('div');
    linea.className = 'resumen-linea';
    linea.innerHTML = `<span>${fila.querySelector('.nombre').textContent} x${cantidad}</span><span>${formatear(subtotal)}</span>`;
    resumenServicios.appendChild(linea);
  }

  document.getElementById('resumen-entradas-monto').textContent = formatear(subtotalEntradas);
  document.getElementById('resumen-total').textContent = formatear(total);
}


//  Contadores de servicios (− / +)

for (const fila of document.getElementsByClassName('servicio')) {
  const campo = fila.querySelector('.cantidad');

  fila.querySelector('.mas').addEventListener('click', () => {
    campo.value = Number(campo.value) + 1;
    actualizarResumen();
  });

  fila.querySelector('.menos').addEventListener('click', () => {
    campo.value = Math.max(Number(campo.value) - 1, 0);
    actualizarResumen();
  });
}


//  Campos numéricos de la tarjeta 

// Número, mes, año y CVV solo aceptan dígitos
for (const campo of document.getElementsByClassName('solo-numeros')) {
  campo.addEventListener('input', () => {
    campo.value = campo.value.replace(/\D/g, '');
  });
}


// Validación mínima de formato al confirmar

// Solo evita errores obvios de tipeo. El backend valida todo de verdad
form.addEventListener('submit', (e) => {
  const f = form.elements;
  const reglas = [
    [f.titular, f.titular.value.trim().split(/\s+/).length >= 2],
    [f.numero_tarjeta, /^\d{13,19}$/.test(f.numero_tarjeta.value)],
    [f.mes_vencimiento, /^(0[1-9]|1[0-2])$/.test(f.mes_vencimiento.value)],
    [f.anio_vencimiento, /^\d{4}$/.test(f.anio_vencimiento.value)],
    [f.cvv, /^\d{3,4}$/.test(f.cvv.value)],
  ];

  // Marca en rojo los campos inválidos
  let valido = true;
  for (const [campo, ok] of reglas) {
    campo.classList.toggle('invalido', !ok);
    if (!ok) valido = false;
  }

  errorBox.hidden = valido;
  errorBox.textContent = 'Revisá los datos de la tarjeta.';
  if (!valido) e.preventDefault();

});


// Estado inicial
actualizarResumen();
