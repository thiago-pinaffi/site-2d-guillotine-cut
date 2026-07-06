"""
desenhador.py — versão leve para a web.

No site, o desenho das chapas é feito pelo navegador (SVG), não pelo
matplotlib. O algoritmo genético só usa o Desenhador quando report=True, o
que não acontece nesta interface (roda sempre com report=False). Este stub
existe apenas para satisfazer o import, sem carregar o matplotlib (pesado)
no navegador.

A versão completa (com matplotlib) está em src/utilitarios/desenhador.py no
repositório, para uso local/desktop.
"""


class Desenhador:
    def __init__(self, bin=None, *args, **kwargs):
        self.bin = bin

    def desenhar_solucao(self, *args, **kwargs):
        # Sem efeito na web (o desenho é feito em SVG pelo navegador).
        return None

    def imprimir(self, *args, **kwargs):
        return None
