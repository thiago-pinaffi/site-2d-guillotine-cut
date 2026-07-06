"""
solver_api.py
=============
Camada de aplicação que conecta a interface ao algoritmo genético.

Responsabilidades:
  1. Receber os dados do jeito que um usuário informa (bin + lista de peças com cor).
  2. Aplicar a RESTRIÇÃO DE COR: peças de cores diferentes nunca compartilham a
     mesma chapa. Cada cor é resolvida separadamente e os bins são somados.
  3. Devolver o resultado como um dicionário 100% serializável em JSON, com as
     coordenadas de cada peça já calculadas, pronto para desenhar na tela.

O núcleo (empacotador + algoritmo genético) NÃO é modificado por este arquivo.
"""

import io
import time
import contextlib

from algoritmo_genetico.algoritmo_genetico import AlgoritmoGenetico
from parametros_spec import aplicar_parametros


# ---------------------------------------------------------------------------
# Validação da entrada
# ---------------------------------------------------------------------------

def validar_entrada(largura_bin, altura_bin, pecas):
    """
    Confere se os dados fazem sentido antes de gastar tempo processando.
    Levanta ValueError com uma mensagem clara (que a interface pode exibir).

    pecas: lista de dicts no formato
        {"largura": int, "altura": int, "cor": str, "quantidade": int}
    """
    erros = []

    if largura_bin <= 0 or altura_bin <= 0:
        erros.append("As dimensões da chapa (bin) devem ser maiores que zero.")

    if not pecas:
        erros.append("Inclua pelo menos uma peça.")

    for i, p in enumerate(pecas, start=1):
        w = p.get("largura")
        h = p.get("altura")
        q = p.get("quantidade")
        cor = p.get("cor")

        if w is None or h is None or q is None:
            erros.append(f"Peça {i}: faltam dados (largura, altura ou quantidade).")
            continue
        if w <= 0 or h <= 0:
            erros.append(f"Peça {i}: largura e altura devem ser maiores que zero.")
        if q <= 0:
            erros.append(f"Peça {i}: a quantidade deve ser pelo menos 1.")
        if not cor or not str(cor).strip():
            erros.append(f"Peça {i}: informe uma cor.")
        # Peça não pode ser maior que a chapa (senão o empacotador quebra)
        if w is not None and h is not None and (w > largura_bin or h > altura_bin):
            erros.append(
                f"Peça {i} ({w}x{h}) é maior que a chapa "
                f"({largura_bin}x{altura_bin}) e nunca caberia."
            )

    if erros:
        raise ValueError("\n".join(erros))


# ---------------------------------------------------------------------------
# Agrupamento por cor (a restrição física)
# ---------------------------------------------------------------------------

def agrupar_por_cor(pecas):
    """
    Agrupa as peças por cor, preservando a ordem de aparição das cores.

    Retorna: dict {cor: [[largura, altura, demanda], ...]}
    (esse [[l, a, d], ...] é exatamente o formato que o GA espera como instância)
    """
    grupos = {}
    for p in pecas:
        cor = str(p["cor"]).strip()
        grupos.setdefault(cor, []).append(
            [round(float(p["largura"])), round(float(p["altura"])),
             round(float(p["quantidade"]))]
        )
    return grupos


# ---------------------------------------------------------------------------
# Serialização da solução (Bin -> dict simples)
# ---------------------------------------------------------------------------

def _bin_para_dict(bin_obj, cor, indice_global):
    """
    Achata um objeto Bin numa estrutura simples para JSON, extraindo a lista de
    peças já com coordenadas (x, y, largura, altura).
    """
    pecas_no_bin = []
    for faixa_2 in bin_obj.faixas_2:
        for faixa_3 in faixa_2.faixas_3:
            for item in faixa_3.itens:
                pecas_no_bin.append({
                    "id": item.id_item,
                    "x": item.coord_x,
                    "y": item.coord_y,
                    "largura": item.largura,
                    "altura": item.altura,
                })

    area_bin = bin_obj.largura * bin_obj.altura
    area_usada = sum(pc["largura"] * pc["altura"] for pc in pecas_no_bin)
    aproveitamento = (area_usada / area_bin) if area_bin else 0.0

    return {
        "indice": indice_global,          # número da chapa no resultado geral
        "cor": cor,
        "largura": bin_obj.largura,
        "altura": bin_obj.altura,
        "aproveitamento": round(aproveitamento, 4),  # 0..1
        "pecas": pecas_no_bin,
    }


# ---------------------------------------------------------------------------
# Função principal chamada pela interface
# ---------------------------------------------------------------------------

def resolver(largura_bin, altura_bin, pecas, parametros=None, callback_cor=None):
    """
    Resolve o problema completo respeitando a restrição de cor.

    Parâmetros:
        largura_bin, altura_bin : dimensões da chapa
        pecas    : lista de dicts {largura, altura, cor, quantidade}
        parametros: dict opcional {chave: valor} para configurar o algoritmo
                    (ver parametros_spec.PARAMETROS). O que não vier usa o padrão
                    do núcleo. Inclui 'tempo_max' (critério de parada por cor).
        callback_cor: função opcional chamada a cada cor concluída,
                      recebendo (cor, indice, total_cores) — útil p/ barra de progresso

    Retorna um dict serializável:
        {
          "ok": True,
          "resumo": {
              "total_chapas": int,
              "total_pecas": int,
              "aproveitamento_medio": float (0..1),
              "tempo_total_s": float
          },
          "por_cor": { cor: {"chapas": int, "pecas": int} },
          "chapas": [ {indice, cor, largura, altura, aproveitamento, pecas:[...]}, ... ]
        }
    """
    validar_entrada(largura_bin, altura_bin, pecas)

    dimensoes_bin = [round(float(largura_bin)), round(float(altura_bin))]
    grupos = agrupar_por_cor(pecas)

    chapas = []
    por_cor = {}
    indice_global = 0
    t0 = time.perf_counter()

    total_cores = len(grupos)
    for i, (cor, instancia) in enumerate(grupos.items(), start=1):
        ga = AlgoritmoGenetico(
            instancia=[list(x) for x in instancia],  # cópia defensiva
            dimensoes_bin=dimensoes_bin,
            report=False,
        )
        # Aplica a configuração do usuário sobre os parâmetros do núcleo.
        aplicar_parametros(ga.parametros, parametros)
        # O núcleo imprime algumas mensagens de depuração no stdout; como não o
        # alteramos, apenas silenciamos essa saída aqui para manter a API limpa.
        with contextlib.redirect_stdout(io.StringIO()):
            ga.executar(stop_time=True)

        melhor = ga.melhor_individuo
        pecas_da_cor = 0
        for bin_obj in melhor.solucao:
            chapa = _bin_para_dict(bin_obj, cor, indice_global)
            chapas.append(chapa)
            pecas_da_cor += len(chapa["pecas"])
            indice_global += 1

        por_cor[cor] = {
            "chapas": melhor.num_bins,
            "pecas": pecas_da_cor,
        }

        if callback_cor is not None:
            callback_cor(cor, i, total_cores)

    tempo_total = time.perf_counter() - t0
    total_pecas = sum(info["pecas"] for info in por_cor.values())
    aprov_medio = (
        sum(ch["aproveitamento"] for ch in chapas) / len(chapas)
        if chapas else 0.0
    )

    return {
        "ok": True,
        "resumo": {
            "total_chapas": len(chapas),
            "total_pecas": total_pecas,
            "aproveitamento_medio": round(aprov_medio, 4),
            "tempo_total_s": round(tempo_total, 2),
        },
        "por_cor": por_cor,
        "chapas": chapas,
    }
