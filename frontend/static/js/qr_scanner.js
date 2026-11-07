// Lectura del QR con la cámara. No hace peticiones: carga el código en el
// formulario y lo envía como un formulario normal.
const botonCamara = document.getElementById('btn-camara');
const video = document.getElementById('camara');
const aviso = document.getElementById('camara-aviso');
const campoCodigo = document.getElementById('codigo_qr');
const formulario = document.getElementById('form-validar');
let flujo = null;

function detenerCamara() {
    if (flujo) {
        flujo.getTracks().forEach(pista => pista.stop());
        flujo = null;
    }
    video.hidden = true;
    botonCamara.textContent = 'Escanear con la cámara';
}