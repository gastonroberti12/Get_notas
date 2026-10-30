-- Cine Paradiso - Script de creación y carga (MySQL 8+)
DROP DATABASE IF EXISTS cine_paradiso;
CREATE DATABASE cine_paradiso CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE cine_paradiso;

-- ============ ESTRUCTURA FÍSICA ============
CREATE TABLE sucursales (
    id        INT AUTO_INCREMENT PRIMARY KEY,
    nombre    VARCHAR(100) NOT NULL,
    direccion VARCHAR(200) NOT NULL,
    telefono  VARCHAR(30)
);

CREATE TABLE salas (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    sucursal_id INT NOT NULL,
    nombre      VARCHAR(50) NOT NULL,
    capacidad   INT NOT NULL,
    UNIQUE (sucursal_id, nombre),
    FOREIGN KEY (sucursal_id) REFERENCES sucursales(id)
);

CREATE TABLE butacas (
    id      INT AUTO_INCREMENT PRIMARY KEY,
    sala_id INT NOT NULL,
    fila    CHAR(1) NOT NULL,
    numero  INT NOT NULL,
    UNIQUE (sala_id, fila, numero),
    FOREIGN KEY (sala_id) REFERENCES salas(id)
);

-- ============ USUARIOS ============
CREATE TABLE usuarios (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    nombre         VARCHAR(80)  NOT NULL,
    apellido       VARCHAR(80)  NOT NULL,
    email          VARCHAR(150) NOT NULL UNIQUE,
    contrasena     VARCHAR(255) NOT NULL,  -- hash, nunca texto plano
    rol            ENUM('cliente','administrador') NOT NULL DEFAULT 'cliente',
    fecha_registro DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_ultimo_logout DATETIME NULL  -- se actualiza en el logout
);

-- ============ CARTELERA ============
CREATE TABLE pelicula (
    id                     INT AUTO_INCREMENT PRIMARY KEY,
    titulo                 VARCHAR(200) NOT NULL,
    sinopsis               TEXT,
    poster_url             VARCHAR(500),
    duracion_min           INT,
    clasificacion          VARCHAR(20),
    genero                 VARCHAR(100),
    id_externo             VARCHAR(20) UNIQUE,  -- imdbID de OMDb
    fecha_inicio_cartelera DATETIME,
    fecha_fin_cartelera    DATETIME,
    activa                 BOOLEAN NOT NULL DEFAULT TRUE  -- baja lógica
);

CREATE TABLE funcion (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    pelicula_id INT NOT NULL,
    sala_id     INT NOT NULL,
    fecha_hora  DATETIME NOT NULL,
    precio      DECIMAL(10,2) NOT NULL,
    activa      BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE (sala_id, fecha_hora),
    FOREIGN KEY (pelicula_id) REFERENCES pelicula(id),
    FOREIGN KEY (sala_id)     REFERENCES salas(id)
);

-- ============ COMPRAS ============
CREATE TABLE reservas (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id        INT NOT NULL,
    funcion_id        INT NOT NULL,
    fecha_compra      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    estado            ENUM('pendiente','confirmada','cancelada','expirada','finalizada') NOT NULL DEFAULT 'pendiente',
    total             DECIMAL(10,2) NOT NULL DEFAULT 0,
    fecha_cancelacion DATETIME,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
    FOREIGN KEY (funcion_id) REFERENCES funcion(id)
);

CREATE TABLE entrada (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    reserva_id INT NOT NULL,
    butaca_id  INT NOT NULL,
    codigo_qr  VARCHAR(64) UNIQUE,
    estado     ENUM('pendiente','confirmada','cancelada','finalizada') NOT NULL DEFAULT 'pendiente',
    fecha_uso  DATETIME,
    FOREIGN KEY (reserva_id) REFERENCES reservas(id),
    FOREIGN KEY (butaca_id)  REFERENCES butacas(id)
);

CREATE TABLE servicios (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    nombre      VARCHAR(100) NOT NULL,
    descripcion VARCHAR(255),
    precio      DECIMAL(10,2) NOT NULL,
    activo      BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE reserva_servicios (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    reserva_id      INT NOT NULL,
    servicio_id     INT NOT NULL,
    cantidad        INT NOT NULL,
    precio_unitario DECIMAL(10,2) NOT NULL,  -- precio congelado al momento de la compra
    UNIQUE (reserva_id, servicio_id),
    FOREIGN KEY (reserva_id)  REFERENCES reservas(id),
    FOREIGN KEY (servicio_id) REFERENCES servicios(id)
);
