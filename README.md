## A mágica acontecendo
### Foi utilizado o mecanismo de Locking pessimista - A API possui uma "Porta" com a quantidade de items do estoque e para acessar essa informação existe somente uma "Chave"(No código, o objeto threading.Lock), no momento que um cliente adicionar um item ao carrinho ele tenta pegar essa chave para verificar a quantidade de itens no estoque, se a chave estiver disponível ele altera a quantidade do estoque e devolve a chave, se a chave estiver ocupada ele aguarda o outro processo finalizar para só então prosseguir. Este processo garante que a operação crítica de "verificar-e-modificar" o estoque seja indivisível. Isso elimina a race condition e assegura que, mesmo que dois clientes cliquem "comprar" simultaneamente, o último item será vendido de forma justa e consistente para apenas um deles.

### Diagrama de sequência que mostra o funcionamento do Locking Pessimista
```mermaid
sequenceDiagram
    participant Cliente Ana
    participant Cliente Beto
    participant API as Sua API de Estoque
    participant Lock as threading.Lock

    Note over API: Estoque Inicial = 1

    %% Ana inicia a requisição primeiro
    Cliente Ana->>+API: POST /stock/SKU-001/reserve
    API->>+Lock: Tenta adquirir o lock
    Lock-->>-API: Lock adquirido com sucesso!
    
    Note over API: Ana está na seção crítica

    %% Beto tenta ao mesmo tempo, mas fica bloqueado
    Cliente Beto->>+API: POST /stock/SKU-001/reserve
    API->>+Lock: Tenta adquirir o lock (está ocupado)
    Note over Lock: Lock em uso por Ana. Beto deve esperar.

    %% API processa a requisição da Ana sem interrupções
    API-->>API: Verifica estoque (qtd = 1). OK.
    API-->>API: Decrementa estoque para 0.
    API-->>API: Cria reserva para Ana.
    
    API->>Lock: Libera o lock 
    API-->>-Cliente Ana: 200 OK (Reserva Confirmada)

    %% Agora que o lock foi liberado, a requisição do Beto continua
    Lock-->>-API: Lock adquirido com sucesso!
    Note over API: Beto está na seção crítica

    API-->>API: Verifica estoque (qtd = 0). FALHA.
    API->>Lock: Libera o lock 
    API-->>-Cliente Beto: 409 Conflict (Estoque Esgotado)
```

## Diagrama da Arquitetura - Como a API se conecta
```mermaid
graph TD
    subgraph "Cliente"
        A[Shopify / Vitrine do E-commerce]
    end

    subgraph "Arquitetura da API"
        B(API Bázico Stock Service)
    end

    subgraph "Sistema de Gestão (ERP)"
        C[Bling / Fonte da Verdade do Estoque]
    end

    %% Fluxo Principal de Reserva (Alta Frequência)
    A -- "1. Cliente adiciona último item ao carrinho<br>(POST /stock/{sku}/reserve)" --> B;
    B -- "2. Reserva confirmada ou negada<br>(Resposta 200 OK ou 409 Conflict)" --> A;

    %% Fluxo de Confirmação de Compra (Menor Frequência)
    A -- "3. Cliente finaliza a compra" --> B;
    B -- "4. Efetiva a compra - (Resposta 200 Compra efetivada ou 410 Reserva Expirada)<br>(POST /stock/confirm)" --> A;
    B -- "5. Atualiza estoque definitivo no ERP" --> C;

    %% Fluxo de Sincronização Inicial (Baixa Frequência)
    C -- "Quantidade inicial de estoque" --> B;
```

## Relatório de Raciocínio

