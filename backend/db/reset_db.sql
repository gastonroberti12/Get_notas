-- reset_db.sql - Reseteo de datos de Cine Paradiso (#41)
-- Vacía TODAS las tablas y reinicia los AUTO_INCREMENT, pero conserva la estructura.
-- SOLO PARA DESARROLLO Y PRUEBAS: borra usuarios, reservas y entradas también.
--
-- Uso: ejecutar este archivo y DESPUÉS seed.sql para volver a cargar los datos iniciales.
--   1) reset_db.sql   (vacía)
--   2) seed.sql       (carga sucursales, salas, butacas, usuarios, películas, funciones y servicios)

USE cine_paradiso;

-- TRUNCATE falla en tablas referenciadas por claves foráneas, así que se desactiva el
-- chequeo mientras se vacía y se vuelve a activar al final.
SET FOREIGN_KEY_CHECKS = 0;

TRUNCATE TABLE reserva_servicios;
TRUNCATE TABLE entrada;
TRUNCATE TABLE reservas;
TRUNCATE TABLE funcion;
TRUNCATE TABLE pelicula;
TRUNCATE TABLE servicios;
TRUNCATE TABLE usuarios;
TRUNCATE TABLE butacas;
TRUNCATE TABLE salas;
TRUNCATE TABLE sucursales;

SET FOREIGN_KEY_CHECKS = 1;