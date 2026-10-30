from datetime import datetime, timedelta, timezone

import jwt
from werkzeug.security import check_password_hash, generate_password_hash

from constants import JWT_EXPIRACION_MINUTOS, JWT_SECRET_KEY
from cine_fuente.utils import construir_error_api

ALGORITMO = "HS256"


def hashear_contrasenia(contrasenia: str) -> str:
    """Devuelve el hash a guardar en usuarios.contrasena (usar al registrar)."""
    return generate_password_hash(contrasenia)


def verificar_contrasenia(hash_guardado: str, contrasenia: str) -> bool:
    """Compara la contraseña ingresada con el hash guardado en la base."""
    return check_password_hash(hash_guardado, contrasenia)


def generar_token(usuario_id: int, rol: str) -> str:
    """Firma un JWT con id, rol y vencimiento. No se guarda en ningún lado."""
    ahora = datetime.now(timezone.utc)
    claims = {
        "sub": str(usuario_id),
        "rol": rol,
        "iat": ahora,
        "exp": ahora + timedelta(minutes=JWT_EXPIRACION_MINUTOS),
    }
    return jwt.encode(claims, JWT_SECRET_KEY, algorithm=ALGORITMO)


def decodificar_token(token: str) -> dict:
    """Verifica la firma y el vencimiento. Devuelve los claims o levanta ValueError (401)."""
    try:
        claims = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[ALGORITMO],
            options={"require": ["sub", "rol", "exp"]},
        )
        int(claims["sub"])
        return claims
    except jwt.ExpiredSignatureError:
        raise ValueError(construir_error_api(
            "TOKEN_EXPIRADO", "Token expirado", "La sesión venció. Iniciá sesión nuevamente."
        ), 401)
    except (jwt.InvalidTokenError, ValueError):
        raise ValueError(construir_error_api(
            "TOKEN_INVALIDO", "Token inválido", "El token no es válido."
        ), 401)