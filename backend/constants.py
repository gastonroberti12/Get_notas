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

if not all([DB_USER, DB_PASSWORD, DB_NAME]):
    raise RuntimeError("Faltan variables de configuración de MySQL")

CAMPOS_SERVICIOS_PERMITIDOS = ("nombre", "descripcion", "precio", "activo")
