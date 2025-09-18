# app/stock_manager.py

import threading
import uuid
from datetime import datetime, timedelta
from typing import Optional

class StockManager:
    """
    Gerencia o estado do estoque e das reservas de forma segura (thread-safe).
    Esta classe é um Singleton na prática para nosso protótipo.
    """
    def __init__(self):
        # Simula a tabela de produtos no banco de dados.
        # Formato: {sku: quantidade}
        self._stock = {"SKU-BZC-001": 10, "SKU-BZC-002": 5}
        
        # Guardará as reservas ativas.
        # Formato: {reservation_id: {"sku": sku, "expires_at": timestamp}}
        self._reservations = {}

        # O 'lock' é o mecanismo que impede a "corrida pelo último item".
        # Apenas uma requisição (thread) pode "segurar" o lock por vez.
        self._lock = threading.Lock()
        print("StockManager inicializado.")

    def get_stock_level(self, sku: str) -> Optional[int]:
        """
        Consulta a quantidade disponível de um SKU de forma segura.

        Retorna a quantidade ou None se o SKU não existir.
        """
        # Usamos 'with self._lock:' para garantir que nenhuma outra requisição
        # possa modificar o estoque ENQUANTO estamos lendo o valor.
        # Isso previne leituras 'sujas' (dirty reads).
        with self._lock:
            # O método .get() de dicionários é útil pois retorna None
            # se a chave não existir, evitando erros.
            quantity = self._stock.get(sku)
            return quantity

    def reserve_stock(self, sku: str, quantity: int = 1) -> Optional[str]:
        """
        Tenta reservar uma quantidade de um SKU.
        Retorna um ID de reserva se bem-sucedido, ou None se não houver estoque suficiente.
        """
        with self._lock:
            available = self._stock.get(sku, 0)
            if available >= quantity:
                # Reduz o estoque disponível
                self._stock[sku] -= quantity
                
                # Gera um ID único para a reserva
                reservation_id = str(uuid.uuid4())
                expires_at = datetime.now() + timedelta(seconds=10)

                self._reservations[reservation_id] = {
                    "sku": sku,
                    "quantity": quantity,
                    "expires_at": expires_at
                }

                print(f"Estoque reservado! SKU: {sku}, Qtd: {quantity}, ID Reserva:{reservation_id}")
                print(f"Estoque atual: {self._stock}")

                return reservation_id
            else:
                print(f"Estoque insuficiente para {sku}. Disponível: {available}, Requerido: {quantity}")
                return None

    def confirm_purchase(self, reservation_id: str) -> str:
        """
        Confirma uma compra, removendo a reserva.
        Se a reserva estiver expirada, o estoque é devolvido.
        Retorna um status: 'SUCCESS', 'NOT_FOUND', ou 'EXPIRED'.
        """
        with self._lock:
            # 1. Verifica se a reserva existe
            reservation = self._reservations.get(reservation_id)
            if not reservation:
                return "NOT_FOUND"

            # 2. Verifica se a reserva expirou
            if datetime.now() > reservation["expires_at"]:
                # Se expirou, devolve o estoque ao pool principal
                sku = reservation["sku"]
                quantity = reservation["quantity"]
                self._stock[sku] += quantity
                
                # Remove a reserva expirada
                del self._reservations[reservation_id]
                
                print(f"Reserva {reservation_id} expirada. Estoque do SKU {sku} devolvido.")
                print(f"Estoque atual: {self._stock}")
                return "EXPIRED"

            # 3. Se a reserva é válida, apenas a remove
            # O estoque já foi decrementado no momento da reserva.
            del self._reservations[reservation_id]
            print(f"Reserva {reservation_id} confirmada com sucesso!")
            return "SUCCESS"


