import random
import sys

from empacotador.item import Item

class LeitorDeItens:
    """
    Converte dados de entrada em objetos Item.
    """

    def __init__(self, dados_brutos, forma_de_ordenamento = None):
        """
        dados_brutos pode ser:
        - lista
        - dict
        - arquivo
        - instância clássica

        Forma de ordenamento pode ser:
         - 'H' 
         - 'W'
         - 'Random'
         - None    #Default
        """

        #Os meus leitores de arquivos de corte e empacotamento entrarão aqui no futuro
        #Por exemplo, se a extensão do arquivo for .bpp vai em uma função

        #Armazena os dados brutos
        if forma_de_ordenamento == 'H':
            self.dados_brutos = self.ordenar_por_H(dados_brutos) #ordenamento dos dados
        elif forma_de_ordenamento == 'W':
            self.dados_brutos = self.ordenar_por_W(dados_brutos)
        elif forma_de_ordenamento == "area_Des":
            self.dados_brutos = self.ordenar_por_area(dados_brutos, decrescente=True)
        elif forma_de_ordenamento == "area_As":
            self.dados_brutos = self.ordenar_por_area(dados_brutos, decrescente=False)
        elif forma_de_ordenamento == 'Random':
            self.dados_brutos = self.ordenar_random(dados_brutos)

        elif forma_de_ordenamento == 'perimetro':
            self.dados_brutos = sorted(
                dados_brutos,
                key=lambda tup: 2 * (tup[0] + tup[1]),
                reverse=True
            )
        elif forma_de_ordenamento == 'ratio_Des':
            self.dados_brutos = sorted(
                dados_brutos,
                key=lambda tup: tup[1] / tup[0],  # H/W
                reverse=True
            )
        elif forma_de_ordenamento == 'ratio_As':
            self.dados_brutos = sorted(
                dados_brutos,
                key=lambda tup: tup[1] / tup[0],
                reverse=False
            )
        elif forma_de_ordenamento == None:
            self.dados_brutos = dados_brutos
        else:
            print("ERRO, O ORDENAMENTO DOS ITENS DEVE SER POR: LARGURA 'w' OU COMPRIMENTO 'h'")
            print("   -Altura -> 'H'")
            print("   -Largura -> 'W'")
            print("   -Aleatório -> 'Random'")
            print("   -Formato inicial -> None ->(Não ordena, Default)")
            sys.exit()
    
    def ordenar_por_W(self, dados_brutos):
        """
            Ordena os itens por largura W

            Dados de entrada: dados no formato: [[Largura, Altura, Demanda], [Largura, Altura, Demanda], ...]
        """

        dados_brutos.sort(key=lambda tup: tup[0], reverse=True)
        return dados_brutos 

    def ordenar_por_H(self, dados_brutos):
        """
            Ordena os itens por altura H

            Dados de entrada: dados no formato: [[Largura, Altura, Demanda], [Largura, Altura, Demanda], ...]
        """
        dados_brutos.sort(key=lambda tup: tup[1], reverse=True)
        return dados_brutos
    
    def ordenar_por_area(self, dados_brutos, decrescente = True):
        """
        Ordena os itens por área (do maior para o menor é default)
        """
        dados_brutos.sort(key=lambda tup: tup[1] * tup[0], reverse=decrescente)
        return dados_brutos
    
    def ordenar_random(self, dados_brutos):
        random.shuffle(dados_brutos)  # embaralha
        return dados_brutos

        

    def criar_itens(self):
        """
        Retorna uma lista de objetos Item.
        """
        itens = [] #Vai guardar todos os itens criados

        id_item = 0

        for (largura, altura, demanda) in self.dados_brutos:
            for _ in range(demanda):
                
                item = Item(
                    largura = largura,
                    altura = altura,
                    id_item = id_item
                )
                itens.append(item)
                id_item += 1

        return itens
