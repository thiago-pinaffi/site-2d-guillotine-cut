from .bin import Bin
from .faixa2 import Faixa2
from algoritmo_genetico.parametros_ga import ParametrosGA
import json

class Empacotador:
    """
    Resolve o empacotamento de UM indivíduo.
    """

    def __init__(self, itens, dimensoes_bin, faixas_iniciais = None, parametros = None, tipo_de_empacotamento = "FF"):
        """
        Recebe:
        - itens: lista de Item (não alocados)
        - dimensoes_bin: (W, H)
        - faixas_iniciais: solução parcial inicial, como se fosse um warm start
        - parametros: regras do problema (ex: 3 estágios)

        -tipo_de_empacotamento = FF (default), BF
        """
        self.parametros = ParametrosGA()
        
        self.itens = itens
        self.dimensoes_bin = dimensoes_bin

        self.bins = None

        self.bin_atual = None
        self.proximo_id_bin = None

        self.fitness_solucao = None #Valor da solução (o resultado)

        self.tipo = tipo_de_empacotamento


        if faixas_iniciais: #Usado quando existe uma solução inicial parcial
            self.warm_start(faixas_iniciais)
        else:
            self.cold_start()

    def warm_start(self, faixas_iniciais):
        """
        Usado quando existe uma solução inicial parcial

        A solução incial precisa ser consistente (ter todas as caracteristicas de uma solução completa, porém não precisa ter todos os itens alocados)
        """
        self.cold_start()

        if not self.bins:
            self.criar_novo_bin()
        
        for faixa_2 in faixas_iniciais:
            if self.faixa_2_valida(faixa_2):
                faixa_2_clone = faixa_2.clonar()

                bin = self.existe_bin_para_a_faixa_2(faixa_2_clone)
                
                if bin != None:
                    #print("bin != None")
                    self.empilhar_faixas_2(bin, faixa_2_clone)
                    
                else:
                    #print("bin == None")
                    self.criar_novo_bin()

                    #Validação extra
                    bin = self.existe_bin_para_a_faixa_2(faixa_2_clone)
                    if bin != None:
                        self.empilhar_faixas_2(bin, faixa_2_clone)
                    else:
                        raise ValueError(
                        f"Faixa {faixa_2_clone.id_faixa2} não cabe em um bin vazio"
                        )

            #self.mutacao(faixa_2_clone)

    def faixa_2_valida(self, faixa_2):
        # 1) conta quantos itens (w,h) a faixa exige
        demanda = {}
        for f3 in faixa_2.faixas_3:
            for it in f3.itens:
                key = (it.largura, it.altura)
                demanda[key] = demanda.get(key, 0) + 1

        # 2) conta quantos itens (w,h) existem disponíveis
        estoque = {}
        for it in self.itens:
            key = (it.largura, it.altura)
            estoque[key] = estoque.get(key, 0) + 1

        # 3) valida quantidade
        for key, q in demanda.items():
            if estoque.get(key, 0) < q:
                return False

        return True

    
    def existe_item_compativel(self, item_ref, temp_list):
        """
        Verifica se existe algum item disponível
        com mesma largura e altura.
        """
        temp_list.append(item_ref)

        for new_it_ref in temp_list:
            for item in self.itens:
                if (item.largura != new_it_ref.largura) or (item.altura != new_it_ref.altura):
                    return False
        return True


    def existe_bin_para_a_faixa_2(self, faixa_2):
        """
        Verifica se existe algum bin que caixa a faixa_2 (em altura)
        """
        
        for bin in self.bins:
            if bin.altura_disponivel >= faixa_2.altura:
                return bin
        return None

    def empilhar_faixas_2(self, bin, faixa_2):
        """
        Aloca a faixa no bin,
        atualiza as coordenadas
        """
        #print(faixa_2)

        # base Y onde a faixa será colocada
        y_base = bin.altura - bin.altura_disponivel

        # atualiza coordenadas da faixa e conteúdo
        self.atualizar_coordenadas_faixas(faixa_2, y_base)

        # adiciona faixa ao bin
        bin.faixas_2.append(faixa_2)

        # atualiza altura disponível do bin
        bin.altura_disponivel -= faixa_2.altura

        # remove itens alocados da lista de itens disponíveis
        for faixa_3 in faixa_2.faixas_3:
            for item in faixa_3.itens:
                #print("-")
                self.remover_item_alocado(item)
                item.marcar_como_alocado()



    def atualizar_coordenadas_faixas(self, faixa_2, y_base):
        """
        Atualiza coordenadas Y da faixa_2,
        das faixas_3 e dos itens.
        """
        faixa_2.coord_y = y_base

        for faixa_3 in faixa_2.faixas_3:
            faixa_3.coord_y = y_base  # TODAS na mesma altura

            y_item = y_base
            for item in faixa_3.itens:
                item.coord_y = y_item
                y_item += item.altura


    def remover_item_alocado(self, item):
        """
        Remove item da lista de itens disponíveis
        se ainda estiver presente.
        """
        for i, it in enumerate(self.itens):
            if it.largura == item.largura and it.altura == item.altura:
                #print(f"Item {item.largura}x{item.altura} removido")
                self.itens.pop(i)
                return

        raise RuntimeError(
            f"Item {item.largura}x{item.altura} não encontrado na lista de disponíveis"
            f"Itens disponíveis: {[ (it.largura, it.altura) for it in self.itens[:5] ]}"
    )

    def cold_start(self):
        """
        Usado quando quando não há uma solução inicial (ou seja, é o início do zero)
        """
        self.bins = []

        self.bin_atual = None
        self.proximo_id_bin = 0


    def resolver(self):
        """
        Orquestra todo o empacotamento.
        Retorna uma estrutura de solução (bins, faixas, itens).
        """

        if not self.bins:
            self.criar_novo_bin() #Cria o bin inicial somente se não existe um ainda

        for item in self.itens:
            #Devo colocar uma contição nova aqui?
            alocado = self.tentar_alocar_item(item=item)
            if not alocado:
                #significa que o item não cabe em nenhum lugar disponível 
                self.criar_novo_bin()
                alocado = self.tentar_alocar_item(item=item)

                #Segurança: item maior que o bin
                if not alocado:
                    raise ValueError(
                        f"Item {item.id_item} não cabe em um bin vazio"
                    )

        self.calcular_resultado()
        return self.bins

    def criar_novo_bin(self):
        """
        Cria um novo bin vazio (faixa 1 implícita).
        """
        W = self.dimensoes_bin[0]
        H = self.dimensoes_bin[1]
        id = self.proximo_id_bin

        novo_bin = Bin(largura=W, altura=H, id_bin=id)

        self.bins.append(novo_bin)
        self.bin_atual = novo_bin

        self.proximo_id_bin += 1

        #print(self.bins)


    def tentar_alocar_item(self, item):
        """
        Tenta alocar um item em:
        1) faixas 3 existentes
        2) faixas 2 existentes
        3) criando nova faixa 2
        Retorna True se alocado.
        """
        
        if self.tentar_faixas_3(item=item):
            return True
        elif self.tentar_faixas_2(item=item):
            return True
        elif self.criar_faixa_2(item=item):
            return True
        else:
            return False

    def tentar_faixas_3(self, item):
        """
        Percorre todas as faixas 3
        e tenta empilhar o item verticalmente.
        """

        # ===== FIRST FIT =====
        if self.tipo == "FF":
            for bin in self.bins:
                for faixa_2 in bin.faixas_2:
                    for faixa_3 in faixa_2.faixas_3:
                        if faixa_3.alocar_item(item=item):
                            return True
            
            return False

        # ===== BEST FIT =====
        elif self.tipo == "BF":
            melhor = None
            melhor_sobra = float("inf")

            for bin in self.bins:
                for faixa_2 in bin.faixas_2:
                    for faixa_3 in faixa_2.faixas_3:
                        sobra = faixa_3.altura - faixa_3.altura_usada - item.altura
                        if sobra >= 0 and sobra < melhor_sobra:
                            melhor = faixa_3
                            melhor_sobra = sobra

            if melhor:
                return melhor.alocar_item(item)

            return False
        
        else:
            raise RuntimeError(
            f"Tipo de empacotamento {self.tipo} inválido"
            f"Tipos permitidos: 'FF', 'BF'"
            )

    def tentar_faixas_2(self, item):
        """
        Percorre faixas 2 e tenta alocar
        criando uma faixa 3, se necessário.
        """

        if self.tipo == "FF":
            for bin in self.bins:
                for faixa_2 in bin.faixas_2:
                    if faixa_2.tentar_alocar_item(item):
                        return True
            return False
    
        elif self.tipo == "BF":
            # ===== BEST FIT =====
            melhor = None
            melhor_sobra = float("inf")

            for bin in self.bins:
                for faixa_2 in bin.faixas_2:
                    sobra = faixa_2.largura_disponivel - item.largura
                    if sobra >= 0 and sobra < melhor_sobra:
                        melhor = faixa_2
                        melhor_sobra = sobra

            if melhor:
                return melhor.tentar_alocar_item(item)

            return False
        
        else:
            raise RuntimeError(
            f"Tipo de empacotamento {self.tipo} inválido"
            f"Tipos permitidos: 'FF', 'BF'"
            )
    


    def criar_faixa_2(self, item):
        """
        Cria uma nova faixa 2 no bin
        e aloca o item nela.
        """
        for bin in self.bins:

            # 1) Verifica se o item cabe verticalmente no bin
            if item.altura > bin.altura_disponivel:
                continue

            # 2) Define a coordenada Y da nova faixa 2
            coord_y = bin.altura - bin.altura_disponivel

            # 3) Cria a faixa 2
            nova_faixa_2 = Faixa2(
                largura=bin.largura,
                altura=item.altura,
                coord_y=coord_y
            )

            # 4) Cria a primeira faixa 3 e tenta alocar o item
            if not nova_faixa_2.tentar_alocar_item(item):
                continue  # segurança, mas raro

            # 5) Atualiza o bin
            bin.faixas_2.append(nova_faixa_2)
            bin.altura_disponivel -= nova_faixa_2.altura

            return True

        return False

    def calcular_resultado(self):
        for bin in self.bins:
            for faixa_2 in bin.faixas_2:
                faixa_2.calcular_ocupacao()
            bin.calcular_ocupacao()
            bin.calcular_fitness()
            #bin.imprimir()
        self.calcular_fitness_total()

    def calcular_fitness_total(self):
        W, H = self.dimensoes_bin
        area_bin = W * H
        n = len(self.bins)

        # === OBJETIVO PRIMÁRIO: minimizar bins ===
        # Penalização exponencial por bin extra
        # Quanto mais bins, pior de forma não-linear
        penalidade_bins = n ** 2

        # === OBJETIVO SECUNDÁRIO: esvaziar o bin mais vazio ===
        # Queremos MAXIMIZAR o espaço livre do bin mais vazio
        # (facilita eliminá-lo nas próximas gerações)
        area_livre_max = max(b.altura_disponivel * W for b in self.bins)
        espaco_livre_normalizado = area_livre_max / area_bin  # 0..1

        # === FITNESS FINAL (minimizar) ===
        # O peso 0.1 faz o secundário influenciar sem dominar o primário
        self.fitness_solucao = penalidade_bins - (0.1 * espaco_livre_normalizado)

        return self.fitness_solucao
    
    def gerar_resultado(self, export_json = False, json_archive_name = 'results_list', return_data = True):
        """
        Gera estrutura final de saída
        (usada pelo GA para fitness e crossover).
        """
        saida = {
            'bins': self.bins,
            'fitness_total': self.fitness_solucao,
            'num_bins': len(self.bins) 
        }

        if export_json:
            bins_dict, itens_dict = self.to_dict()
            json_saida = {
                'Cromossomo': itens_dict,
                'Bins': bins_dict,
                'fitness_total': saida['fitness_total'],
                'num_bins': saida['num_bins']
            }

            arc_name = json_archive_name + '.json'
            with open(arc_name, "w", encoding="utf-8") as f:
                json.dump(json_saida, f, indent=4, ensure_ascii=False)

        if return_data:
            return saida
    
    def to_dict(self):
        """
        Converte o elemento desejado para dict
        """
        bins_dict = [bin.to_dict() for bin in self.bins]
        itens_dict = [item.to_dict() for item in self.itens]

        return bins_dict, itens_dict

