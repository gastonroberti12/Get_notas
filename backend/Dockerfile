FROM python:3.12-slim
# direccion de trabajo dentro del contenedor
WORKDIR /app

# Evita que Python genere archivos .pyc y carpetas __pycache__ innecesarias
ENV PYTHONDONTWRITEBYTECODE=1

# Fuerza a que los print() y logs salgan en tiempo real en la consola de Docker
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 10000

CMD gunicorn --workers 1 --threads 4 --timeout 120 --bind 0.0.0.0:${PORT:-10000} app:app