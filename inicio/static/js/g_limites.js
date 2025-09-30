// static/js/g_lites.js
document.addEventListener("DOMContentLoaded", function () {
  // --- manejo de inputs dinámicos ---
  let nextIndex = 1; // ya existe el índice 0 en el HTML inicial
  const addBtn = document.getElementById('newfuncion');
  const container = document.getElementById('inputs-container');

  // delegación para eliminar (funciona tanto para botones existentes como para los creados)
  if (container) {
    container.addEventListener('click', function(e) {
      const btn = e.target.closest('.remove-btn, .remove-btn *');
      if (!btn) return;
      const row = btn.closest('.input-row');
      if (!row) return;

      const rows = container.querySelectorAll('.input-row');
      if (rows.length <= 1) {
        // si es el único row, limpiar los inputs en lugar de eliminarlo
        row.querySelectorAll('input').forEach(i => i.value = '');
      } else {
        row.remove();
      }
    });
  }

  // función de ayuda para crear un nuevo row (misma estructura que el template)
  function createFunctionRow(index, funcValue = "", cValue = "0") {
    const row = document.createElement('div');
    row.className = 'input-row';
    row.dataset.rowIndex = String(index);

    row.innerHTML = `
      <div class="input-container">
        <label class="form-label visually-hidden" for="funcion-${index}">Función</label>
        <input required id="funcion-${index}" type="text" name="funcion[]" placeholder="ej. x**2+1" aria-label="Función" />
      </div>

      <div class="input-container" style="max-width:110px;">
        <label class="form-label visually-hidden" for="c-${index}">c</label>
        <input id="c-${index}" type="text" name="c[]" value="${cValue}" placeholder="c" aria-label="Valor de c" />
      </div>

      <button type="button" class="remove-btn" title="Eliminar esta función" aria-label="Eliminar función">
        <i class="bi bi-x-lg"></i>
      </button>
    `;

    // asignar valor de la función (si se pasa)
    const inp = row.querySelector(`#funcion-${index}`);
    if (inp && funcValue) inp.value = funcValue;

    return row;
  }

  if (addBtn) {
    addBtn.addEventListener('click', function () {
      if (!container) {
        console.warn("No se encontró #inputs-container. Asegúrate de que el formulario exista.");
        return;
      }
      const newRow = createFunctionRow(nextIndex);
      container.appendChild(newRow);
      const focusInput = newRow.querySelector('input[name="funcion[]"]');
      if (focusInput) focusInput.focus();
      nextIndex++;
    });
  }

  // --- Plotly: graficar múltiples funciones desde resultados-data exportado por Django ---
  try {
    const resultadosElem = document.getElementById('resultados-data');
    if (!resultadosElem) {
      // no hay datos -> no graficar
      return;
    }

    let resultados = [];
    try {
      resultados = JSON.parse(resultadosElem.textContent || '[]');
    } catch (e) {
      console.error('No se pudo parsear resultados-data:', e);
      resultados = [];
    }

    const traces = [];
    resultados.forEach((r, idx) => {
      let xs = r.x_json;
      let ys = r.y_json;

      // si vinieron como strings JSON (p. ej. si en la view hiciste json.dumps), intentar parsear
      if (typeof xs === 'string') {
        try { xs = JSON.parse(xs); } catch(e) { xs = null; }
      }
      if (typeof ys === 'string') {
        try { ys = JSON.parse(ys); } catch(e) { ys = null; }
      }

      if (!Array.isArray(xs) || !Array.isArray(ys) || xs.length !== ys.length) {
        console.warn('Datos inválidos para la función:', r.funcion);
        return;
      }

      traces.push({
        x: xs,
        y: ys,
        mode: 'lines',
        name: r.funcion || `f${idx+1}(x)`,
        line: { width: 2 }
      });

      // marcar aproximación en c (primer y finito cercano)
      const cval = parseFloat(r.c);
      if (!Number.isNaN(cval)) {
        let nearestY = null;
        for (let i = 0; i < xs.length; i++) {
          const yi = ys[i];
          if (yi !== null && yi !== undefined && !isNaN(yi) && isFinite(yi)) {
            nearestY = yi;
            break;
          }
        }
        if (nearestY !== null) {
          traces.push({
            x: [cval],
            y: [nearestY],
            mode: 'markers',
            name: `c (${r.funcion})`,
            marker: { size: 8, symbol: 'circle' }
          });
        }
      }
    });

    const plotEl = document.getElementById('plotly-div');
    if (!plotEl) return;

    if (traces.length > 0) {
      const layout = {
        title: 'Gráficas de funciones',
        xaxis: { title: 'x' },
        yaxis: { title: 'f(x)', autorange: true },
        showlegend: true,
        margin: { t: 40, b: 40 }
      };
      Plotly.newPlot(plotEl, traces, layout, { responsive: true });
    } else {
      plotEl.innerHTML = '<p class="text-muted">No hay funciones válidas para graficar.</p>';
    }

  } catch (err) {
    console.error("Error al inicializar la gráfica:", err);
  }
});
