class Faixa3:
    """
    Representa uma faixa de nível 3 (estágio 3 de corte).
    É uma região vertical dentro de uma faixa 2.
    Responsável por alocar itens lado a lado.
    """

    def __init__(self, largura, altura, coord_x, coord_y, id_faixa3=None):
        """
        Inicializa a faixa 3 com dimensões fixas
        e posição absoluta dentro do bin.
        """
        self.id_faixa3 = id_faixa3

        # Geometria fixa
        self.largura = largura
        self.altura = altura
        self.coord_x = coord_x
        self.coord_y = coord_y

        # Estrutura interna
        self.itens = []

        # Controle de espaço
        self.largura_disponivel = largura
        self.altura_usada = 0

        # Métrica
        self.area_ocupada = 0

    def clonar(self):
        faixa_3_clone = Faixa3(
            largura= self.largura,
            altura= self.altura,
            coord_x= self.coord_x,
            coord_y= self.coord_y,
            id_faixa3= self.id_faixa3
        )

        for item in self.itens:
            faixa_3_clone.itens.append(item.clonar())

        return faixa_3_clone
    
    def __repr__(self):
        return (
            f"Faixa3("
            f"W={self.largura}, "
            f"H={self.altura}, "
            f"X={self.coord_x}, "
            f"Y={self.coord_y}, "
            f"Itens={len(self.itens)})"
        )

    def pode_alocar(self, item):
        """
        Verifica se o item cabe verticalmente
        dentro da faixa 3 (empilhamento).
        """
        return self.altura_usada + item.altura <= self.altura and item.largura <= self.largura



    def alocar_item(self, item):
        """
        Aloca o item empilhando verticalmente.
        """
        if not self.pode_alocar(item):
            return False

        item.coord_x = self.coord_x
        item.coord_y = self.coord_y + self.altura_usada

        self.itens.append(item)
        self.altura_usada += item.altura
        self.calcular_ocupacao()

        item.alocado = True
        return True



    def calcular_ocupacao(self):
        """
        Retorna a taxa de ocupação da faixa 3.
        """
        area_usada = sum(
            item.largura * item.altura for item in self.itens
        )

        if area_usada > 0:
            self.area_ocupada = area_usada

    def to_dict(self):
        """
        Converte a faixa 3 para dict
        """
        return {
            'id': self.id_faixa3,
            "x": self.coord_x,
            "y": self.coord_y,
            "largura": self.largura,
            "altura": self.altura,
            'altura_usada': self.altura_usada,
            'area_ocupada': self.area_ocupada,
            "itens": [item.to_dict() for item in self.itens]
        }

