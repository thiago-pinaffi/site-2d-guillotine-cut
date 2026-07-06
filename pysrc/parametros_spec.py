"""
parametros_spec.py
==================
Fonte única de verdade sobre os parâmetros do algoritmo genético.

Cada entrada descreve UM parâmetro do ParametrosGA: rótulo amigável, valor
padrão (lido do próprio núcleo), faixa aceitável, texto de ajuda (o "i"), e o
MODO em que ele vale:

    modo = "sempre"    -> sempre editável
    modo = "fixo"      -> só vale com "Ajuste automático" DESLIGADO
    modo = "variavel"  -> só vale com "Ajuste automático" LIGADO

Com o ajuste automático LIGADO, o algoritmo regula sozinho, ao longo da
execução, a probabilidade de cruzamento/mutação, o tamanho da população e a
elite — e para isso usa as faixas (_min/_max). Com ele DESLIGADO, usa os valores
fixos únicos. Por isso os dois conjuntos existem, mas só um vale por vez.

Tanto o backend (validação/aplicação) quanto a interface (formulário + tooltips)
consomem esta mesma lista, para nunca ficarem fora de sincronia.
"""

from algoritmo_genetico.parametros_ga import ParametrosGA

# Instância só para ler os valores padrão reais do núcleo.
_PADRAO = ParametrosGA()


def _p(chave, rotulo, tipo, ajuda, modo="sempre", minimo=None, maximo=None, padrao=None):
    if padrao is None:
        padrao = getattr(_PADRAO, chave)
    return {
        "chave": chave, "rotulo": rotulo, "tipo": tipo, "ajuda": ajuda,
        "modo": modo, "min": minimo, "max": maximo, "padrao": padrao,
    }


PARAMETROS = [
    # ---- Interruptor mestre ----
    _p("parametros_variaveis", "Ajuste automático de parâmetros", "bool",
       "Quando LIGADO, o algoritmo regula sozinho, ao longo da execução, a "
       "probabilidade de cruzamento e de mutação, o tamanho da população e a "
       "elite. Nesse modo valem as FAIXAS (mínimo/máximo). DESLIGUE para fixar "
       "você mesmo os valores únicos.",
       modo="sempre"),

    # ---- Parada ----
    _p("tempo_max", "Tempo por cor (s)", "int",
       "Critério de parada: por quantos segundos o algoritmo trabalha em CADA cor "
       "antes de entregar o melhor resultado. Mais tempo tende a usar menos chapas, "
       "com retorno cada vez menor. Principal botão de rapidez x qualidade.",
       modo="sempre", minimo=1, maximo=86400),
    _p("num_geracoes", "Máximo de gerações", "int",
       "Outro critério de parada: número máximo de gerações. O padrão é bem alto, "
       "deixando o TEMPO ser o limite prático. Reduza para travar por número de "
       "gerações em vez de por tempo.",
       modo="sempre", minimo=1, maximo=1000000000),

    # ---- Valores fixos (só com auto DESLIGADO) ----
    _p("prob_crossover", "Probabilidade de cruzamento", "float",
       "Chance de combinar duas soluções-pais para gerar um filho (misturar bons "
       "pedaços de corte). 0 a 1. Vale apenas com o ajuste automático DESLIGADO.",
       modo="fixo", minimo=0.0, maximo=1.0),
    _p("prob_mutacao", "Probabilidade de mutação", "float",
       "Chance de embaralhar levemente a ordem das peças, introduzindo novidade e "
       "evitando ficar preso numa resposta ruim. 0 a 1. Vale apenas com o ajuste "
       "automático DESLIGADO.",
       modo="fixo", minimo=0.0, maximo=1.0),
    _p("tamanho_populacao", "Tamanho da população", "int",
       "Quantas soluções candidatas existem a cada geração. Maior = explora mais, "
       "porém mais lento. Vale apenas com o ajuste automático DESLIGADO.",
       modo="fixo", minimo=2, maximo=1000),
    _p("percent_ind_elite", "Fração de elite (%)", "float",
       "Fatia das melhores soluções que passam intactas para a próxima geração. "
       "Fração de 0 a 1 (0,2 = 20%). Vale apenas com o ajuste automático DESLIGADO.",
       modo="fixo", minimo=0.0, maximo=1.0),

    # ---- Faixas variáveis (só com auto LIGADO) ----
    _p("prob_crossover_min", "Cruzamento - mínimo", "float",
       "Limite inferior da probabilidade de cruzamento com o ajuste automático "
       "LIGADO. O valor varia entre este mínimo e o máximo ao longo da execução.",
       modo="variavel", minimo=0.0, maximo=1.0),
    _p("prob_crossover_max", "Cruzamento - máximo", "float",
       "Limite superior da probabilidade de cruzamento com o ajuste automático LIGADO.",
       modo="variavel", minimo=0.0, maximo=1.0),
    _p("prob_mutacao_min", "Mutação - mínimo", "float",
       "Limite inferior da probabilidade de mutação com o ajuste automático LIGADO.",
       modo="variavel", minimo=0.0, maximo=1.0),
    _p("prob_mutacao_max", "Mutação - máximo", "float",
       "Limite superior da probabilidade de mutação com o ajuste automático LIGADO.",
       modo="variavel", minimo=0.0, maximo=1.0),
    _p("populacao_min", "População - mínimo", "int",
       "Menor tamanho de população usado com o ajuste automático LIGADO.",
       modo="variavel", minimo=2, maximo=1000),
    _p("populacao_max", "População - máximo", "int",
       "Maior tamanho de população usado com o ajuste automático LIGADO.",
       modo="variavel", minimo=2, maximo=1000),
    _p("percent_ind_elite_min", "Elite - mínimo (%)", "float",
       "Menor fração de elite usada com o ajuste automático LIGADO. 0 a 1.",
       modo="variavel", minimo=0.0, maximo=1.0),
    _p("percent_ind_elite_max", "Elite - máximo (%)", "float",
       "Maior fração de elite usada com o ajuste automático LIGADO. 0 a 1.",
       modo="variavel", minimo=0.0, maximo=1.0),

    # ---- Cruzamento (sempre) ----
    _p("percent_bins_elite", "Fração de chapas-elite (%)", "float",
       "No cruzamento, fatia das melhores CHAPAS dos pais copiadas inteiras para o "
       "filho antes de reencaixar o resto. Preserva blocos bem resolvidos. 0 a 1.",
       modo="sempre", minimo=0.0, maximo=1.0),
    _p("percent_faixas_elite", "Fração de faixas-elite (%)", "float",
       "Ainda no cruzamento, depois das chapas-elite, fatia de peças herdada das "
       "melhores FAIXAS (fileiras de corte) dos pais. 0 a 1.",
       modo="sempre", minimo=0.0, maximo=1.0),

    # ---- Seleção de pais (sempre) ----
    _p("percent_ind_TOP", "Faixa TOP na seleção (%)", "float",
       "Um dos pais vem sempre do grupo dos melhores (TOP). Define o tamanho do "
       "grupo, como fração da população. Menor = pressão seletiva mais forte. 0 a 1.",
       modo="sempre", minimo=0.0, maximo=1.0),
    _p("percent_ind_MID", "Faixa MID na seleção (%)", "float",
       "Tamanho do grupo do MEIO (fração da população), de onde sai o segundo pai. 0 a 1.",
       modo="sempre", minimo=0.0, maximo=1.0),
    _p("percent_ind_BOT", "Faixa BOT na seleção (%)", "float",
       "Fatia dos PIORES indivíduos, descartada ao sortear o segundo pai. Fração da "
       "população, 0 a 1.",
       modo="sempre", minimo=0.0, maximo=1.0),

    # ---- Destroy & repair (sempre) ----
    _p("prob_DR", "Probabilidade de destruir-e-reconstruir", "float",
       "Chance de aplicar a busca 'destroy-and-repair': remover algumas chapas de "
       "uma boa solução e reencaixar as peças do zero, buscando compactar. Poderoso, "
       "porém custoso. 0 a 1.",
       modo="sempre", minimo=0.0, maximo=1.0),
    _p("DR_top_individuos", "Destruir: alvo entre os melhores (%)", "float",
       "Ao aplicar destroy-and-repair, o alvo é sorteado entre esta fatia dos "
       "melhores indivíduos. Fração da população, 0 a 1 (0,3 = top 30%).",
       modo="sempre", minimo=0.0, maximo=1.0),
    _p("DR_k", "Destruir: nº de chapas removidas", "lista_int",
       "Quantas chapas são destruídas por vez. O algoritmo sorteia um valor desta "
       "lista (padrão 2, 3 ou 4). Informe números separados por vírgula.",
       modo="sempre"),

    # ---- Injeção de diversidade / convergência (sempre) ----
    _p("Inj_Diversidade_TOP", "Diversidade: nº de melhores comparados", "int",
       "Para decidir se a população estagnou (e injetar diversidade), o algoritmo "
       "compara os N melhores indivíduos. Este é o N.",
       modo="sempre", minimo=1, maximo=100),
    _p("Inj_Diversidade_percent_diferenca", "Diversidade: tolerância (%)", "float",
       "Quão parecidos os melhores precisam estar (em área livre, como fração da "
       "chapa) para serem considerados estagnados. 0,05 = 5%. 0 a 1.",
       modo="sempre", minimo=0.0, maximo=1.0),

    # ---- Restart parcial (sempre) ----
    _p("num_max_iteracoes_sem_melhoria", "Restart: gerações sem melhoria", "int",
       "Se o melhor resultado não melhora por este número de gerações, o algoritmo "
       "faz um 'restart parcial' para escapar de um ótimo local.",
       modo="sempre", minimo=1, maximo=100000),
    _p("proporcao_tempo_max_sem_melhoria", "Restart: gatilho por tempo (fração)", "float",
       "Também dispara o restart parcial quando o tempo decorrido atinge esta fração "
       "do tempo total por cor. 0,2 = 20%. 0 a 1.",
       modo="sempre", minimo=0.0, maximo=1.0),
    _p("individuos_para_manter_em_restart_parcial", "Restart: indivíduos preservados", "int",
       "Quantos dos melhores indivíduos sobrevivem a um restart parcial; o resto da "
       "população é regenerado.",
       modo="sempre", minimo=1, maximo=1000),
]

_POR_CHAVE = {p["chave"]: p for p in PARAMETROS}


def spec_publico():
    """Versão da spec para enviar ao navegador (JSON serializável)."""
    return PARAMETROS


def aplicar_parametros(param_ga, valores):
    """
    Aplica um dict {chave: valor} vindo da interface sobre uma instância de
    ParametrosGA, com segurança:
      - só aceita chaves conhecidas (ignora o resto);
      - respeita tipo e faixa [min, max] de cada parâmetro (clamp);
      - 'lista_int' aceita lista ou string "2,3,4";
      - recalcula n_ind_elite quando muda população ou fração de elite.
    'valores' pode ser None ou parcial - o que não vier fica no padrão do núcleo.
    """
    if not valores:
        return param_ga

    for chave, bruto in valores.items():
        spec = _POR_CHAVE.get(chave)
        if spec is None:
            continue

        tipo = spec["tipo"]
        if tipo == "bool":
            valor = bool(bruto)
        elif tipo == "lista_int":
            valor = _parse_lista_int(bruto)
            if not valor:
                continue
        else:
            try:
                valor = float(bruto)
            except (TypeError, ValueError):
                continue
            if tipo == "int":
                valor = int(round(valor))
            lo, hi = spec.get("min"), spec.get("max")
            if lo is not None:
                valor = max(lo, valor)
            if hi is not None:
                valor = min(hi, valor)

        setattr(param_ga, chave, valor)

    param_ga.n_ind_elite = max(
        1, int(param_ga.tamanho_populacao * param_ga.percent_ind_elite)
    )
    return param_ga


def _parse_lista_int(bruto):
    """Aceita [2,3,4] ou '2, 3, 4' e devolve lista de inteiros >= 1."""
    if isinstance(bruto, (list, tuple)):
        itens = bruto
    else:
        itens = str(bruto).replace(";", ",").split(",")
    out = []
    for x in itens:
        try:
            n = int(round(float(x)))
            if n >= 1:
                out.append(n)
        except (TypeError, ValueError):
            continue
    return out
