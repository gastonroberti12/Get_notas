// Lectura del QR con la cámara. No hace peticiones: carga el código en el
// formulario y lo envía como un formulario normal.
const botonCamara = document.getElementById('btn-camara');
const video = document.getElementById('camara');
const aviso = document.getElementById('camara-aviso');
const campoCodigo = document.getElementById('codigo_qr');
const formulario = document.getElementById('form-validar');
let flujo = null;

function detenerCamara() {
    //Apaga cada pista del flujo (aca solo hay una, la del video).
    // Si no se frenan, la camara sigue encendida aunque se oculte el video.
    if (flujo) {
        flujo.getTracks().forEach(pista => pista.stop());
        flujo = null;
    }
    video.hidden = true;
    botonCamara.textContent = 'Escanear con la cámara';
}

//Revisa el video una y otra vez hasta encontrar un QR.
//Cuando lo encuentra carga el codigo en el formulario y lo envia.
async function buscarQr(detector) {
    if (!flujo) return;
    const codigos = await detector.detect(video); //Le pide al detector que mire el cuadro de video.
    if (codigos.length > 0) {
        campoCodigo.value = codigos[0].rawValue;
        detenerCamara();
        formulario.submit();
        return;
    }
    requestAnimationFrame(() => buscarQr(detector));
}


//Prende o apaga la camara cuando se hace click en el boton. Al prenderla empieza a buscar QR.
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
        //Pide permiso para usar la camara trasera del celular.
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


botonCamara.addEventListener('click', activarCamara);