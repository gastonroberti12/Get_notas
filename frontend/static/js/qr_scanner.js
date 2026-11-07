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


async function buscarQr(detector) {
    if (!flujo) return;
    const codigos = await detector.detect(video);
    if (codigos.length > 0) {
        campoCodigo.value = codigos[0].rawValue;
        detenerCamara();
        formulario.submit();
        return;
    }
    requestAnimationFrame(() => buscarQr(detector));
}


async function activarCamara() {
    if (flujo) {
        detenerCamara();
        return;
    }
    if (!('BarcodeDetector' in window) || !navigator.mediaDevices) {
        aviso.textContent = 'Este navegador no puede leer QR. Ingresá el código a mano.';
        return;
    }
    try {
        flujo = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
        video.srcObject = flujo;
        video.hidden = false;
        await video.play();
        botonCamara.textContent = 'Cancelar cámara';
        aviso.textContent = 'Apuntá al código QR.';
        buscarQr(new BarcodeDetector({ formats: ['qr_code'] }));
    } catch (error) {
        detenerCamara();
        aviso.textContent = 'No se pudo usar la cámara. Ingresá el código a mano.';
    }
}