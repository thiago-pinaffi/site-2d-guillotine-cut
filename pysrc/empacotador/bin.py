class Bin:
    """
    Representa um bin do problema de corte.
    É responsável apenas por organizar faixas de nível 2
    e agregar métricas (ocupação, fitness).
    """

    def __init__(self, largura, altura, id_bin=None):
        """
        Inicializa o bin com dimensões fixas.
        """
        self.id_bin = id_bin
        self.largura = largura
        self.altura = altura

        # Estrutura principal
        self.faixas_2 = []

        # Métricas agregadas
        self.ocupacao = 0.0 #%
        self.area_ocupada = 0.0 #Valor
        self.fitness = 0.0
        self.altura_disponivel = altura
        

    def imprimir(self):
        print()
        print(self)
        for faixa_2 in self.faixas_2:
            print(f"  {faixa_2}")
            for faixa_3 in faixa_2.faixas_3:
                print(f"    {faixa_3}")
                for item in faixa_3.itens:
                    print(f"      {item}")
    
    def __repr__(self):
        return f"Bin(id={self.id_bin}, W={self.largura}, H={self.altura}, Área ocupada={self.area_ocupada}, Fitness={self.fitness}, Altura Disponível: {self.altura_disponivel}, Faixas_2={self.faixas_2})"

    def calcular_ocupacao(self):
        """
        Calcula a ocupação do bin a partir das faixas de nível 2.
        Não olha itens diretamente.
        """
        area_usada = 0
        for faixa_2 in self.faixas_2:
            area_usada += faixa_2.area_ocupada
        
        area_total = self.largura * self.altura
        ocupacao = area_usada/area_total

        if area_usada > 0:
            self.area_ocupada = area_usada
            self.ocupacao = ocupacao

    def calcular_fitness(self):
        """
        Calcula o fitness do bin com base na ocupação
        e em possíveis penalizações.
        """
        #Atualmente o fitness é a % de área ocupada
        self.fitness = self.ocupacao

    def to_dict(self):
        """
        Converte para dict
        """
        return {
            "id": self.id_bin,
            "largura": self.largura,
            "altura": self.altura,
            'area_ocupada': self.area_ocupada,
            'fitness': self.fitness,
            'altura_disponivel': self.altura_disponivel,
            "faixas_2": [f2.to_dict() for f2 in self.faixas_2]
        }


