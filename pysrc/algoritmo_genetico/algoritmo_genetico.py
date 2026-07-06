import random
import time

from .parametros_ga import ParametrosGA
from .individuo import Individuo
from empacotador.empacotador import Empacotador
from utilitarios.leitor_itens import LeitorDeItens
from utilitarios.desenhador import Desenhador


class AlgoritmoGenetico:
    def __init__(self, instancia, dimensoes_bin, report = False):
        
        self.populacao = list()

        self.melhor_individuo = None

        self.parametros = ParametrosGA()

        self.instancia = instancia
        self.dimensoes_bin = dimensoes_bin

        leitor = LeitorDeItens(self.instancia, forma_de_ordenamento='Random') #Eu coloquei random, para a cada iteração ser diferente
        itens = leitor.criar_itens()

        self.itens_base = leitor.criar_itens()
        self.qtd_itens = len(self.itens_base)

        self.novo_cromossomo = None

        self.report = report

        self.melhor_da_geracao = None

        self.injecao_de_diversidade_ativa = False

        self.geracoes_sem_melhoria_global = 0
        self.melhor_bins_global_anterior = None
        self.melhor_area_global_anterior = None
        self.intervalo_restart = 100  # Se não melhorar ocm 80 gerações reseta
        self.cooldown_restart = 0
        self.min_cooldown_restart = 100  # mínimo de gerações entre restarts

        self.resultado_com_300_s = {}


    def __repr__(self):
        pass

    def iniciar_populacao(self):
        ordenamentos_deterministicos = [
            'H',           # maior altura primeiro
            'W',           # maior largura primeiro
            'area_Des',    # maior área primeiro
            'area_As',     # menor área primeiro
            'perimetro',   # maior perímetro primeiro
            'ratio_Des',   # maior razão H/W primeiro (itens altos e estreitos)
            'ratio_As',    # menor razão H/W primeiro (itens largos e baixos)
        ]

        n_det = len(ordenamentos_deterministicos)
        n_random = max(0, self.parametros.tamanho_populacao - n_det)
        possibilidades_de_ordenamento = ordenamentos_deterministicos + ['Random'] * n_random
        #possibilidades_de_ordenamento = ['H', 'W', "area_Des", "area_As"] + ['Random']*(self.parametros.tamanho_populacao - 4) #Isso garante que a primeira vez seja H, a segunda W, e as demais random
        for i in range(self.parametros.tamanho_populacao):
            ordenamento = possibilidades_de_ordenamento[i]
            

            leitor = LeitorDeItens(self.instancia, forma_de_ordenamento=ordenamento)
            itens = leitor.criar_itens()


            empacotador = Empacotador(itens=itens, dimensoes_bin=self.dimensoes_bin, tipo_de_empacotamento="FF")
            empacotador.resolver()


            if self.report:
                for bin in empacotador.bins:
                    desenhador = Desenhador(bin=bin)
                    #desenhador.imprimir()
                    desenhador.desenhar_solucao()


            #saida = empacotador.gerar_resultado(export_json = False, return_data = True)
            individuo = Individuo(cromossomo=itens)
            individuo.anotar_resultado(solucao=empacotador.bins, fitness=empacotador.fitness_solucao, num_bins=len(empacotador.bins))
            individuo.avaliar_area_menor_bin()
            self.populacao.append(individuo)
            
            if self.report:
                print(f"Ordenamento: {ordenamento} - Indivíduo {i + 1}")
            
                print(f"   Bins: {empacotador.bins}")
                print(f"   Fitness: {empacotador.fitness_solucao}")
                print()
        
        # === PRINT: Top 4 determinísticos + melhor Random ===
        total_area = self.dimensoes_bin[0] * self.dimensoes_bin[1]

    def _rebuild_itens_dict(self):
        self.itens_dict = {}
        for it in self.itens:
            key = (it.largura, it.altura)
            if key not in self.itens_dict:
                self.itens_dict[key] = []
            self.itens_dict[key].append(it)
    
    def restart_necessario(self, tempo_decorrido):
        # Cooldown: não restarta se restartou recentemente
        if self.cooldown_restart > 0:
            self.cooldown_restart -= 1
            return False

        atual_bins = self.melhor_individuo.num_bins
        atual_area = self.melhor_individuo.area_do_menor_bin

        if (self.melhor_bins_global_anterior == atual_bins and
            self.melhor_area_global_anterior == atual_area):
            self.geracoes_sem_melhoria_global += 1
        else:
            self.geracoes_sem_melhoria_global = 0
            self.melhor_bins_global_anterior = atual_bins
            self.melhor_area_global_anterior = atual_area

        t_tempo = tempo_decorrido / max(1, self.parametros.tempo_max)
        proporcao_tempo = self.parametros.proporcao_tempo_max_sem_melhoria

        return (
            self.geracoes_sem_melhoria_global >= self.parametros.num_max_iteracoes_sem_melhoria
            or t_tempo >= proporcao_tempo
        )
    
    def restart_parcial(self):
        #print(">>> Restart parcial")
        try:
            self.populacao.sort(key=self.chave_ranking)
        except:
            self.populacao.sort(key=lambda ind: ind.num_bins)

        # Mantém apenas o top N
        n_preservar = self.parametros.individuos_para_manter_em_restart_parcial  # ajustável
        self.populacao = self.populacao[:n_preservar]

        # Preenche o resto com ordenamentos variados + random
        ordenamentos = ['H', 'W', 'area_Des', 'area_As', 'perimetro', 'ratio_Des', 'ratio_As']
        i = 0
        while len(self.populacao) < self.parametros.tamanho_populacao:
            ord_escolhido = ordenamentos[i % len(ordenamentos)] if i < len(ordenamentos) else 'Random'
            leitor = LeitorDeItens(self.instancia, forma_de_ordenamento=ord_escolhido)
            itens = leitor.criar_itens()
            empacotador = Empacotador(itens=itens, dimensoes_bin=self.dimensoes_bin, tipo_de_empacotamento="FF")
            empacotador.resolver()
            individuo = Individuo(cromossomo=itens)
            individuo.anotar_resultado(solucao=empacotador.bins, fitness=empacotador.fitness_solucao, num_bins=len(empacotador.bins))
            individuo.avaliar_area_menor_bin()
            self.populacao.append(individuo)
            i += 1

        # Reseta parâmetros para exploração
        self.parametros.prob_mutacao = self.parametros.prob_mutacao_max
        self.parametros.prob_crossover = self.parametros.prob_crossover_max
        self.geracoes_desde_restart = 0

    def selecionar_pais(self):
        """
        Seleciona dois individuos pais para fazer o crossover
        """
        #Por enquanto estou retornando 0 e 1, aplicar uma regra depois

        #A regra: Selecionar um pai do TOP e um pai do MiDDLE

        #Uma copia ordenada da lista população, para não mexer nela
        try:
            ranking = sorted(self.populacao, key=self.chave_ranking)
        except:
            ranking = sorted(
                self.populacao,
                key=lambda ind: (ind.num_bins)
            )
        n = len(ranking)

        qtd_TOP = max(1, int(n * self.parametros.percent_ind_TOP))
        qtd_BOT = max(1, int(n * self.parametros.percent_ind_BOT))
        qtd_MID = n - qtd_TOP - qtd_BOT

        idx_TOP = random.randint(0, qtd_TOP - 1)
        ind_TOP = ranking[idx_TOP]

        idx_MID = random.randint(qtd_TOP, qtd_TOP + qtd_MID - 1)
        ind_MID = ranking[idx_MID]

        if self.report:
            print(f"Indíviduos Selecionados  ->  TOP:{idx_TOP}  |  MID:{idx_MID}")
        
        return ind_TOP, ind_MID

    def verificar_validade_faixa_2(self, faixa_2):
        # 1) conta quantos itens (w,h) a faixa exige
        demanda = {}
        for f3 in faixa_2.faixas_3:
            for it in f3.itens:
                key = (it.largura, it.altura)
                demanda[key] = demanda.get(key, 0) + 1

        # 2) valida quantidade usando o dict
        for key, q in demanda.items():
            disponivel = len(self.itens_dict.get(key, []))
            if disponivel < q:
                return False

        return True
    
    def elitismo_faixas(self, pai_1, pai_2):
        """
        Retorna as faixas_2 de ambos os pais
        Retorna apenas a quantidade de faixas determinada nos parâmetros
        """
        faixas = []
        for bin in pai_1.solucao:
            for faixa_2 in bin.faixas_2:
                faixas.append(faixa_2)
        
        for bin in pai_2.solucao:
            for faixa_2 in bin.faixas_2:
                faixas.append(faixa_2)

        faixas_ordenadas = sorted(faixas, key=lambda faixa: faixa.ocupacao, reverse=True)
        for f_2 in faixas_ordenadas:
            if self.verificar_validade_faixa_2(f_2):
                for faixa_3 in f_2.faixas_3:
                    for item in faixa_3.itens:
                        if len(self.novo_cromossomo) < int(self.qtd_itens * self.parametros.percent_faixas_elite): #Verificar se a qtd de itens crossover já não foi atingida
                            self.remover_e_item_alocado(item)
                        else:
                            return 
                        
        return


    def verificar_validade_bin(self, bin):
        demanda = {}
        for faixa_2 in bin.faixas_2:
            for f3 in faixa_2.faixas_3:
                for it in f3.itens:
                    key = (it.largura, it.altura)
                    demanda[key] = demanda.get(key, 0) + 1

        for key, q in demanda.items():
            disponivel = len(self.itens_dict.get(key, []))
            if disponivel < q:
                return False
        return True
    
    def elitismo_bins(self, pai):
        """
        Alguns bins não serão mexidos
        Retorna os itens desses bins, em ordem
        """

        bins_pai = []

        n_bins_mantidos = max(1, int(self.parametros.percent_bins_elite * len(pai.solucao))) # No mínimo 1 bin será mantido        
        bins_ordenados = sorted(pai.solucao, key=lambda bin: bin.fitness, reverse=True)

        for idx_bin in range(len(bins_ordenados)):
            if self.verificar_validade_bin(bins_ordenados[idx_bin]): #Verifica se todos os itens do bin pai estão disponíveis
                bins_pai.append(bins_ordenados[idx_bin])
                if len(bins_pai) >= n_bins_mantidos: #Significa que atingiu o número de bins a serem mantidos
                    return bins_pai

        #Aqui é para caso atinja uma qtd de bins mantidos menor do que o desejado (ou seja, vai acabar o for)
        return bins_pai

    def remover_e_item_alocado(self, item):
        key = (item.largura, item.altura)
        
        if key in self.itens_dict and self.itens_dict[key]:
            it = self.itens_dict[key].pop()  # O(1)
            self.itens.remove(it)            # ainda O(n) mas chamado menos
            self.novo_cromossomo.append(it)
            return

        raise RuntimeError(
            f"Item {item.largura}x{item.altura} não encontrado"
        )

    def remocao_items_de_um_bin (self, bin):
        for faixa_2 in bin.faixas_2:
            for faixa_3 in faixa_2.faixas_3:
                for item in faixa_3.itens:
                    self.remover_e_item_alocado(item)


    def crossover(self, pai_1, pai_2):
        self.novo_cromossomo = []

        # ETAPA 1: coleta itens dos bins elite em ordem
        todos_bins = sorted(
            pai_1.solucao + pai_2.solucao,
            key=lambda b: b.fitness,
            reverse=True
        )
        n_elite = max(1, int(self.parametros.percent_bins_elite * len(todos_bins)))

        bins_elite_adicionados = 0
        for bin in todos_bins:
            if bins_elite_adicionados >= n_elite:
                break
            if self.verificar_validade_bin(bin):
                self.remocao_items_de_um_bin(bin)
                bins_elite_adicionados += 1

        # ETAPA 2: faixas elite para os restantes
        self.elitismo_faixas(pai_1, pai_2)

    def elitismo_populacao(self):
        """
        Faz o elitismo da população, ou seja, os melhores individuos são preservados
        """
        try:
            self.populacao.sort(key=self.chave_ranking)
        except:
            self.populacao.sort(
                key=lambda ind: (ind.num_bins)
            )
        elite = [ind.clonar() for ind in self.populacao[:self.parametros.n_ind_elite]]
        return elite
    

    def atualizar_melhor_individuo(self, geracao):
        # melhor da geração
        try:
            melhor_da_geracao = min(self.populacao, key=self.chave_ranking)
        except:
            melhor_da_geracao = min(
                self.populacao,
                key=lambda ind: (ind.num_bins)
            )

        self.melhor_da_geracao = melhor_da_geracao.clonar()

        # atualiza melhor global
        if self.melhor_individuo is None:
            self.melhor_individuo = melhor_da_geracao.clonar()
            melhorou = True
        else:
            melhorou = (
                melhor_da_geracao.num_bins < self.melhor_individuo.num_bins
                or (
                    melhor_da_geracao.num_bins == self.melhor_individuo.num_bins
                    and melhor_da_geracao.area_do_menor_bin > self.melhor_individuo.area_do_menor_bin
                )
            )
            if melhorou:
                self.melhor_individuo = melhor_da_geracao.clonar()

        # ordena população para pegar top-5 da geração
        try:
            ranking = sorted(self.populacao, key=self.chave_ranking)
        except:
            ranking = sorted(
                self.populacao,
                key=lambda ind: (ind.num_bins)
            )

        top_k = min(5, len(ranking))

        total_area = self.dimensoes_bin[0] * self.dimensoes_bin[1]


    def destroy_and_repair(self, individuo, k=None):
        k = random.choice(self.parametros.DR_k)

        self.itens = [it.clonar() for it in self.itens_base]

        self._rebuild_itens_dict()

        bins_ordenados = sorted(individuo, key=lambda bin: bin.fitness)
        bins_remover = bins_ordenados[:k]
        bins_restantes = [b for b in bins_ordenados if b not in bins_remover]

        # Coleta itens destruídos
        itens_destruidos = []
        for bin in bins_remover:
            for f2 in bin.faixas_2:
                for f3 in f2.faixas_3:
                    for item in f3.itens:
                        itens_destruidos.append(item)

        # Monta cromossomo: preservados primeiro, destruídos depois
        self.novo_cromossomo = []
        for bin in bins_restantes:
            self.remocao_items_de_um_bin(bin)  # move de self.itens para self.novo_cromossomo

        random.shuffle(itens_destruidos)
        for item in itens_destruidos:
            # pega o item equivalente de self.itens para manter consistência
            self.remover_e_item_alocado(item)

        # Empacota tudo do zero, sem warm start
        empacotador = Empacotador(
            itens=self.novo_cromossomo,
            dimensoes_bin=self.dimensoes_bin,
            tipo_de_empacotamento="BF"
        )
        empacotador.resolver()

        resultado = Individuo(cromossomo=self.novo_cromossomo)
        resultado.anotar_resultado(
            solucao=empacotador.bins,
            fitness=empacotador.fitness_solucao,
            num_bins=len(empacotador.bins)
        )
        resultado.avaliar_area_menor_bin()
        return resultado

    def mutacao(self):
        #print("prob_mutacao =", self.parametros.prob_mutacao, type(self.parametros.prob_mutacao))
        insertion_count = 0
        swap_count = 0
        inversion_count = 0

        def mutacao_insercao():
            nonlocal insertion_count
            for item in self.itens:
                if random.random() < self.parametros.prob_mutacao: #Se atingir a probabilidade, faz a inserção
                    pos = random.randint(0, len(self.novo_cromossomo))
                    insertion_count += 1  
                else: #Se não, insere no final
                    pos = len(self.novo_cromossomo)

                self.novo_cromossomo.insert(pos, item)

        def mutacao_swap():
            nonlocal swap_count
            if random.random() < self.parametros.prob_mutacao:
                swap_count += 1
                i = random.randrange(self.qtd_itens)
                j = random.randrange(self.qtd_itens)
                self.novo_cromossomo[i], self.novo_cromossomo[j] = self.novo_cromossomo[j], self.novo_cromossomo[i]
        
        def mutacao_inversion():
            nonlocal inversion_count
            # só aplica com certa probabilidade
            if random.random() < self.parametros.prob_mutacao:
                inversion_count += 1
                n = len(self.novo_cromossomo)
                if n < 2:
                    return

                i = random.randint(0, n - 2)
                j = random.randint(i + 1, n - 1)

                # inverte o segmento [i, j]
                self.novo_cromossomo[i:j+1] = reversed(self.novo_cromossomo[i:j+1])


        mutacao_insercao()

        #Por hora fiz assim mesmo, depois troco
        for item in self.itens:
            val_aleatorio = random.random()
            if val_aleatorio < 0.5:
                mutacao_swap()
            else:
                mutacao_inversion()
        #print(f"    Insertion: {insertion_count} | Swap: {swap_count} | Inversion: {inversion_count}")
        


    def chave_ranking(self, ind):
        W, H = self.dimensoes_bin
        area_bin = W * H

        area_livre_max = max(b.altura_disponivel * W for b in ind.solucao)
        espaco_livre_normalizado = area_livre_max / area_bin

        return (
            ind.num_bins,                    # 1º: menos bins
            -espaco_livre_normalizado,       # 2º: bin mais vazio possível
        )

    def populacao_convergiu(self):
        """
        Verifica se os melhores indivíduos têm todos o mesmo num_bins
        e área livre muito parecida
        """
        try:
            ranking = sorted(self.populacao, key=self.chave_ranking)
        except:
            ranking = sorted(self.populacao, key=lambda ind: ind.num_bins)
        
        top = ranking[:min(self.parametros.Inj_Diversidade_TOP, len(ranking))]
        
        bins_iguais = len(set(ind.num_bins for ind in top)) == 1
        areas_proximas = (
            max(ind.area_do_menor_bin for ind in top) -
            min(ind.area_do_menor_bin for ind in top)
        ) < (self.dimensoes_bin[0] * self.dimensoes_bin[1] * self.parametros.Inj_Diversidade_percent_diferenca)

        return bins_iguais and areas_proximas

    def injetar_diversidade(self):
        """
        Substitui metade da população por novos indivíduos aleatórios
        """
        #print(">>> Injetando diversidade")

        #TRAVANDO PARAMETROS NO MAXIMO
        self.parametros.resetar_parametros()
        
        try:
            self.populacao.sort(key=self.chave_ranking)
        except:
            self.populacao.sort(key=lambda ind: ind.num_bins)

        # Mantém apenas os elite
        self.populacao = self.populacao[:self.parametros.n_ind_elite]

        # Preenche o resto com novos indivíduos aleatórios
        while len(self.populacao) < self.parametros.tamanho_populacao:
            leitor = LeitorDeItens(self.instancia, forma_de_ordenamento='Random')
            itens = leitor.criar_itens()
            empacotador = Empacotador(itens=itens, dimensoes_bin=self.dimensoes_bin, tipo_de_empacotamento="FF")
            empacotador.resolver()
            individuo = Individuo(cromossomo=itens)
            individuo.anotar_resultado(solucao=empacotador.bins, fitness=empacotador.fitness_solucao, num_bins=len(empacotador.bins))
            individuo.avaliar_area_menor_bin()
            self.populacao.append(individuo)

    
    
    def executar(self, stop_time = True):
        """
        É o main do algoritmo genetico
        """
        t_inicial = time.perf_counter()

        if self.parametros.parametros_variaveis:
            self.parametros.parametros_da_geracao(geracao = 0, tempo_decorrido=None)

        self.iniciar_populacao()
        self.atualizar_melhor_individuo(geracao=0)

        
        for geracao in range(self.parametros.num_geracoes):
            self.geracao = geracao
            t_agora = time.perf_counter()
            tempo_decorrido = t_agora - t_inicial
            if self.parametros.parametros_variaveis and not self.injecao_de_diversidade_ativa:
                self.parametros.parametros_da_geracao(geracao = geracao, tempo_decorrido = tempo_decorrido)
            #print(f"[G{geracao:03d}] | cross={self.parametros.prob_crossover:.2f} mut={self.parametros.prob_mutacao:.2f} | pop={self.parametros.tamanho_populacao} elite={self.parametros.n_ind_elite} D%R={self.parametros.prob_DR}")
            #print(f"Geração {geracao}")
            nova_populacao = self.elitismo_populacao()
            contador_filho = 0

            while len(nova_populacao) < self.parametros.tamanho_populacao:
                self.itens = [it.clonar() for it in self.itens_base]

                self._rebuild_itens_dict()
                
                self.qtd_itens = len(self.itens)

                pai_1, pai_2 = self.selecionar_pais()
                self.crossover(pai_1=pai_1, pai_2=pai_2)
                self.mutacao()

                escolha_tipo = random.choices(["FF", "BF"], weights=[0.9, 0.1], k=1)[0]
                empacotador_ws = Empacotador(
                    itens=self.novo_cromossomo,
                    dimensoes_bin=self.dimensoes_bin,
                    tipo_de_empacotamento=escolha_tipo
                )
                empacotador_ws.resolver()
                #empacotador_ws.bins = bins_crossover  # usa direto
                #empacotador_ws.calcular_resultado()   # só recalcula métricas

                filho = Individuo(cromossomo=self.novo_cromossomo)
                filho.anotar_resultado(
                    solucao=empacotador_ws.bins,
                    fitness=empacotador_ws.fitness_solucao,
                    num_bins=len(empacotador_ws.bins)
                )
                filho.avaliar_area_menor_bin()

                # Aplica destroy_and_repair e mantém o melhor entre os dois
                # Em vez de sempre usar melhor_da_geracao
                # Escolhe aleatoriamente entre os melhores
                prob_dr = self.parametros.prob_DR  # probabilidade do Destroy and repair
                if random.random() < prob_dr:
                    try:
                        ranking = sorted(self.populacao, key=self.chave_ranking)
                    except:
                        ranking = sorted(self.populacao, key=lambda ind: ind.num_bins)

                    top_k = max(1, int(self.parametros.DR_top_individuos * len(ranking)))  # top %
                    alvo_dr = random.choice(ranking[:top_k])

                    filho_dr = self.destroy_and_repair(individuo=alvo_dr.solucao)

                    #filho_dr = self.destroy_and_repair(individuo=self.melhor_da_geracao.solucao)
                    if filho_dr is not None:
                        try:
                            if self.chave_ranking(filho_dr) < self.chave_ranking(filho):
                                filho = filho_dr
                        except:
                            if filho_dr.num_bins < filho.num_bins:
                                filho = filho_dr

                nova_populacao.append(filho)


            if self.report:
                for filho in nova_populacao:
                    print(f"Filho {contador_filho}/{self.parametros.tamanho_populacao}")
                    contador_filho += 1
                    for idx, bin in enumerate(filho.solucao):
                        print(
                            f"Bin {idx}/{len(filho.solucao)} | Altura disponível: {bin.altura_disponivel}"
                        )


            self.populacao = nova_populacao
            self.atualizar_melhor_individuo(geracao)

            

            t_agora = time.perf_counter()
            tempo = t_agora - t_inicial
            if (tempo > self.parametros.tempo_max) and (len(self.resultado_com_300_s) == 0):
                self.resultado_com_300_s['tempo'] = tempo
                self.resultado_com_300_s['fitness'] = self.melhor_individuo.fitness
                self.resultado_com_300_s['area_do_menor_bin'] = self.melhor_individuo.area_do_menor_bin
                self.resultado_com_300_s['num_bins'] = self.melhor_individuo.num_bins
                self.resultado_com_300_s['geracao'] = geracao
                print(f"300 segundos atingidos, geração {geracao}")
                
                if stop_time:
                    break 
            #for i in self.populacao:
                #print(i)
        #print(nova_populacao)
            
            # Detecta convergência e injeta diversidade se necessário
            if self.populacao_convergiu():
                self.injecao_de_diversidade_ativa = True
                self.injetar_diversidade()
            else:
                self.injecao_de_diversidade_ativa = False

            t_agora = time.perf_counter()
            tempo_decorrido = t_agora - t_inicial
            #Para quando os resultados estagnarem
            if self.restart_necessario(tempo_decorrido=tempo_decorrido):
                self.restart_parcial()
                self.cooldown_restart = self.min_cooldown_restart
                # Atualiza o anterior para o estado atual pós-restart
                self.melhor_bins_global_anterior = self.melhor_individuo.num_bins
                self.melhor_area_global_anterior = self.melhor_individuo.area_do_menor_bin

        #self.report = True
        if self.report:
            for bin in self.melhor_individuo.solucao:
                desenhador = Desenhador(bin=bin)
                #desenhador.imprimir()
                desenhador.desenhar_solucao()
                desenhador.imprimir()
        #return geracao


