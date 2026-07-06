
class ParametrosGA:
    def __init__(
            self,
            #Prob fixas
            prob_crossover = 0.5, #0.6856833100653761,
            prob_mutacao = 0.5, #0.30649968939940125,

            percent_ind_elite = 0.2, #0.18460952247849138,
            percent_bins_elite = 0.3,#0.30165779731892933,
            percent_faixas_elite = 0.45,#0.42598455848240985,

            tamanho_populacao = 80,#82,

            num_geracoes = 1000000,
            tempo_max = 600, #<- se quiser mexer no tempo é aqui
            

            percent_ind_TOP = 0.25,
            percent_ind_MID = 0.5,
            percent_ind_BOT = 0.25,

            #Prob variaveis
            prob_mutacao_min = 0.05,
            prob_mutacao_max = 0.35,
            prob_crossover_min = 0.8,
            prob_crossover_max = 0.9,

            populacao_min = 20,
            populacao_max = 40,

            percent_ind_elite_max = 0.4,
            percent_ind_elite_min = 0.1,

            prob_DR = 0.3,

            DR_top_individuos = 0.3,
            DR_k = [2, 3, 4],

            Inj_Diversidade_TOP = 5,
            Inj_Diversidade_percent_diferenca = 0.05,

            num_max_iteracoes_sem_melhoria = 50,
            proporcao_tempo_max_sem_melhoria = 0.2,
            individuos_para_manter_em_restart_parcial = 2,

            parametros_variaveis = True
            

            ):
    
        """
        Parâmetros do algoritmo genético
        """

        #Parametros Fixos
        self.prob_crossover = prob_crossover
        self.prob_mutacao = prob_mutacao

        self.tamanho_populacao = tamanho_populacao
        self.tempo_max = tempo_max
        self.n_ind_elite = max(1, int(tamanho_populacao * percent_ind_elite)) #No mínimo 1 individuo Elite
        self.percent_ind_elite = percent_ind_elite
        self.percent_faixas_elite = percent_faixas_elite
        self.num_geracoes = num_geracoes #stop criteria

        self.percent_bins_elite = percent_bins_elite

        #Para a seleção de individuos
        self.percent_ind_TOP = percent_ind_TOP
        self.percent_ind_MID = percent_ind_MID
        self.percent_ind_BOT = percent_ind_BOT

        #Parâmetros variáveis
        self.populacao_min = populacao_min
        self.populacao_max = populacao_max

        self.prob_mutacao_min = prob_mutacao_min
        self.prob_mutacao_max = prob_mutacao_max

        self.prob_crossover_min = prob_crossover_min
        self.prob_crossover_max = prob_crossover_max

        self.percent_ind_elite_max = percent_ind_elite_max
        self.percent_ind_elite_min = percent_ind_elite_min

        #Aqui define como vai ser, se será fixo ou variável
        self.parametros_variaveis = parametros_variaveis

        self.prob_DR = prob_DR

        #Destroy and repair
        self.DR_top_individuos = DR_top_individuos
        self.DR_k = DR_k

        #Injeção de diversidade / convergência
        self.Inj_Diversidade_TOP = Inj_Diversidade_TOP
        self.Inj_Diversidade_percent_diferenca = Inj_Diversidade_percent_diferenca

        #Restart parcial
        self.num_max_iteracoes_sem_melhoria = num_max_iteracoes_sem_melhoria
        self.proporcao_tempo_max_sem_melhoria = proporcao_tempo_max_sem_melhoria
        self.individuos_para_manter_em_restart_parcial = individuos_para_manter_em_restart_parcial
        self.prob_DR_min = prob_DR
        self.prob_DR_max = 1

    def parametros_da_geracao(self, geracao, tempo_decorrido = None):

        # Progresso por geração
        t_geracao = geracao / max(1, self.num_geracoes - 1)
        
        if tempo_decorrido != None:
            # Progresso por tempo
            t_tempo = tempo_decorrido / max(1, self.tempo_max)
            # Usa o que estiver mais avançado
            t = max(t_geracao, t_tempo)
        else: 
            t = t_geracao

        t_rapido = min(1.0, t * 10)


        self.prob_crossover = self.prob_crossover_max - (self.prob_crossover_max - self.prob_crossover_min) * t_rapido
        self.prob_mutacao   = self.prob_mutacao_max   - (self.prob_mutacao_max   - self.prob_mutacao_min)   * t_rapido

        self.prob_crossover = max(0.0, min(1.0, float(self.prob_crossover)))
        self.prob_mutacao   = max(0.0, min(1.0, float(self.prob_mutacao)))

        self.tamanho_populacao = int(self.populacao_min + (self.populacao_max - self.populacao_min) * t_rapido)
        self.tamanho_populacao = max(2, min(self.tamanho_populacao, self.populacao_max))

        n_min = self.percent_ind_elite_min * self.tamanho_populacao
        n_max = self.percent_ind_elite_max * self.tamanho_populacao
        n = max(1, int(n_min + (n_max - n_min) * t_rapido))
        self.n_ind_elite = n  

        self.prob_DR = self.prob_DR_min

    def resetar_parametros(self):

        self.prob_crossover = self.prob_crossover_max
        self.prob_mutacao   = self.prob_mutacao_max 
        n_min = self.percent_ind_elite_min * self.tamanho_populacao
        self.n_ind_elite = max(1, int(n_min))
        self.prob_DR = self.prob_DR_max


