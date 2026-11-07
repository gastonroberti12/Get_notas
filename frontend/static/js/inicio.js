// ===================================
// CARRUSEL DE PELÍCULAS
// ===================================

document.addEventListener("DOMContentLoaded", function () {

    const carrusel = document.querySelector(".carousel-container");

    if (!carrusel) return;

    const peliculas = [...carrusel.querySelectorAll(".carousel-slide")];
    const btnAnterior = carrusel.querySelector(".carousel-prev");
    const btnSiguiente = carrusel.querySelector(".carousel-next");
    const indicadores = carrusel.querySelector(".carousel-indicators");

    if (peliculas.length === 0) return;

    let indiceActual = 0;
    let animando = false;

    const DURACION = 500;
    const DESPLAZAMIENTO = 50;

    // Inicializar el carrusel
    peliculas.forEach((pelicula, indice) => {
        pelicula.hidden = indice !== 0;
    });

    // Actualizar indicadores
    function actualizarIndicadores() {
        if (!indicadores) return;

        indicadores.querySelectorAll("button").forEach((boton, indice) => {
            const activo = indice === indiceActual;

            boton.classList.toggle("activo", activo);
            boton.setAttribute("aria-current", String(activo));
        });
    }

    // Cambiar película con animación
    function mostrarPelicula(indice, direccion = 1) {

        if (animando) return;

        const nuevoIndice = (indice + peliculas.length) % peliculas.length;

        if (nuevoIndice === indiceActual) return;

        animando = true;

        const saliente = peliculas[indiceActual];
        const entrante = peliculas[nuevoIndice];

        entrante.hidden = false;

        // La película entrante aparece por encima
        entrante.style.zIndex = "2";
        saliente.style.zIndex = "1";

        // Respetar preferencias de movimiento reducido
        const reducirMovimiento = window.matchMedia(
            "(prefers-reduced-motion: reduce)"
        ).matches;

        if (reducirMovimiento) {
            saliente.hidden = true;
            entrante.style.zIndex = "";
            saliente.style.zIndex = "";
            indiceActual = nuevoIndice;
            actualizarIndicadores();
            animando = false;
            return;
        }

        // Animación de salida
        const animacionSalida = saliente.animate(
            [
                {
                    opacity: 1,
                    transform: "translateX(0)"
                },
                {
                    opacity: 0,
                    transform: `translateX(${-direccion * DESPLAZAMIENTO}px)`
                }
            ],
            {
                duration: DURACION,
                easing: "ease-in-out",
                fill: "forwards"
            }
        );

        // Animación de entrada
        const animacionEntrada = entrante.animate(
            [
                {
                    opacity: 0,
                    transform: `translateX(${direccion * DESPLAZAMIENTO}px)`
                },
                {
                    opacity: 1,
                    transform: "translateX(0)"
                }
            ],
            {
                duration: DURACION,
                easing: "ease-in-out",
                fill: "forwards"
            }
        );

        indiceActual = nuevoIndice;
        actualizarIndicadores();

        // Finalizar cuando ambas animaciones terminen
        Promise.all([
            animacionSalida.finished,
            animacionEntrada.finished
        ]).then(() => {

            saliente.hidden = true;

            animacionSalida.cancel();
            animacionEntrada.cancel();

            saliente.style.zIndex = "";
            entrante.style.zIndex = "";

            animando = false;
        });

    }

    // Crear indicadores
    if (indicadores) {

        peliculas.forEach((_, indice) => {

            const boton = document.createElement("button");

            boton.type = "button";
            boton.classList.add("carousel-indicador");

            boton.setAttribute(
                "aria-label",
                `Mostrar película ${indice + 1}`
            );

            boton.addEventListener("click", () => {
                const direccion = indice > indiceActual ? 1 : -1;
                mostrarPelicula(indice, direccion);
            });

            indicadores.appendChild(boton);
        });

    }

    // Flecha anterior
    btnAnterior?.addEventListener("click", () => {
        mostrarPelicula(indiceActual - 1, -1);
    });

    // Flecha siguiente
    btnSiguiente?.addEventListener("click", () => {
        mostrarPelicula(indiceActual + 1, 1);
    });

    actualizarIndicadores();
    
    // Cambio automatico cada 5 segundos
    const INTERVALO = 10000;

    if (peliculas.length > 1) {
        setInterval(() => {
            mostrarPelicula(indiceActual + 1, 1);
        }, INTERVALO);
    }

});
// ===================================
// FILTROS POR GÉNERO
// ===================================

document.addEventListener("DOMContentLoaded", function () {

    const contenedorFiltros = document.querySelector(".filtros-container");
    const peliculas = document.querySelectorAll(".pelicula-card");

    if (!contenedorFiltros || peliculas.length === 0) return;

    // Obtener todos los géneros disponibles
    const generos = new Set();

    peliculas.forEach(pelicula => {

        const listaGeneros = pelicula.dataset.generos.split(",");

        listaGeneros.forEach(genero => {
            if (genero.trim()) {
                generos.add(genero.trim());
            }
        });

    });

    // Crear un botón para filtrar
    function crearBoton(nombre) {

        const boton = document.createElement("button");

        boton.type = "button";
        boton.classList.add("filtro-btn");
        boton.textContent = nombre;

        boton.setAttribute("aria-pressed", "false");

        boton.addEventListener("click", () => {
            filtrarPeliculas(nombre);
        });

        contenedorFiltros.appendChild(boton);
    }

    // Botón para mostrar todas las películas
    crearBoton("Todas");

    // Crear botones según los géneros existentes
    [...generos].sort().forEach(genero => {
        crearBoton(genero);
    });

    // Filtrar tarjetas
    function filtrarPeliculas(generoSeleccionado) {

        peliculas.forEach(pelicula => {

            const generosPelicula = pelicula.dataset.generos
                .split(",")
                .map(genero => genero.trim());

            const mostrar =
                generoSeleccionado === "Todas" ||
                generosPelicula.includes(generoSeleccionado);

            pelicula.hidden = !mostrar;

        });

        // Actualizar el botón seleccionado
        contenedorFiltros.querySelectorAll(".filtro-btn").forEach(boton => {

            const activo = boton.textContent === generoSeleccionado;

            boton.classList.toggle("activo", activo);
            boton.setAttribute("aria-pressed", String(activo));

        });

    }

    // Mostrar todas las películas inicialmente
    filtrarPeliculas("Todas");

});

