class Item:
    """
    Representa um item retangular a ser empacotado.
    O item NÃO decide nada. Ele apenas existe e ocupa espaço.
    """

    def __init__(self, largura, altura, id_item=None):
        """
        Inicializa o item com dimensões fixas.
        """
        self.id_item = id_item

        # Dimensões
        self.largura = largura
        self.altura = altura

        # Posição (só é definida após alocação)
        self.coord_x = None
        self.coord_y = None

        # Estado
        self.alocado = False

    def __repr__(self):
        return f"Item(id={self.id_item}, w={self.largura}, h={self.altura}, x={self.coord_x}, y={self.coord_y})"
    
    def marcar_como_alocado(self):
        """
        Marca o item como alocado.
        """
        self.alocado = True

    def to_dict(self):
        """
        Converte o item para dict
        """
        return {
            "id": self.id_item,
            "x": self.coord_x,
            "y": self.coord_y,
            "largura": self.largura,
            "altura": self.altura,
            'alocado': self.alocado
        }
    
    def clonar(self):
        item_clone = Item(
            id_item= self.id_item,
            largura= self.largura,
            altura = self.altura
        )
        item_clone.coord_x = self.coord_x
        item_clone.coord_y = self.coord_y

        return item_clone
    