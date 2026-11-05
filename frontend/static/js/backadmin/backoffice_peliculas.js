// Solo UI: vista previa del póster y fecha de fin sugerida (inicio + 7 días).
const url = document.getElementById('poster_url');
const img = document.getElementById('poster-img');
const vacio = document.getElementById('poster-vacio');
const inicio = document.getElementById('fecha_inicio_cartelera');
const fin = document.getElementById('fecha_fin_cartelera');


url.addEventListener('input', () => {
  img.src = url.value;
  img.hidden = !url.value;
  vacio.hidden = !!url.value;
});
img.addEventListener('error', () => { img.hidden = true; vacio.hidden = false; });


inicio.addEventListener('change', () => {
  if (!inicio.value || fin.value) return;
  const f = new Date(inicio.value);
  f.setDate(f.getDate() + 7);
  const dos = (n) => String(n).padStart(2, '0');
  fin.value = `${f.getFullYear()}-${dos(f.getMonth() + 1)}-${dos(f.getDate())}T${dos(f.getHours())}:${dos(f.getMinutes())}`;
});