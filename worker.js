/* ============================================================
   worker.js — roda o Pyodide (Python) fora da thread principal,
   para o cálculo não travar a interface.
   ============================================================ */

importScripts("https://cdn.jsdelivr.net/pyodide/v0.26.2/full/pyodide.js");

let pyodide = null;

const PY_MODULOS = [
  "utilitarios/leitor_itens.py",
  "utilitarios/desenhador.py",
  "empacotador/item.py",
  "empacotador/faixa3.py",
  "empacotador/faixa2.py",
  "empacotador/bin.py",
  "empacotador/empacotador.py",
  "algoritmo_genetico/parametros_ga.py",
  "algoritmo_genetico/individuo.py",
  "algoritmo_genetico/algoritmo_genetico.py",
  "parametros_spec.py",
  "solver_api.py",
  "bridge.py",
];

function progresso(txt) {
  self.postMessage({ progresso: txt });
}

async function iniciar() {
  progresso("Carregando o motor de cálculo…");
  pyodide = await loadPyodide();

  progresso("Preparando o algoritmo…");
  for (const d of ["utilitarios", "empacotador", "algoritmo_genetico"]) {
    try { pyodide.FS.mkdir(d); } catch (e) { /* já existe */ }
  }
  for (const caminho of PY_MODULOS) {
    try {
      const resp = await fetch("pysrc/" + caminho, { cache: "no-store" });
      if (!resp.ok) throw new Error("HTTP " + resp.status);
      pyodide.FS.writeFile(caminho, await resp.text());
    } catch (e) {
      throw new Error("Falha ao carregar " + caminho + " (" + e.message + ")");
    }
  }
  pyodide.runPython("import sys; sys.path.insert(0, '.')");
  pyodide.runPython("import bridge, json");
}

self.onmessage = async (ev) => {
  const { id, tipo, dados } = ev.data;
  try {
    if (tipo === "iniciar") {
      await iniciar();
      self.postMessage({ id, ok: true, resultado: true });

    } else if (tipo === "spec") {
      const specJson = pyodide.runPython("bridge.obter_spec_parametros()");
      self.postMessage({ id, ok: true, resultado: JSON.parse(specJson) });

    } else if (tipo === "resolver") {
      const { largura_bin, altura_bin, parametros, pecas } = dados;
      // passa os dados como variáveis globais no Python (evita problemas de escape)
      pyodide.globals.set("_larg", largura_bin);
      pyodide.globals.set("_alt", altura_bin);
      pyodide.globals.set("_pecas_json", JSON.stringify(pecas));
      pyodide.globals.set("_param_json", JSON.stringify(parametros || {}));
      const saidaJson = pyodide.runPython(
        "bridge.resolver_json(_larg, _alt, _pecas_json, _param_json)"
      );
      self.postMessage({ id, ok: true, resultado: JSON.parse(saidaJson) });

    } else {
      self.postMessage({ id, ok: false, erro: "Comando desconhecido." });
    }
  } catch (e) {
    self.postMessage({ id, ok: false, erro: (e && e.message) || String(e) });
  }
};
