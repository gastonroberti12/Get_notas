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
- Python 3.
- Git.
- Postman para ejecutar las pruebas manuales.

---

## 1. Levantar todo el proyecto con Docker

Desde la raíz del proyecto:

```powershell
docker compose up -d
```

Para construir o reconstruir las imágenes después de actualizar el código:

```powershell
git pull
docker compose up -d --build frontend backend
```

Docker levantará MySQL, el backend Flask en el puerto 5001 y el frontend Flask en el puerto 5000.

Comprobar el contenedor:

```powershell
docker compose ps
```

Detener la base de datos:

```powershell
docker compose down
```

Para borrar también los datos persistidos y recrear la base desde cero:

```powershell
docker compose down -v
docker compose up -d
```

El contenedor usa el nombre `mysql-cine-paradiso` y expone MySQL en `localhost:3306`.

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

Primero copiá el archivo de ejemplo:

```powershell
Copy-Item backend/.env.example backend/.env
```

Configurá en `backend/.env` la contraseña y la clave de OMDb. El archivo `.env` está excluido por Git y no debe subirse al repositorio.

> Este paso se ejecuta una sola vez al clonar el repositorio o inicializar el proyecto.

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
DELETE /butacas/{id}
DELETE /salas/{sala_id}/butacas
```

### Servicios

```text
GET    /servicios
GET    /servicios/{id}
POST   /servicios
PATCH  /servicios/{id}
DELETE /servicios/{id}
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
3. Crear una colección de Postman o importar la colección del repositorio si está disponible.
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
