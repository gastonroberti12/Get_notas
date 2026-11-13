# Cine Paradiso — API

Trabajo final de la cátedra Lanzillotta.

## Integrantes

- Gastón Roberti - 116174
- Leandro Piccicacco - 116059
- Cristian Nahuel Daglio - 116017
- Tiago Elias Melilli - 116111
- Juan Francisco Skanata - 116128
- Alexis Martin Blazek - 115977
- Lucía Hernández Tamagno 116281
- Baltazar Marani - 115983
- Agustín Perata - 115580

## Requisitos previos

- Docker Desktop con Docker Compose.
- Python 3, solo si vas a ejecutar los servicios fuera de Docker.
- Git, para clonar o actualizar el repositorio.
- Postman, opcional, para ejecutar las pruebas manuales.

---

## 1. Levantar todo el proyecto con Docker

En la primera ejecución, prepará los archivos de entorno según el paso 2 y luego, desde la raíz del proyecto:

```powershell
docker compose up -d --build
```

Para construir o reconstruir las imágenes después de actualizar el código (Repo remoto):

```powershell
git pull
docker compose up -d --build 

```

Docker levantará MySQL, el backend Flask en el puerto 5001 y el frontend Flask en el puerto 5000.

Comprobar el contenedor:

```powershell
docker compose ps
```

Detener todos los servicios:

```powershell
docker compose down
```

Para borrar también los datos persistidos y recrear la base desde cero:

```powershell
docker compose down -v
docker compose up -d
```

> **Atención:** `docker compose down -v` elimina el volumen de MySQL y todos los datos guardados.

El contenedor usa el nombre `mysql-cine-paradiso`. MySQL se expone por defecto en `localhost:3306`. Si ese puerto está ocupado, podés definir `DB_PORT=3307` en un archivo `.env` junto a `docker-compose.yml`; esto cambia el puerto del host, mientras que el backend sigue conectándose al puerto `3306` dentro de Docker.

### Consultar la base desde la consola

```powershell
docker exec -it mysql-cine-paradiso mysql -u cine -pcine_password cine_paradiso
```

Dentro de MySQL:

```sql
SHOW TABLES;
USE cine_paradiso;
SELECT * FROM funcion;
```

---

## 2. Configuración inicial del entorno

Copiá los archivos de ejemplo:

```powershell
Copy-Item backend/.env.example backend/.env
Copy-Item frontend/.env.example frontend/.env
```

En Linux o macOS:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

En `backend/.env`, configurá las credenciales de MySQL y `JWT_SECRET_KEY`. La clave `OMDB_API_KEY` es necesaria para buscar películas en OMDb; las variables `SMTP_*` se usan para enviar correos. En `frontend/.env`, reemplazá `SECRET_KEY` por una clave propia para las sesiones.

No subas estos archivos ni sus claves al repositorio.

> Este paso se ejecuta una sola vez al clonar el repositorio o inicializar el proyecto. Docker Compose necesita ambos archivos porque los dos servicios los declaran como `env_file`.

### Opción A: virtualenv

#### Windows

Desde la raíz del proyecto:

```powershell
setup_virtualenv.bat
```

#### Linux / macOS

```bash
chmod +x setup_virtualenv.sh
./setup_virtualenv.sh
```

### Opción B: pipenv

#### Windows

```powershell
setup_pipenv.bat
```

#### Linux / macOS

```bash
chmod +x setup_pipenv.sh
./setup_pipenv.sh
```

---

## 3. Activar y desactivar el entorno virtual

### Con virtualenv

Los scripts crean el entorno dentro de la carpeta `backend`.

#### Windows

```powershell
cd backend
.venv\Scripts\activate
```

#### Linux / macOS

```bash
cd backend
source .venv/bin/activate
```

Para desactivar:

```bash
deactivate
```

### Con pipenv

#### Windows

```powershell
cd backend
python -m pipx run pipenv shell
```

#### Linux / macOS

```bash
cd backend
pipenv shell
```

Para salir:

```bash
exit
```

---

## 4. Ejecutar la aplicación Flask

Con la base de datos levantada y el entorno configurado:

```bash
cd backend
python app.py
```

La API queda disponible en:

```text
http://localhost:5001
```

Este comando inicia solo el backend. Para usar la aplicación completa, es más simple iniciar también el frontend mediante Docker Compose, como se describe en la sección 1.

Con Docker Compose, no es necesario activar un entorno virtual ni ejecutar Flask manualmente.
Los servicios pueden levantarse o actualizarse con:

```powershell
docker compose up -d --build frontend backend
```

---

## 5. Integración con OMDb

La clave de OMDb debe estar configurada como `OMDB_API_KEY` en `backend/.env`.

Endpoints externos disponibles:

```text
GET /peliculas/buscar?q=batman&pagina=1
GET /peliculas/tt0372784
```

Las películas consultadas también pueden almacenarse localmente y sus pósters se guardan en `frontend/static/images`.

---

## 6. Endpoints principales

### Autenticación

```text
POST /auth/login
POST /auth/logout
```

### Películas

```text
GET    /peliculas
GET    /peliculas/{id}
GET    /peliculas/buscar?q=batman&pagina=1
GET    /peliculas/{imdb_id}
POST   /peliculas
PATCH  /peliculas/{id}
DELETE /peliculas/{id}
```

### Funciones

```text
GET    /funciones
GET    /funciones/{id}
POST   /funciones
PATCH  /funciones/{id}
DELETE /funciones/{id}
```

Para consultar las funciones activas de una sucursal, el frontend puede filtrar
por `sucursal_id` y `activa`:

```text
GET /funciones?sucursal_id=1&activa=true
```

Ejemplo para reservar o consultar una función:

```text
GET http://localhost:5001/funciones/1
```

### Sucursales y salas

```text
GET    /sucursales
GET    /sucursales/{id}
POST   /sucursales
PATCH  /sucursales/{id}
DELETE /sucursales/{id}

GET    /salas
GET    /salas/{id}
POST   /salas
PATCH  /salas/{id}
DELETE /salas/{id}
```

### Butacas

```text
GET    /salas/{sala_id}/butacas
POST   /salas/{sala_id}/butacas/generar
POST   /butacas
PATCH  /butacas/{id}
DELETE /butacas/{id}
DELETE /salas/{sala_id}/butacas
```

### Reservas y entradas

```text
GET    /reservas                         (administrador)
GET    /usuarios/me/reservas             (cliente autenticado)
GET    /reservas/{id}
GET    /reservas/{id}/entradas
POST   /reservas                         (crear reserva)
POST   /reservas/{id}/pago
PATCH  /reservas/{id}                    (cancelar reserva)

GET    /entradas                         (administrador)
GET    /usuarios/me/entradas             (cliente autenticado)
GET    /entradas/{id}
POST   /entradas/validacion              (validar QR)
```

Las reservas pendientes vencen según `RESERVA_EXPIRACION_MINUTOS` (8 minutos por defecto). El backend valida el vencimiento al confirmar el pago.

### Servicios

```text
GET    /servicios
GET    /servicios/{id}
POST   /servicios
PATCH  /servicios/{id}
DELETE /servicios/{id}
GET    /reservas/{reserva_id}/servicios
POST   /reservas/{reserva_id}/servicios
PATCH  /reservas/{reserva_id}/servicios/{servicio_reserva_id}
DELETE /reservas/{reserva_id}/servicios/{servicio_reserva_id}
```

Los listados admiten paginación con `_limit` y `_offset`:

```text
GET /funciones?_limit=10&_offset=0
GET /salas?_limit=10&_offset=0
```

---

## 7. Pruebas con Postman

1. Levantar el proyecto con `docker compose up -d`.
2. Usar el frontend o ejecutar una consulta de prueba.
3. Importar `backend/tests/Cine Paradiso - Suite de pruebas API.postman_collection.json` en Postman.
4. Usar `http://localhost:5001` como URL base.
5. Para endpoints `POST` o `PATCH`, seleccionar `Body > raw > JSON` y agregar el header:

```text
Content-Type: application/json
```

Ejemplo para crear una función:

```json
{
  "pelicula_id": 1,
  "sala_id": 1,
  "fecha_hora": "2026-11-01T18:00:00",
  "precio": 8500
}
```
