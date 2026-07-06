/* ============================================================
   Plano de Corte — versão web (roda no navegador via Pyodide)
   O algoritmo Python roda dentro do navegador do usuário.
   Nada é enviado a servidor algum.
   ============================================================ */

"use strict";

/* ---------- Pyodide roda num Web Worker (não trava a interface) ---------- */
let worker = null;
let PY_PRONTO = false;
let _msgId = 0;
const _pendentes = new Map();
let _cancelado = false;

function _criarWorker() {
  const txt = document.getElementById("carregandoAppTxt");
  const w = new Worker("worker.js");
  w.onmessage = (ev) => {
    const { id, ok, resultado, erro, progresso } = ev.data;
    if (progresso) {
      if (txt) txt.textContent = progresso;
      return;
    }
    const p = _pendentes.get(id);
    if (!p) return;
    _pendentes.delete(id);
    if (ok) p.resolve(resultado);
    else p.reject(new Error(erro || "Erro no cálculo."));
  };
  w.onerror = () => {
    if (txt) txt.textContent = "Não foi possível carregar o programa.";
  };
  return w;
}

function chamarWorker(tipo, dados) {
  return new Promise((resolve, reject) => {
    const id = ++_msgId;
    _pendentes.set(id, { resolve, reject });
    worker.postMessage({ id, tipo, dados });
  });
}

function calcularNoWorker(payload) {
  return chamarWorker("resolver", payload);
}

// Cancela o cálculo em andamento: mata o worker (interrompe o Python na hora)
// e cria um novo, já pronto para o próximo cálculo.
async function cancelarExecucao() {
  _cancelado = true;
  // rejeita qualquer promessa pendente para o fluxo do resolver saber que parou
  for (const [id, p] of _pendentes) {
    p.reject(new Error("__cancelado__"));
  }
  _pendentes.clear();
  if (worker) worker.terminate();
  // recria o worker e reinicializa o Pyodide em segundo plano
  worker = _criarWorker();
  try {
    await chamarWorker("iniciar", null);
  } catch (e) {
    // se falhar ao reinicializar, o usuário pode recarregar a página
  }
}

async function iniciarPython() {
  const txt = document.getElementById("carregandoAppTxt");
  try {
    worker = _criarWorker();
    // manda o worker inicializar o Pyodide e carregar os módulos
    await chamarWorker("iniciar", null);
    PY_PRONTO = true;
    document.getElementById("carregandoApp").classList.add("pronto");
  } catch (e) {
    txt.textContent = "Não foi possível carregar o programa.";
    txt.insertAdjacentHTML(
      "afterend",
      '<p class="carregando-app__erro">' + (e.message || e) +
      "<br>Verifique sua conexão e recarregue a página.</p>"
    );
  }
}


// Paleta de amostras nomeadas comuns em marcenaria (nome -> cor de exibição).
// Se o usuário digitar um nome desconhecido, geramos uma cor estável a partir do texto.
const CORES_CONHECIDAS = {
  "branco": "#F3F0E9",
  "preto": "#2B2925",
  "carvalho": "#C89B6A",
  "nogueira": "#6E4B2A",
  "cinza": "#9A9488",
  "cru": "#DCCFA8",
  "amadeirado": "#B07C4E",
  "mel": "#D8A24A",
  "grafite": "#4A4741",
  "vermelho": "#B5462E",
  "azul": "#3B6A63",
};

const el = (sel) => document.querySelector(sel);

const linhasPecas = el("#linhasPecas");
let contadorLinhas = 0;

/* ---------- Cor de exibição a partir do nome ---------- */
function corDeExibicao(nome) {
  const chave = (nome || "").trim().toLowerCase();
  if (CORES_CONHECIDAS[chave]) return CORES_CONHECIDAS[chave];
  if (!chave) return "#CFC7B4";
  // hash simples e determinístico -> matiz estável
  let h = 0;
  for (let i = 0; i < chave.length; i++) h = (h * 31 + chave.charCodeAt(i)) % 360;
  return `hsl(${h}, 34%, 62%)`;
}

/* Cor de texto legível (preto/branco) sobre um fundo qualquer */
function textoContraste(cor) {
  // aceita hex ou hsl; para hsl assumimos luminância média -> grafite
  if (cor.startsWith("#")) {
    const r = parseInt(cor.slice(1, 3), 16);
    const g = parseInt(cor.slice(3, 5), 16);
    const b = parseInt(cor.slice(5, 7), 16);
    const lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
    return lum > 0.6 ? "#2B2925" : "#F3F0E9";
  }
  return "#2B2925";
}

/* ============================================================
   GUIA DE PARÂMETROS
   ============================================================ */
let SPEC = [];                    // especificação vinda do servidor
const guiaBox = () => el("#guiaParametros");

function montarGuia(spec) {
  SPEC = spec;
  const box = guiaBox();
  box.innerHTML = "";

  spec.forEach((p) => {
    const linha = document.createElement("div");
    linha.className = "param";
    linha.dataset.chave = p.chave;
    linha.dataset.modo = p.modo || "sempre";

    // 1) rótulo (esquerda)
    const nome = document.createElement("span");
    nome.className = "param__nome";
    nome.textContent = p.rotulo;

    // 2) controle (meio-direita)
    const ctrl = document.createElement("div");
    ctrl.className = "param__ctrl";
    if (p.tipo === "bool") {
      ctrl.innerHTML = `
        <label class="toggle">
          <input type="checkbox" class="in-param" ${p.padrao ? "checked" : ""}>
          <span class="toggle__trilho"></span>
        </label>`;
    } else if (p.tipo === "lista_int") {
      ctrl.innerHTML = `
        <input type="text" class="in-param in-lista" value="${
          Array.isArray(p.padrao) ? p.padrao.join(", ") : p.padrao
        }" placeholder="2, 3, 4">`;
    } else {
      const passo = p.tipo === "float" ? "0.01" : "1";
      const sufixo = p.tipo === "float" ? '<span class="param__sufixo">0–1</span>' : "";
      ctrl.innerHTML = `
        <input type="number" class="in-param" value="${p.padrao}"
               step="${passo}" ${p.min != null ? `min="${p.min}"` : ""}
               ${p.max != null ? `max="${p.max}"` : ""} inputmode="decimal">
        ${sufixo}`;
    }

    // 3) botão "i" (direita) — balão abre para dentro da tela
    const dica = document.createElement("span");
    dica.className = "dica";
    dica.tabIndex = 0;
    dica.setAttribute("role", "button");
    dica.setAttribute("aria-label", `Ajuda sobre ${p.rotulo}`);
    dica.innerHTML = `i<span class="dica__balao" role="tooltip">${p.ajuda}</span>`;

    linha.appendChild(nome);
    linha.appendChild(ctrl);
    linha.appendChild(dica);
    box.appendChild(linha);
  });

  const toggle = box.querySelector('.param[data-chave="parametros_variaveis"] .in-param');
  if (toggle) {
    toggle.addEventListener("change", aplicarEstadoAutomatico);
    aplicarEstadoAutomatico();
  }
}

/*
 * Mostra/oculta e habilita/desabilita os parâmetros conforme o interruptor:
 *  - auto LIGADO  -> valem as FAIXAS (modo "variavel"); os fixos ficam ocultos
 *  - auto DESLIGADO -> valem os valores únicos (modo "fixo"); as faixas ficam ocultas
 *  - modo "sempre" -> aparecem nos dois casos
 */
function aplicarEstadoAutomatico() {
  const box = guiaBox();
  const alvo = box.querySelector('.param[data-chave="parametros_variaveis"] .in-param');
  if (!alvo) return;
  const auto = alvo.checked;
  box.querySelectorAll(".param").forEach((linha) => {
    const modo = linha.dataset.modo;
    let visivel = true;
    if (modo === "fixo") visivel = !auto;
    else if (modo === "variavel") visivel = auto;
    linha.hidden = !visivel;
  });
}

function lerParametros() {
  const box = guiaBox();
  const valores = {};
  SPEC.forEach((p) => {
    const input = box.querySelector(`.param[data-chave="${p.chave}"] .in-param`);
    if (!input) return;
    if (p.tipo === "bool") {
      valores[p.chave] = input.checked;
    } else if (p.tipo === "lista_int") {
      valores[p.chave] = input.value; // backend faz o parse de "2, 3, 4"
    } else {
      const v = parseFloat(input.value);
      valores[p.chave] = Number.isFinite(v) ? v : p.padrao;
    }
  });
  return valores;
}

function restaurarPadroes() {
  const box = guiaBox();
  SPEC.forEach((p) => {
    const input = box.querySelector(`.param[data-chave="${p.chave}"] .in-param`);
    if (!input) return;
    if (p.tipo === "bool") input.checked = !!p.padrao;
    else if (p.tipo === "lista_int")
      input.value = Array.isArray(p.padrao) ? p.padrao.join(", ") : p.padrao;
    else input.value = p.padrao;
  });
  aplicarEstadoAutomatico();
}

async function carregarSpec() {
  try {
    const spec = await chamarWorker("spec", null);
    montarGuia(spec);
  } catch (e) {
    guiaBox().innerHTML =
      '<p class="ajuda">Não foi possível carregar os parâmetros. Recarregue a página.</p>';
  }
}

/* ---------- Linha de peça ---------- */
function criarLinha(dados = {}) {
  contadorLinhas++;
  const linha = document.createElement("div");
  linha.className = "linha-peca";
  linha.dataset.id = contadorLinhas;

  linha.innerHTML = `
    <input type="number" class="in-larg" min="1" inputmode="numeric" value="${dados.largura ?? ""}" aria-label="Largura da peça">
    <input type="number" class="in-alt" min="1" inputmode="numeric" value="${dados.altura ?? ""}" aria-label="Altura da peça">
    <span class="celula-cor">
      <span class="celula-cor__amostra"></span>
      <input type="text" class="in-cor" value="${dados.cor ?? ""}" placeholder="ex: Branco" aria-label="Cor da peça">
    </span>
    <input type="number" class="in-qtd" min="1" inputmode="numeric" value="${dados.quantidade ?? 1}" aria-label="Quantidade">
    <button type="button" class="btn-remover" title="Remover peça" aria-label="Remover peça">×</button>
  `;

  const inCor = linha.querySelector(".in-cor");
  const amostra = linha.querySelector(".celula-cor__amostra");
  const pintar = () => { amostra.style.background = corDeExibicao(inCor.value); };
  inCor.addEventListener("input", pintar);
  pintar();

  linha.querySelector(".btn-remover").addEventListener("click", () => {
    linha.remove();
    if (!linhasPecas.children.length) criarLinha(); // nunca deixa vazio
  });

  linhasPecas.appendChild(linha);
}

// Lê o valor numérico de um campo aceitando vírgula OU ponto como decimal.
function _numero(txt) {
  if (txt == null) return NaN;
  return parseFloat(String(txt).replace(",", "."));
}

// estado: alguma dimensão foi arredondada na última leitura?
let _houveArredondamento = false;

function mostrarAvisoArredondamento() {
  const a = document.getElementById("avisoArredondamento");
  if (a) a.hidden = false;
}
function esconderAvisoArredondamento() {
  const a = document.getElementById("avisoArredondamento");
  if (a) a.hidden = true;
}

function lerPecas() {
  const pecas = [];
  _houveArredondamento = false;
  linhasPecas.querySelectorAll(".linha-peca").forEach((linha) => {
    const lRaw = _numero(linha.querySelector(".in-larg").value);
    const aRaw = _numero(linha.querySelector(".in-alt").value);
    const cor = linha.querySelector(".in-cor").value.trim();
    const qRaw = _numero(linha.querySelector(".in-qtd").value);
    // ignora linhas totalmente vazias
    if (!lRaw && !aRaw && !cor) return;

    const largura = Math.round(lRaw);
    const altura = Math.round(aRaw);
    const quantidade = Math.round(qRaw);
    if (largura !== lRaw || altura !== aRaw || quantidade !== qRaw) {
      _houveArredondamento = true;
    }
    pecas.push({ largura, altura, cor, quantidade });
  });
  return pecas;
}

/* ============================================================
   ARREDONDAMENTO — detecção detalhada + popup
   ============================================================ */

// Varre todos os campos (chapa + peças) e devolve a lista do que será
// arredondado, com referência ao input para poder destacar/corrigir.
function detectarArredondamentos() {
  const itens = [];

  const campos = [
    { input: el("#larguraBin"), nome: "Chapa — largura" },
    { input: el("#alturaBin"), nome: "Chapa — altura" },
  ];
  campos.forEach(({ input, nome }) => {
    const raw = _numero(input.value);
    const arred = Math.round(raw);
    if (Number.isFinite(raw) && arred !== raw) {
      itens.push({ input, nome, de: raw, para: arred });
    }
  });

  let n = 0;
  linhasPecas.querySelectorAll(".linha-peca").forEach((linha) => {
    n++;
    const alvos = [
      { sel: ".in-larg", rot: "largura" },
      { sel: ".in-alt", rot: "altura" },
      { sel: ".in-qtd", rot: "quantidade" },
    ];
    const cor = linha.querySelector(".in-cor").value.trim();
    const lRaw = _numero(linha.querySelector(".in-larg").value);
    const aRaw = _numero(linha.querySelector(".in-alt").value);
    if (!lRaw && !aRaw && !cor) return; // linha vazia
    alvos.forEach(({ sel, rot }) => {
      const input = linha.querySelector(sel);
      const raw = _numero(input.value);
      const arred = Math.round(raw);
      if (Number.isFinite(raw) && arred !== raw) {
        itens.push({ input, nome: `Peça ${n} — ${rot}`, de: raw, para: arred });
      }
    });
  });

  return itens;
}

// Formata número removendo casas inúteis, usando vírgula (padrão BR) na exibição.
function _fmt(n) {
  return String(n).replace(".", ",");
}

// Mostra o popup e resolve com a escolha do usuário:
//   "continuar" | "corrigir" | "cancelar"
function perguntarArredondamento(itens) {
  return new Promise((resolve) => {
    const modal = el("#modalArred");
    const lista = el("#modalArredLista");
    lista.innerHTML = "";
    itens.forEach((it) => {
      const div = document.createElement("div");
      div.className = "modal__item";
      div.innerHTML =
        `<span class="onde">${it.nome}</span>` +
        `<span><span class="de">${_fmt(it.de)}</span> → ` +
        `<span class="para">${_fmt(it.para)}</span></span>`;
      lista.appendChild(div);
    });

    modal.hidden = false;

    const fechar = (escolha) => {
      modal.hidden = true;
      btnCont.removeEventListener("click", onCont);
      btnCorr.removeEventListener("click", onCorr);
      btnCanc.removeEventListener("click", onCanc);
      resolve(escolha);
    };
    const btnCont = el("#modalArredContinuar");
    const btnCorr = el("#modalArredCorrigir");
    const btnCanc = el("#modalArredCancelar");
    const onCont = () => fechar("continuar");
    const onCorr = () => fechar("corrigir");
    const onCanc = () => fechar("cancelar");
    btnCont.addEventListener("click", onCont);
    btnCorr.addEventListener("click", onCorr);
    btnCanc.addEventListener("click", onCanc);
  });
}

// Aplica os valores arredondados nos campos e os destaca visualmente.
function aplicarCorrecoes(itens) {
  itens.forEach((it) => {
    it.input.value = it.para;
    const celula = it.input.closest(".campo, .celula-cor, td, .linha-peca") || it.input.parentElement;
    it.input.classList.add("_arred-alvo");
    const wrap = it.input.parentElement;
    wrap.classList.add("campo-arredondado");
  });
  // rola até o primeiro campo corrigido
  if (itens[0]) {
    itens[0].input.scrollIntoView({ behavior: "smooth", block: "center" });
  }
  // remove o destaque depois de alguns segundos
  setTimeout(() => {
    document.querySelectorAll(".campo-arredondado").forEach((e) =>
      e.classList.remove("campo-arredondado"));
  }, 4000);
}

/* ---------- Desenho de uma chapa (SVG em escala) ---------- */
function desenharChapa(chapa) {
  const W = chapa.largura;
  const H = chapa.altura;

  // viewBox nas unidades reais; deixamos o CSS escalar a largura.
  // Altura proporcional via aspect ratio do próprio viewBox.
  const svgNS = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(svgNS, "svg");
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
  svg.setAttribute("class", "chapa-card__svg");
  svg.setAttribute("preserveAspectRatio", "xMidYMid meet");
  svg.setAttribute("role", "img");
  svg.setAttribute("aria-label",
    `Chapa ${chapa.indice + 1}, cor ${chapa.cor}, ${chapa.pecas.length} peças`);

  const corBase = corDeExibicao(chapa.cor);
  const corTxt = textoContraste(corBase);
  const fonte = Math.max(W, H) * 0.028; // tamanho de rótulo relativo à chapa

  chapa.pecas.forEach((p) => {
    const rect = document.createElementNS(svgNS, "rect");
    rect.setAttribute("x", p.x);
    rect.setAttribute("y", p.y);
    rect.setAttribute("width", p.largura);
    rect.setAttribute("height", p.altura);
    rect.setAttribute("fill", corBase);
    rect.setAttribute("class", "peca-rect");
    svg.appendChild(rect);

    // rótulo só se couber
    if (p.largura > W * 0.06 && p.altura > H * 0.05) {
      const txt = document.createElementNS(svgNS, "text");
      txt.setAttribute("x", p.x + p.largura / 2);
      txt.setAttribute("y", p.y + p.altura / 2);
      txt.setAttribute("text-anchor", "middle");
      txt.setAttribute("dominant-baseline", "central");
      txt.setAttribute("font-size", fonte);
      txt.setAttribute("fill", corTxt);
      txt.setAttribute("class", "peca-txt");
      txt.textContent = `${p.largura}×${p.altura}`;
      svg.appendChild(txt);
    }
  });

  return svg;
}

/* ---------- Renderiza o resultado inteiro ---------- */
let ULTIMO_RESULTADO = null;      // resultado do último cálculo (para downloads)
let ULTIMA_CHAPA = { largura: null, altura: null };

function renderizar(res) {
  ULTIMO_RESULTADO = res;
  ULTIMA_CHAPA = {
    largura: parseInt(el("#larguraBin").value, 10),
    altura: parseInt(el("#alturaBin").value, 10),
  };
  const resumo = el("#resumo");
  const chapasBox = el("#chapas");
  chapasBox.innerHTML = "";

  const r = res.resumo;
  resumo.innerHTML = `
    <div class="resumo__item"><span class="resumo__val">${r.total_chapas}</span><span class="resumo__rot">Chapas</span></div>
    <div class="resumo__item"><span class="resumo__val">${r.total_pecas}</span><span class="resumo__rot">Peças</span></div>
    <div class="resumo__item"><span class="resumo__val">${Math.round(r.aproveitamento_medio * 100)}%</span><span class="resumo__rot">Aproveitamento médio</span></div>
    <div class="resumo__item"><span class="resumo__val">${r.tempo_total_s}s</span><span class="resumo__rot">Tempo de cálculo</span></div>
  `;

  res.chapas.forEach((chapa) => {
    const card = document.createElement("div");
    card.className = "chapa-card";
    const corBase = corDeExibicao(chapa.cor);
    card.innerHTML = `
      <div class="chapa-card__cab">
        <span class="chapa-card__id">Chapa <span class="pon">#</span>${chapa.indice + 1}
          &nbsp;<span class="chapa-card__cor"><span class="amostra" style="background:${corBase}"></span>${chapa.cor}</span>
        </span>
        <span class="chapa-card__aprov">${Math.round(chapa.aproveitamento * 100)}% usado</span>
      </div>
    `;
    card.appendChild(desenharChapa(chapa));
    chapasBox.appendChild(card);
  });

  el("#estadoVazio").hidden = true;
  el("#carregando").hidden = true;
  el("#resultado").hidden = false;
}

/* ---------- Cálculo (roda num Web Worker, não trava a tela) ---------- */
async function resolver() {
  const erroBox = el("#erro");
  erroBox.hidden = true;

  // 1) Antes de calcular: há valores com casas decimais? Se sim, pergunta.
  const arredondamentos = detectarArredondamentos();
  if (arredondamentos.length > 0) {
    const escolha = await perguntarArredondamento(arredondamentos);
    if (escolha === "cancelar") {
      return; // não faz nada
    }
    if (escolha === "corrigir") {
      aplicarCorrecoes(arredondamentos); // aplica na tela e destaca
      return; // deixa o usuário revisar; ele clica calcular de novo quando quiser
    }
    // "continuar": segue com os valores arredondados
    mostrarAvisoArredondamento();
  } else {
    esconderAvisoArredondamento();
  }

  const largura_bin = Math.round(_numero(el("#larguraBin").value));
  const altura_bin = Math.round(_numero(el("#alturaBin").value));
  const parametros = lerParametros();
  const tempo_max = parametros.tempo_max || 10;
  const pecas = lerPecas();

  // Estimativa de tempo p/ avisar o usuário (nº de cores × tempo)
  const cores = new Set(pecas.map((p) => (p.cor || "").toLowerCase())).size || 1;
  el("#carregandoTxt").textContent =
    `Otimizando o corte… (até ~${cores * tempo_max}s, ${cores} cor${cores > 1 ? "es" : ""})`;

  el("#estadoVazio").hidden = true;
  el("#resultado").hidden = true;
  el("#carregando").hidden = false;
  const btn = el("#btnResolver");
  btn.disabled = true;
  _cancelado = false;

  try {
    const dados = await calcularNoWorker({ largura_bin, altura_bin, parametros, pecas });
    if (!dados.ok) {
      throw new Error(dados.erro || "Não foi possível calcular o plano.");
    }
    el("#carregando").hidden = true;
    renderizar(dados);
  } catch (e) {
    el("#carregando").hidden = true;
    // se foi cancelamento do usuário, não mostra erro — só volta ao estado anterior
    if (e.message === "__cancelado__" || _cancelado) {
      if (el("#resultado").hidden) el("#estadoVazio").hidden = false;
    } else {
      if (el("#resultado").hidden) el("#estadoVazio").hidden = false;
      erroBox.textContent = e.message;
      erroBox.hidden = false;
    }
  } finally {
    btn.disabled = false;
    _cancelado = false;
  }
}

/* ============================================================
   IMPORTAÇÃO DE PLANILHA
   ============================================================ */
function preencherTabela(pecas, { substituir = true } = {}) {
  if (substituir) linhasPecas.innerHTML = "";
  pecas.forEach((p) => criarLinha(p));
  if (!linhasPecas.children.length) criarLinha(); // nunca deixa vazio
}

function feedbackImport(msg, erro = false) {
  const box = el("#importFeedback");
  box.textContent = msg;
  box.classList.toggle("import-feedback--erro", erro);
  box.hidden = false;
}

// Reconhecimento tolerante de nomes de coluna (espelha o backend Python).
const _SINONIMOS = {
  largura: ["largura","larg","width","w","comprimento","base"],
  altura: ["altura","alt","height","h","profundidade"],
  cor: ["cor","color","colour","material"],
  quantidade: ["quantidade","qtd","qtde","quant","qty","quantity","demanda"],
};
function _normaliza(t) {
  return String(t == null ? "" : t)
    .normalize("NFKD").replace(/[\u0300-\u036f]/g, "")
    .trim().toLowerCase();
}
function _mapearColunas(cabecalho) {
  const mapa = {};
  cabecalho.forEach((cel, idx) => {
    const nome = _normaliza(cel);
    for (const campo in _SINONIMOS) {
      if (_SINONIMOS[campo].includes(nome) && !(campo in mapa)) mapa[campo] = idx;
    }
  });
  return mapa;
}

async function enviarPlanilha(arquivo) {
  if (!arquivo) return;
  feedbackImport("Lendo a planilha…");
  try {
    const buf = await arquivo.arrayBuffer();
    const wb = XLSX.read(buf, { type: "array" });
    const ws = wb.Sheets[wb.SheetNames[0]];
    const linhas = XLSX.utils.sheet_to_json(ws, { header: 1, blankrows: false });
    if (!linhas.length) throw new Error("A planilha está vazia.");

    const mapa = _mapearColunas(linhas[0]);
    const faltando = ["largura","altura","cor","quantidade"].filter((c) => !(c in mapa));
    if (faltando.length) {
      throw new Error(
        "A planilha precisa ter as colunas: largura, altura, cor, quantidade.\n" +
        "Não encontrei: " + faltando.join(", ") + ".\n" +
        "Baixe a planilha-modelo e use o mesmo formato."
      );
    }

    const pecas = [];
    let ignoradas = 0;
    for (let i = 1; i < linhas.length; i++) {
      const linha = linhas[i];
      const val = (c) => linha[mapa[c]];
      const brutos = ["largura","altura","cor","quantidade"].map(val);
      if (brutos.every((v) => v === undefined || v === "")) continue;
      const preenchidos = brutos.filter((v) => v !== undefined && v !== "");
      if (preenchidos.length < 2) continue;

      const larg = Math.round(Number(val("largura")));
      const alt = Math.round(Number(val("altura")));
      const qtd = Math.round(Number(val("quantidade")));
      const cor = val("cor") != null ? String(val("cor")).trim() : "";
      if (!Number.isFinite(larg) || !Number.isFinite(alt) || !Number.isFinite(qtd) ||
          larg <= 0 || alt <= 0 || qtd <= 0 || !cor) {
        ignoradas++;
        continue;
      }
      pecas.push({ largura: larg, altura: alt, cor, quantidade: qtd });
    }

    if (!pecas.length) {
      throw new Error(
        "Nenhuma peça válida foi encontrada. Verifique se largura, altura e " +
        "quantidade são números maiores que zero e se a cor está preenchida."
      );
    }

    preencherTabela(pecas, { substituir: true });
    let msg = `${pecas.length} peça(s) importada(s) e prontas na tabela.`;
    if (ignoradas > 0) msg += ` ${ignoradas} linha(s) foram ignoradas por dados inválidos.`;
    feedbackImport(msg, false);
  } catch (e) {
    feedbackImport(e.message, true);
  }
}

/* Gera e baixa a planilha-modelo (client-side, SheetJS). */
function baixarModelo() {
  const dados = [
    ["largura", "altura", "cor", "quantidade"],
    [396, 700, "Branco", 4],
    [800, 300, "Branco", 3],
    [500, 500, "Carvalho", 2],
    [250, 450, "Carvalho", 5],
  ];
  const ws = XLSX.utils.aoa_to_sheet(dados);
  ws["!cols"] = [{ wch: 12 }, { wch: 12 }, { wch: 16 }, { wch: 14 }];
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, "Pecas");
  XLSX.writeFile(wb, "modelo_pecas.xlsx");
}

function ligarImportacao() {
  const zona = el("#zonaImport");
  const input = el("#inputPlanilha");

  // clicar abre o seletor (mas não quando clica no link "baixar modelo")
  zona.addEventListener("click", (ev) => {
    if (ev.target.closest("#linkModelo")) return;
    input.click();
  });
  zona.addEventListener("keydown", (ev) => {
    if ((ev.key === "Enter" || ev.key === " ") && !ev.target.closest("a")) {
      ev.preventDefault();
      input.click();
    }
  });

  input.addEventListener("change", () => {
    if (input.files[0]) enviarPlanilha(input.files[0]);
    input.value = ""; // permite reimportar o mesmo arquivo
  });

  // arrastar e soltar
  ["dragenter", "dragover"].forEach((evt) =>
    zona.addEventListener(evt, (ev) => {
      ev.preventDefault();
      zona.classList.add("import--arrastando");
    })
  );
  ["dragleave", "drop"].forEach((evt) =>
    zona.addEventListener(evt, (ev) => {
      ev.preventDefault();
      zona.classList.remove("import--arrastando");
    })
  );
  zona.addEventListener("drop", (ev) => {
    const arquivo = ev.dataTransfer.files && ev.dataTransfer.files[0];
    if (arquivo) enviarPlanilha(arquivo);
  });
}

/* ============================================================
   DOWNLOADS (client-side, sem servidor)
   ============================================================ */
function _cliqueDownload(blob, nomeArquivo) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = nomeArquivo;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

function baixarResultadosXlsx() {
  if (!ULTIMO_RESULTADO) return;
  const res = ULTIMO_RESULTADO;
  // Aba Resumo
  const resumo = [["Chapa", "Cor", "Largura", "Altura", "Nº de peças", "Aproveitamento"]];
  res.chapas.forEach((ch) => {
    resumo.push([ch.indice + 1, ch.cor, ch.largura, ch.altura, ch.pecas.length,
      Math.round(ch.aproveitamento * 100) / 100]);
  });
  // Aba Peças
  const pecas = [["Chapa", "Cor", "Peça (id)", "Largura", "Altura", "X", "Y"]];
  res.chapas.forEach((ch) => {
    ch.pecas.forEach((pc) => {
      pecas.push([ch.indice + 1, ch.cor, pc.id, pc.largura, pc.altura, pc.x, pc.y]);
    });
  });
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet(resumo), "Resumo");
  XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet(pecas), "Peças");
  XLSX.writeFile(wb, "resultados_corte.xlsx");
}

function baixarPlanoHtml() {
  if (!ULTIMO_RESULTADO) return;
  const res = ULTIMO_RESULTADO;
  const W = ULTIMA_CHAPA.largura, H = ULTIMA_CHAPA.altura;
  const agora = new Date().toLocaleString("pt-BR");

  const cards = res.chapas.map((ch) => {
    const corBase = corDeExibicao(ch.cor);
    const svg = svgChapaString(ch);
    return `<section class="card">
      <div class="card-cab">
        <span class="card-id">Chapa #${ch.indice + 1}
          <span class="amostra" style="background:${corBase}"></span>${escapeHtml(ch.cor)}</span>
        <span class="card-aprov">${Math.round(ch.aproveitamento*100)}% usado · ${ch.pecas.length} peças · ${ch.largura}×${ch.altura}</span>
      </div>${svg}
    </section>`;
  }).join("\n");

  const html = `<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Plano de Corte — ${agora}</title><style>
:root{--papel:#E9E3D5;--carta:#F5F1E8;--grafite:#2B2925;--grafite-med:#6B6355;--linha:#C3BAA6;--lapis:#B5462E}
*{box-sizing:border-box}body{margin:0;padding:24px;background:var(--carta);color:var(--grafite);font-family:system-ui,sans-serif}
header{border-bottom:1.5px solid var(--grafite);padding-bottom:12px;margin-bottom:20px}
h1{font-family:Georgia,serif;font-size:1.5rem;margin:0 0 4px}.sub{font-family:monospace;font-size:.8rem;color:var(--grafite-med)}
.resumo{display:flex;flex-wrap:wrap;gap:8px 28px;margin:16px 0 24px;padding:12px 16px;border:1.5px solid var(--grafite);border-radius:3px;background:var(--papel)}
.resumo b{font-family:Georgia,serif;font-size:1.3rem;display:block}.resumo span{font-family:monospace;font-size:.65rem;text-transform:uppercase;letter-spacing:.05em;color:var(--grafite-med)}
.card{margin-bottom:28px;break-inside:avoid}.card-cab{display:flex;justify-content:space-between;align-items:baseline;gap:8px;border-bottom:1px solid var(--linha);padding-bottom:6px;margin-bottom:8px;flex-wrap:wrap}
.card-id{font-family:monospace;font-weight:600;font-size:.9rem}.amostra{display:inline-block;width:12px;height:12px;border-radius:2px;border:1px solid var(--grafite);vertical-align:middle;margin:0 2px}
.card-aprov{font-family:monospace;font-size:.8rem;color:var(--grafite-med)}
.chapa-svg{width:100%;height:auto;max-height:70vh;display:block;border:1.5px solid var(--grafite);border-radius:3px;background:var(--papel)}
.imprimir{position:fixed;top:20px;right:20px;padding:10px 16px;cursor:pointer;font-family:monospace;font-size:.8rem;font-weight:600;background:var(--lapis);color:#FBF3EE;border:none;border-radius:3px}
footer{margin-top:30px;padding-top:12px;border-top:1px solid var(--linha);font-family:monospace;font-size:.7rem;color:var(--grafite-med)}
@media print{.imprimir{display:none}body{padding:0;background:#fff}}
</style></head><body>
<button class="imprimir" onclick="window.print()">Imprimir / Salvar PDF</button>
<header><h1>Plano de Corte</h1><div class="sub">Chapa ${W}×${H} · gerado em ${agora}</div></header>
<div class="resumo">
<div><b>${res.resumo.total_chapas}</b><span>Chapas</span></div>
<div><b>${res.resumo.total_pecas}</b><span>Peças</span></div>
<div><b>${Math.round(res.resumo.aproveitamento_medio*100)}%</b><span>Aproveitamento médio</span></div>
</div>
${cards}
<footer>Gerado pelo otimizador de corte 2D. Cada cor é cortada em chapas separadas.</footer>
</body></html>`;

  _cliqueDownload(new Blob([html], { type: "text/html" }), "plano_de_corte.html");
}

/* Versão string do SVG (para o HTML exportado) */
function svgChapaString(chapa) {
  const W = chapa.largura, H = chapa.altura;
  const corBase = corDeExibicao(chapa.cor);
  const corTxt = textoContraste(corBase);
  const fonte = (Math.max(W, H) * 0.028).toFixed(1);
  let s = `<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="xMidYMid meet" class="chapa-svg" xmlns="http://www.w3.org/2000/svg">`;
  chapa.pecas.forEach((pc) => {
    s += `<rect x="${pc.x}" y="${pc.y}" width="${pc.largura}" height="${pc.altura}" fill="${corBase}" stroke="#2B2925" stroke-width="0.6"/>`;
    if (pc.largura > W * 0.06 && pc.altura > H * 0.05) {
      s += `<text x="${pc.x + pc.largura/2}" y="${pc.y + pc.altura/2}" text-anchor="middle" dominant-baseline="central" font-size="${fonte}" fill="${corTxt}" font-family="monospace">${pc.largura}×${pc.altura}</text>`;
    }
  });
  return s + "</svg>";
}

function escapeHtml(t) {
  return String(t).replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

/* ---------- Início ---------- */
el("#btnAddPeca").addEventListener("click", () => criarLinha());
el("#btnResolver").addEventListener("click", resolver);
el("#btnCancelar").addEventListener("click", () => {
  el("#carregando").hidden = true;
  if (el("#resultado").hidden) el("#estadoVazio").hidden = false;
  el("#btnResolver").disabled = false;
  cancelarExecucao();
});
el("#btnResetParams").addEventListener("click", restaurarPadroes);
el("#btnBaixarPlano").addEventListener("click", baixarPlanoHtml);
el("#btnBaixarResultados").addEventListener("click", baixarResultadosXlsx);
el("#btnLimparPecas").addEventListener("click", () => {
  linhasPecas.innerHTML = "";
  criarLinha();
  el("#importFeedback").hidden = true;
});
el("#linkModelo").addEventListener("click", (ev) => {
  ev.preventDefault();
  baixarModelo();
});
ligarImportacao();
ligarTour();

// Ponto 5: recolher a guia de parâmetros ao clicar fora dela.
document.addEventListener("click", (ev) => {
  const guia = document.querySelector(".recolhivel");
  if (!guia || !guia.open) return;
  // se o clique foi dentro da guia, não faz nada
  if (guia.contains(ev.target)) return;
  guia.open = false;
});

// Ponto 2: ao calcular, evitar que a página "pule" para o topo.
// O clique no botão pode mudar o foco/layout; preservamos a rolagem.
el("#btnResolver").addEventListener("click", () => {
  const y = window.scrollY;
  // restaura a posição no próximo quadro, caso algo tenha rolado
  requestAnimationFrame(() => window.scrollTo({ top: y }));
});

// Peças de exemplo para o primeiro contato (marcenaria: portas + prateleiras)
criarLinha({ largura: 396, altura: 700, cor: "Branco", quantidade: 4 });
criarLinha({ largura: 800, altura: 300, cor: "Branco", quantidade: 3 });
criarLinha({ largura: 500, altura: 500, cor: "Carvalho", quantidade: 2 });

// Inicia o Python (no worker) e, quando pronto, carrega os parâmetros.
iniciarPython().then(() => {
  if (PY_PRONTO) carregarSpec();
});

/* ============================================================
   TOUR GUIADO (manual de uso passo a passo)
   Overlay que destaca cada parte da tela e explica o que faz.
   Roda sozinho na primeira visita; pode ser revisto pelo botão "Como usar".
   ============================================================ */
const TOUR_PASSOS = [
  {
    alvo: null,
    titulo: "Bem-vindo ao Plano de Corte!",
    texto: "Este programa calcula como cortar suas chapas aproveitando o máximo " +
           "do material. Vou te mostrar rapidamente como usar. Leva menos de um minuto.",
  },
  {
    alvo: "#tit-entrada",
    posicao: "baixo",
    titulo: "1. A chapa",
    texto: "Comece informando o tamanho da sua chapa: largura e altura. Use sempre " +
           "a mesma unidade para tudo (recomendamos milímetros).",
  },
  {
    alvo: "#zonaImport",
    posicao: "baixo",
    titulo: "2. As peças — por planilha",
    texto: "Se você tem muitas peças, baixe a planilha-modelo, preencha no Excel e " +
           "arraste aqui. A tabela é preenchida sozinha. Também dá para digitar à mão.",
  },
  {
    alvo: "#linhasPecas",
    posicao: "baixo",
    titulo: "2. As peças — à mão",
    texto: "Cada linha é uma peça: largura, altura, cor e quantidade. Peças de cores " +
           "diferentes são cortadas em chapas separadas, como na produção real.",
  },
  {
    alvo: ".recolhivel",
    posicao: "cima",
    titulo: "3. Parâmetros (opcional)",
    texto: "Aqui você ajusta como o algoritmo trabalha. Não precisa mexer — os valores " +
           "padrão funcionam bem. Toque no 'i' de cada item para entender o que faz.",
  },
  {
    alvo: "#btnResolver",
    posicao: "cima",
    titulo: "4. Calcular",
    texto: "Quando terminar, clique aqui. O programa desenha o plano de corte de cada " +
           "chapa, mostrando onde fica cada peça.",
  },
  {
    alvo: ".painel--saida",
    posicao: "esquerda",
    titulo: "5. O resultado",
    texto: "O desenho de cada chapa aparece aqui, em escala. Você pode baixar o plano " +
           "de corte (para imprimir) e uma planilha com os resultados.",
  },
  {
    alvo: "#btnAjuda",
    posicao: "baixo",
    titulo: "Pronto!",
    texto: "É só isso. Sempre que quiser rever esta explicação, clique em 'Como usar' " +
           "aqui no topo. Bom trabalho!",
  },
];

let _tourIdx = 0;

function _tourEls() {
  return {
    overlay: document.getElementById("tourOverlay"),
    buraco: document.getElementById("tourBuraco"),
    balao: document.getElementById("tourBalao"),
    titulo: document.getElementById("tourTitulo"),
    texto: document.getElementById("tourTexto"),
    contador: document.getElementById("tourContador"),
    btnProx: document.getElementById("tourProx"),
    btnFechar: document.getElementById("tourFechar"),
  };
}

function iniciarTour() {
  _tourIdx = 0;
  document.getElementById("tourOverlay").hidden = false;
  mostrarPassoTour();
}

function fecharTour() {
  document.getElementById("tourOverlay").hidden = true;
  try { localStorage.setItem("tourVisto", "1"); } catch (e) {}
}

function mostrarPassoTour() {
  const els = _tourEls();
  const passo = TOUR_PASSOS[_tourIdx];

  els.titulo.textContent = passo.titulo;
  els.texto.textContent = passo.texto;
  els.contador.textContent = `${_tourIdx + 1} de ${TOUR_PASSOS.length}`;
  els.btnProx.textContent = _tourIdx === TOUR_PASSOS.length - 1 ? "Concluir" : "Seguinte →";

  const alvo = passo.alvo ? document.querySelector(passo.alvo) : null;
  if (alvo) {
    alvo.scrollIntoView({ behavior: "smooth", block: "center" });
    // pequeno atraso para o scroll assentar antes de medir
    setTimeout(() => posicionarDestaque(alvo, passo.posicao), 300);
  } else {
    // passo sem alvo: destaque some, balão centralizado
    els.buraco.style.opacity = "0";
    els.balao.style.left = "50%";
    els.balao.style.top = "50%";
    els.balao.style.transform = "translate(-50%, -50%)";
    els.balao.className = "tour-balao";
  }
}

function posicionarDestaque(alvo, posicao) {
  const els = _tourEls();
  const r = alvo.getBoundingClientRect();
  const pad = 8;

  // "buraco" que destaca o elemento
  els.buraco.style.opacity = "1";
  els.buraco.style.left = `${r.left - pad}px`;
  els.buraco.style.top = `${r.top - pad}px`;
  els.buraco.style.width = `${r.width + pad * 2}px`;
  els.buraco.style.height = `${r.height + pad * 2}px`;

  const balao = els.balao;
  balao.style.transform = "none";
  const bw = 300, gap = 16;
  const vh = window.innerHeight, vw = window.innerWidth;

  // mede a altura real do balão (com o conteúdo do passo já preenchido)
  balao.className = "tour-balao";
  balao.style.left = "0px";
  balao.style.top = "0px";
  const bh = balao.offsetHeight || 180;

  const espacoAbaixo = vh - r.bottom;
  const espacoAcima = r.top;

  posicao = posicao || "baixo";
  // auto-flip vertical: se pediu "baixo" mas não cabe, e cabe acima, vira "cima"
  if (posicao === "baixo" && espacoAbaixo < bh + gap + 12 && espacoAcima > espacoAbaixo) {
    posicao = "cima";
  } else if (posicao === "cima" && espacoAcima < bh + gap + 12 && espacoAbaixo > espacoAcima) {
    posicao = "baixo";
  }

  let left, top, classe;
  if (posicao === "baixo") {
    left = Math.min(Math.max(r.left, 12), vw - bw - 12);
    top = r.bottom + gap;
    classe = "seta-cima";
  } else if (posicao === "cima") {
    left = Math.min(Math.max(r.left, 12), vw - bw - 12);
    top = r.top - gap;
    balao.style.transform = "translateY(-100%)";
    classe = "seta-baixo";
  } else if (posicao === "esquerda") {
    left = Math.max(r.left - bw - gap, 12);
    top = Math.max(Math.min(r.top, vh - bh - 12), 12);
    classe = "seta-direita";
  } else {
    left = r.right + gap;
    top = Math.max(Math.min(r.top, vh - bh - 12), 12);
    classe = "seta-esquerda";
  }

  // garantia final: nunca deixa o balão sair por cima da tela
  if (posicao !== "cima" && top + bh > vh - 8) top = Math.max(8, vh - bh - 8);
  if (top < 8 && posicao !== "cima") top = 8;

  balao.style.left = `${left}px`;
  balao.style.top = `${top}px`;
  balao.className = "tour-balao " + classe;
}

function ligarTour() {
  const els = _tourEls();
  els.btnProx.addEventListener("click", () => {
    if (_tourIdx < TOUR_PASSOS.length - 1) {
      _tourIdx++;
      mostrarPassoTour();
    } else {
      fecharTour();
    }
  });
  els.btnFechar.addEventListener("click", fecharTour);
  // recalcula posição se a janela mudar de tamanho durante o tour
  window.addEventListener("resize", () => {
    if (!els.overlay.hidden) mostrarPassoTour();
  });
  document.getElementById("btnAjuda").addEventListener("click", iniciarTour);

  // roda automaticamente na primeira visita
  let visto = null;
  try { visto = localStorage.getItem("tourVisto"); } catch (e) {}
  if (!visto) {
    // espera a interface montar antes de iniciar
    setTimeout(iniciarTour, 800);
  }
}
