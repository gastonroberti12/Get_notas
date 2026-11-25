from io import BytesIO

import qrcode


def generar_qr_png(contenido: str) -> bytes:
    """Genera una imagen PNG cuyo contenido es el identificador de la entrada."""
    if not contenido:
        raise ValueError("No se puede generar un QR sin identificador.")

    imagen = qrcode.make(contenido)
    salida = BytesIO() #archivo en memoria, no guarda los datos en el disco si no en una variable
    imagen.save(salida, format="PNG")
    return salida.getvalue()
