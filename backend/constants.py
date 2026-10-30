import os
from dotenv import load_dotenv

load_dotenv()

# Configuración general
BASE_URL = "/api"

# Configuración de MySQL
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")


# Configuración de seguridad (JWT)
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_EXPIRACION_MINUTOS = int(os.getenv("JWT_EXPIRACION_MINUTOS", "30"))


if not all([DB_USER, DB_PASSWORD, DB_NAME]):
    raise RuntimeError("Faltan variables de configuración de MySQL")
