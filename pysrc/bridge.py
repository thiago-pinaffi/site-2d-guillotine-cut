"""
bridge.py — ponte entre o JavaScript (navegador) e o núcleo Python.

Roda dentro do Pyodide. O JavaScript chama estas funções e recebe strings JSON,
que são fáceis de transportar através da fronteira JS<->Python.
"""

import json

import solver_api
import parametros_spec


def obter_spec_parametros():
    """Devolve a especificação dos parâmetros como string JSON."""
    return json.dumps(parametros_spec.spec_publico())


def resolver_json(largura_bin, altura_bin, pecas_json, parametros_json):
    """
    Recebe os dados como JSON (strings), resolve e devolve o resultado como
    string JSON. Erros de validação viram {"ok": false, "erro": "..."}.
    """
    try:
        pecas = json.loads(pecas_json)
        parametros = json.loads(parametros_json) if parametros_json else {}
        resultado = solver_api.resolver(
            largura_bin=int(largura_bin),
            altura_bin=int(altura_bin),
            pecas=pecas,
            parametros=parametros,
        )
        return json.dumps(resultado)
    except ValueError as e:
        return json.dumps({"ok": False, "erro": str(e)})
    except Exception as e:  # segurança
        return json.dumps({"ok": False, "erro": f"Erro inesperado: {e}"})
