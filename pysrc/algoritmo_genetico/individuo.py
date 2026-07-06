class Individuo:
    def __init__(self, cromossomo):
        """
        Representa o indivíduo

         -Cromossomo: Ordem dos itens a serem empacotados
         -Solução: A lista bin com faixas 2, 3 e itens
         -Fitness: Valor fitness da solução
         -Num_bins: Número de bins utilizados na solução
        """
        self.cromossomo = cromossomo

        self.solucao = None
        self.fitness = None
        self.num_bins = None

        self.quadrado_area_usada = None

        self.area_do_menor_bin = None

    def __repr__(self):
        return f"Cromossomo: {self.cromossomo}\nSolução: {self.solucao}\nFitness: {self.fitness}\nNúmero de bins: {self.num_bins}\n"
    
    def anotar_resultado(self, solucao, fitness, num_bins):
        """
        Anota os resultados para o indivíduo
         -Solução: A lista bin com faixas 2, 3 e itens
         -Fitness: Valor fitness da solução
         -Num_bins: Número de bins utilizados na solução
        """

        self.solucao = solucao
        self.fitness = fitness
        self.num_bins = num_bins

    def clonar(self):
        clone = Individuo(self.cromossomo.copy())
        clone.anotar_resultado(
            solucao=self.solucao,
            fitness=self.fitness,
            num_bins=self.num_bins
        )
        clone.avaliar_area_menor_bin()
        return clone
    
    def avaliar_area_menor_bin(self):

        W = self.solucao[0].largura

        #W = self.dimensoes_bin[0]
        self.area_do_menor_bin =  max((W * b.altura_disponivel) for b in self.solucao) if self.solucao else 0

        