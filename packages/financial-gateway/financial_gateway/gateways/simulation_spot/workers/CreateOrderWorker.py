"""CreateOrderWorker - Simulation Spot Gateway"""

class CreateOrderWorker:
    """주문 생성 Worker (Simulation)"""

    def __init__(self, exchange):
        pass

    def execute(self, request):
        raise NotImplementedError("CreateOrderWorker not implemented yet")

    def _encode(self, request):
        raise NotImplementedError("_encode not implemented yet")
