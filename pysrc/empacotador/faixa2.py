from .faixa3 import Faixa3
class Faixa2:
    """
    Representa uma faixa de nível 2 (estágio 2 de corte).
    É uma região horizontal dentro de um bin.
    Responsável por criar e gerenciar faixas de nível 3.
    """

    def __init__(self, largura, altura, coord_y, id_faixa2=None):
        """
        Inicializa a faixa 2 com dimensões fixas
        e posição vertical dentro do bin.
        """
        self.id_faixa2 = id_faixa2

        # Geometria
        self.largura = largura
        self.altura = altura
        self.coord_y = coord_y

        # Estrutura interna
        self.faixas_3 = []

        # Controle interno
        self.altura_usada = 0
        self.largura_disponivel = largura

        # Métrica agregada
        self.ocupacao = 0.0
        self.area_ocupada = 0.0

        #tirar no futuro, é apenas para teste
        self.itens = []

    def clonar(self):
        faixa_2_clone = Faixa2(
            largura= self.largura,
            altura = self.altura,
            coord_y= 0,
            id_faixa2= self.id_faixa2
        )

        for faixa_3 in self.faixas_3:
            faixa_2_clone.faixas_3.append(faixa_3.clonar())

        for faixa_3 in faixa_2_clone.faixas_3:
            faixa_3.altura_usada = sum(item.altura for item in faixa_3.itens)
            faixa_3.calcular_ocupacao()

        faixa_2_clone.largura_disponivel = (
            faixa_2_clone.largura - sum(f3.largura for f3 in faixa_2_clone.faixas_3)
        )

        faixa_2_clone.calcular_ocupacao()


        return faixa_2_clone

    def to_dict(self):
        """
        Converte a faixa 2 para dict
        """
        return {
            "id": self.id_faixa2,
            "y": self.coord_y,
            "largura": self.largura,
            "altura": self.altura,
            'largura_disponivel': self.largura_disponivel,
            'area_ocupada': self.area_ocupada,
            'ocupacao': self.ocupacao,
            "faixas_3": [f3.to_dict() for f3 in self.faixas_3]
        }
    
    def __repr__(self):
        return (
            f"Faixa2("
            f"W={self.largura}, "
            f"H={self.altura}, "
            f"Y={self.coord_y}, "
            f"Ocupação: {self.ocupacao}, "
            f"Faixas_3={len(self.faixas_3)})"
        )
    
    def cabe(self, item):
        return (
            item.largura <= self.largura_disponivel
            and item.altura <= self.altura
        )

    def criar_faixa_3(self, item):
        """
        Cria uma nova faixa de nível 3 dentro da faixa 2.
        Apenas a faixa 2 pode chamar este método.
        """
        if item.largura > self.largura_disponivel:
            return None
    
        nova_faixa_3 = Faixa3(
            largura=item.largura,
            altura=self.altura,
            coord_x=self.largura - self.largura_disponivel,
            coord_y=self.coord_y
        )

        self.faixas_3.append(nova_faixa_3)
        self.largura_disponivel -= item.largura

        return nova_faixa_3
    
    def pode_criar_faixa_3(self, altura_faixa):
        """
        Verifica se ainda há altura disponível
        para criar uma nova faixa 3.
        """
        return self.altura_usada + altura_faixa <= self.altura

    def tentar_alocar_item(self, item):
        """
        Tenta alocar o item em alguma faixa 3 existente.
        Se não for possível, tenta criar nova faixa 3.
        Retorna sucesso ou falha.
        """
        # 1) Tenta usar faixas 3 existentes
        for faixa_3 in self.faixas_3:
            if faixa_3.alocar_item(item):
                self.calcular_ocupacao() #Estava dando bug aqui, calculava errado
                return True

        # 2) Tenta criar nova faixa 3
        if self.pode_criar_faixa_3(item.altura):
            nova_faixa_3 = self.criar_faixa_3(item)
            if nova_faixa_3 is not None:
                if nova_faixa_3.alocar_item(item):
                    self.calcular_ocupacao() #AQui
                    return True

        return False

    def calcular_ocupacao(self):
        """
        Calcula a ocupação da faixa 2 a partir das faixas 3.
        """
        area_total = self.largura * self.altura
        area_ocupada = 0

        for faixa_3 in self.faixas_3:
            area_ocupada += faixa_3.area_ocupada

        if area_ocupada > 0:
            self.area_ocupada = area_ocupada
            self.ocupacao = area_ocupada / area_total
