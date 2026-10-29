-- seed.sql - Datos iniciales de Cine Paradiso 
-- Esto se ejecuta despues del cine_paradiso.sql

-- #37 Sucursales y salas con capacidades distintas

INSERT INTO sucursales (nombre, direccion, telefono) VALUES
    ('Centro', 'Av. Corrientes 1234', '1111222333'),
    ('Palermo', 'Av. Santa Fe 4321', '1144455566'),
    ('Belgrano', 'Av. Cabildo 2500', '1177788899');

-- La capacidad siempre es múltiplo de 10 (filas de 10 butacas), máximo 100.
-- El sucursal_id se busca por nombre, así no depende de cómo quedaron los ids.
INSERT INTO salas (sucursal_id, nombre, capacidad) VALUES
    ((SELECT id FROM sucursales WHERE nombre = 'Centro'),   'Sala 1',   100),
    ((SELECT id FROM sucursales WHERE nombre = 'Centro'),   'Sala 2',    60),
    ((SELECT id FROM sucursales WHERE nombre = 'Palermo'),  'Sala 1',    80),
    ((SELECT id FROM sucursales WHERE nombre = 'Palermo'),  'Sala 2',    40),
    ((SELECT id FROM sucursales WHERE nombre = 'Palermo'),  'Sala VIP',  30),
    ((SELECT id FROM sucursales WHERE nombre = 'Belgrano'), 'Sala 1',    60),
    ((SELECT id FROM sucursales WHERE nombre = 'Belgrano'), 'Sala 2',    50);
 
-- #38 Butacas por sala
-- Cada sala tiene capacidad / 10 filas (A, B, C...) de 10 butacas.
-- Un solo INSERT genera las de todas las salas, y así la cantidad
-- de butacas siempre coincide con salas.capacidad.
-- ------------------------------------------------------------
INSERT INTO butacas (sala_id, fila, numero) 
WITH RECURSIVE filas AS (
    SELECT 1 AS columna
    UNION ALL
    SELECT columna + 1 -- toma el ultimo numero generado y le suma 1
    FROM filas
    WHERE columna < 10 -- se repite mientras el numero sea menor a 10
),
numeros_butaca AS (
    SELECT columna
    FROM filas
)
SELECT
    salas.id,
    CHAR(64 + filas.columna) AS fila, -- convierte un numero en un caracter (ASCII) sirve para filas en letras
    numeros_butaca.columna AS columna
FROM salas
JOIN filas
    ON filas.columna <= salas.capacidad / 10 -- determina cuantas filas va a tener la sala
CROSS JOIN numeros_butaca; -- combina cada fila con las 10 butacas posibles