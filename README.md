# Get_notas
Trabajo Final Catedra lanzillotta

## Integración con OMDb

El backend expone estos endpoints para consultar películas:

- `GET /api/peliculas/buscar?q=batman&pagina=1`
- `GET /api/peliculas/<imdb_id>` (por ejemplo, `/api/peliculas/tt0372784`)

Copiá `backend/.env.example` a `backend/.env` y reemplazá el valor por tu clave nueva de OMDb. El backend carga ese archivo al iniciar y `.env` está excluido de Git, por lo que la clave no se versiona. No uses la clave que compartiste en la imagen: regenerala primero en OMDb. Desde la carpeta `backend`, instalá las dependencias con `python -m pip install -r requirements.txt` e iniciá el servidor con `python app.py`.

La integración consulta OMDb en tiempo real; todavía no persiste películas en MySQL.
