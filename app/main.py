# app/main.py
from fastapi import FastAPI, HTTPException, status
from .stock_manager import StockManager
from . import models

# --- Criação da Aplicação e do Gerenciador de Estoque ---

# Criamos a aplicação FastAPI
app = FastAPI(
    title="Bázico Stock Service",
    description="API para reserva de estoque em tempo real para a BaziWeek.",
    version="1.0.0"
)

# Criamos UMA ÚNICA instância do gerenciador de estoque.
# Ela será compartilhada por todas as requisições da API,
# garantindo que todos vejam o mesmo estado de estoque e usem o mesmo 'lock'.
stock_manager = StockManager()

# --- Endpoints da API ---
@app.get("/stock/{sku}")
def check_availability(sku: str):
    """
    Verifica a quantidade disponível de um SKU.
    """
    print(f"Recebida requisição para consultar o SKU: {sku}")
    
    # Chama o método do nosso gerenciador para obter o dado
    quantity = stock_manager.get_stock_level(sku)
    
    # Se o método retornar None, significa que o SKU não foi encontrado.
    # Lançamos uma exceção HTTP que o FastAPI transformará em um erro 404.
    if quantity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SKU '{sku}' não encontrado."
        )
        
    # Se tudo deu certo, retorna o SKU e sua quantidade.
    return {"sku": sku, "quantity": quantity}

@app.post("/stock/{sku}/reserve", response_model=models.ReservationResponse)
def reserve_item(sku: str):
    """
    Tenta reservar um item do SKU especificado.
    """
    print(f"Recebida requisição para reservar o SKU: {sku}")
    
    # Chama o método do gerenciador para tentar fazer a reserva
    reservation_id = stock_manager.reserve_stock(sku)
    
    # Se o gerenciador retornou None, é porque não há estoque.
    # O código 409 Conflict indica que o estado atual
    # do servidor (sem estoque) impede a execução da requisição.
    if not reservation_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Estoque para o SKU '{sku}' indisponível para reserva."
        )
    
    # Recupera os detalhes da reserva para retornar uma resposta completa
    reservation_details = stock_manager._reservations[reservation_id]

    return models.ReservationResponse(
        reservation_id=reservation_id,
        sku=sku,
        expires_at=reservation_details["expires_at"]
    )

@app.post("/stock/confirm", response_model=models.ConfirmationResponse)
def confirm_item_purchase(request: models.ConfirmationRequest):
    """
    Confirma a compra de um item reservado, efetivando a baixa no estoque.
    """
    reservation_id_str = str(request.reservation_id)
    print(f"Recebida requisição para CONFIRMAR a reserva: {reservation_id_str}")
    
    status_result = stock_manager.confirm_purchase(reservation_id_str)
    
    if status_result == "NOT_FOUND":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reserva com ID '{reservation_id_str}' não encontrada."
        )
    
    if status_result == "EXPIRED":
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail=f"Reserva com ID '{reservation_id_str}' está expirada."
        )
    
    return models.ConfirmationResponse(
        status="SUCCESS",
        message="Compra confirmada e estoque decrementado permanentemente."
    )