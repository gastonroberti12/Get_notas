-- seed.sql - Datos iniciales de Cine Paradiso 
-- Esto se ejecuta despues del cine_paradiso.sql

USE cine_paradiso;

INSERT INTO sucursales (nombre, direccion, telefono) VALUES
    ('Centro', 'Av. Corrientes 1234', '1111222333'),
    ('Palermo', 'Av. Santa Fe 4321', '1144455566'),
    ('Belgrano', 'Av. Cabildo 2500', '1177788899');


INSERT INTO salas (sucursal_id, nombre, capacidad) VALUES
    ((SELECT id FROM sucursales WHERE nombre = 'Centro'),   'Sala 1',   100),
    ((SELECT id FROM sucursales WHERE nombre = 'Centro'),   'Sala 2',    60),
    ((SELECT id FROM sucursales WHERE nombre = 'Palermo'),  'Sala 1',    80),
    ((SELECT id FROM sucursales WHERE nombre = 'Palermo'),  'Sala 2',    40),
    ((SELECT id FROM sucursales WHERE nombre = 'Palermo'),  'Sala VIP',  30),
    ((SELECT id FROM sucursales WHERE nombre = 'Belgrano'), 'Sala 1',    60),
    ((SELECT id FROM sucursales WHERE nombre = 'Belgrano'), 'Sala 2',    50);
 

INSERT INTO butacas (sala_id, fila, numero)
WITH RECURSIVE secuencia AS (
    SELECT 1 AS n
    UNION ALL
    SELECT n + 1 FROM secuencia WHERE n < 10
)
SELECT salas.id, CHAR(64 + filas.n), numeros.n
FROM salas
JOIN secuencia AS filas ON filas.n <= salas.capacidad / 10
CROSS JOIN secuencia AS numeros;

-- Usuarios de prueba (contraseña: Admin1234, solo para desarrollo)
INSERT INTO usuarios (nombre, apellido, email, contrasena, rol) VALUES
    ('Admin', 'Paradiso', 'admin@cineparadiso.com',
     'scrypt:32768:8:1$BlIl9UlLuZjSmkI4$2192facdac3616c69fe2665c9a2489b71ad98e6679a866b1cc3bcc70272ddd3c880a726fcd544eba2438e55b4cb1e2991392df2a55a101886e97fbf7028c3c3d',
     'administrador'),
    ('Cliente', 'Prueba', 'cliente@cineparadiso.com',
     'scrypt:32768:8:1$BlIl9UlLuZjSmkI4$2192facdac3616c69fe2665c9a2489b71ad98e6679a866b1cc3bcc70272ddd3c880a726fcd544eba2438e55b4cb1e2991392df2a55a101886e97fbf7028c3c3d',
     'cliente');

-- Películas (póster null: se completa con PATCH o cargando desde OMDb)
INSERT INTO pelicula (titulo, sinopsis, duracion_min, clasificacion, genero, id_externo,
                      fecha_inicio_cartelera, fecha_fin_cartelera) VALUES
    ('The Godfather', 'La saga de la familia Corleone y su ascenso en el crimen organizado.',
     175, 'R', 'Crime, Drama', 'tt0068646', NOW(), NOW() + INTERVAL 60 DAY),
    ('Back to the Future', 'Un adolescente viaja al pasado en una máquina del tiempo.',
     116, 'PG', 'Adventure, Comedy, Sci-Fi', 'tt0088763', NOW(), NOW() + INTERVAL 60 DAY),
    ('Pulp Fiction', 'Historias entrelazadas de criminales en Los Ángeles.',
     154, 'R', 'Crime, Drama', 'tt0110912', NOW(), NOW() + INTERVAL 60 DAY);

-- Funciones relativas a la fecha de creación (ids: películas 1-3, salas 1-7 en el orden de arriba)
INSERT INTO funcion (pelicula_id, sala_id, fecha_hora, precio) VALUES
    (1, 1, CURDATE() + INTERVAL 1 DAY + INTERVAL 18 HOUR, 8500),
    (2, 2, CURDATE() + INTERVAL 1 DAY + INTERVAL 21 HOUR, 8500),
    (3, 3, CURDATE() + INTERVAL 2 DAY + INTERVAL 20 HOUR, 8500),
    (1, 4, CURDATE() + INTERVAL 2 DAY + INTERVAL 18 HOUR, 7000),
    (2, 5, CURDATE() + INTERVAL 3 DAY + INTERVAL 20 HOUR, 12000);

INSERT INTO servicios (nombre, descripcion, precio) VALUES
    ('Pochoclo grande', 'Pochoclo salado o dulce', 4500),
    ('Gaseosa', 'Vaso 500 ml', 3000),
    ('Combo pareja', '2 gaseosas y pochoclo grande', 9500),
    ('Estacionamiento', 'Ticket de 4 horas', 2500);