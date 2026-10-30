from datetime import datetime, timedelta, timezone
import jwt
from werkzeug.security import check_password_hash, generate_password_hash
from constants import JWT_EXPIRACION_MINUTOS, JWT_SECRET_KEY
from cine_fuente.utils import construir_error_api
from flask import g, request


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


def requiere_login(funcion):
    """Exige un token válido y deja el usuario autenticado en g.usuario ({'id', 'rol'})."""
    def envoltura(*args, **kwargs):
        partes = request.headers.get("Authorization", "").split(None, 1)
        if len(partes) != 2 or partes[0].lower() != "bearer" or not partes[1].strip():
            raise ValueError(construir_error_api(
                "TOKEN_REQUERIDO",
                "Autenticación requerida",
                "Envíe un token válido mediante Authorization: Bearer <token>.",
            ), 401)
        claims = decodificar_token(partes[1].strip())
        g.usuario = {"id": int(claims["sub"]), "rol": claims["rol"]}
        return funcion(*args, **kwargs)
    envoltura.__name__ = funcion.__name__
    return envoltura


def requiere_rol(*roles_permitidos):
    """Exige login y que el rol del usuario esté entre los permitidos (403 si no)."""
    def decorador(funcion):
        def envoltura(*args, **kwargs):
            if g.usuario["rol"] not in roles_permitidos:
                raise ValueError(construir_error_api(
                    "ROL_NO_AUTORIZADO",
                    "Acceso denegado",
                    f"El endpoint requiere uno de estos roles: {', '.join(roles_permitidos)}.",
                ), 403)
            return funcion(*args, **kwargs)
        envoltura.__name__ = funcion.__name__
        return requiere_login(envoltura)
    return decorador


def es_titular_o_admin(usuario_id) -> bool:
    """Devuelve True si el usuario autenticado es el dueño (usuario_id) o administrador; si no, 403."""
    if g.usuario["rol"] != "administrador" and int(usuario_id) != g.usuario["id"]:
        raise ValueError(construir_error_api(
            "RECURSO_NO_AUTORIZADO",
            "Acceso denegado",
            "El recurso no pertenece al usuario autenticado.",
        ), 403)
    return True