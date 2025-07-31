**Expected Timeline:**

- **Task 1:** Setup & Core API (2 hrs)
- **Task 2:** Database & Market Data Integration (2-3 hrs)
- **Task 3:** Kafka Pipeline, Documentation (2–3 hrs)
- **Task 4:** Testing Suite Development (Optional)
- **Task 5:** Docker & CI/CD (Optional)

Build a production-ready microservice that fetches market data, processes it through a streaming pipeline, and serves it via REST APIs. Demonstrate clean code, proper documentation, and DevOps best practices.

- **Endpoints**
    
    ```
    GET /prices/latest?symbol={symbol}&provider={provider?}
    
    ```
    
    **Response:**
    
    ```json
    {
      "symbol": "AAPL",
      "price": 150.25,
      "timestamp": "2024-03-20T10:30:00Z",
      "provider": "alpha_vantage"
    }
    
    ```
    
    ```
    POST /prices/poll
    Content-Type: application/json
    
    {
      "symbols": ["AAPL", "MSFT"],
      "interval": 60,
      "provider": "alpha_vantage"
    }
    
    ```
    
    **Response (202 Accepted):**
    
    ```json
    {
      "job_id": "poll_123",
      "status": "accepted",
      "config": {
        "symbols": ["AAPL", "MSFT"],
        "interval": 60
      }
    }
    
    ```
    
    → You can use FastAPI’s dependency injection for config and a service layer abstraction.
    

- Tables/collections for:
    - raw market data responses
    - processed price points
    - moving averages
    - polling job configs

> Tip: SQLAlchemy ORM with indexes on timestamp & symbol.
> 

Choose **one** provider:

- Alpha Vantage (5 calls/min)
- Yahoo Finance (`yfinance`)
- Finnhub (free tier)

> Tip: Create a provider interface to swap sources easily.
> 
- **Producer:** Publish raw updates to topic `price-events`
- **Consumer:** Compute 5-point moving average, upsert to `symbol_averages`

**Message Schema**

```json
{
  "symbol": "AAPL",
  "price": 150.25,
  "timestamp": "2024-03-20T10:30:00Z",
  "source": "alpha_vantage",
  "raw_response_id": "uuid-here"
}

```

> Use confluent-kafka-python with retries & error handling.
> 
- **Dockerfile** for the FastAPI service
- **docker-compose.yml** for:
    - API service
    - PostgreSQL
    - Kafka + ZooKeeper
    - Adminer (optional)

> Bonus (optional): Deploy to Heroku/AWS – not required, purely bonus.
> 
1. **README.md**
    - Overview, setup, API docs, architecture decisions, local dev, troubleshooting
2. **Architecture Diagrams**
    - **System Architecture Diagram**:
    
    ```mermaid
    graph TB
        subgraph "Market Data Service"
            API["FastAPI Service"]
            DB[(PostgreSQL)]
            Cache[("Redis Cache<br/>")]
        end
        
        subgraph "Message Queue"
            Kafka["Apache Kafka"]
            ZK["ZooKeeper"]
            Producer["Price Producer"]
            Consumer["MA Consumer"]
        end
        
        subgraph "External Services"
            MarketAPI["Market Data API<br/>(Alpha Vantage/YFinance)"]
        end
        
        subgraph "Monitoring"
            Prometheus["Prometheus<br/>[Optional]"]
            Grafana["Grafana<br/>[Optional]"]
        end
        
        Client["Client Application"] --> API
        API --> DB
        API --> Cache
        API --> MarketAPI
        
        API --> Producer
        Producer --> Kafka
        Kafka --> Consumer
        Consumer --> DB
        
        ZK <--> Kafka
        
        API --> Prometheus
        Prometheus --> Grafana
    ```
    
    - **Flow Diagram**: illustrate data movement through the system
        
        ```mermaid
        sequenceDiagram
            participant C as Client
            participant A as FastAPI
            participant M as Market API
            participant K as Kafka
            participant MA as MA Consumer
            participant DB as PostgreSQL
            
            C->>A: GET /prices/latest
            A->>DB: Check cache
            alt Cache miss
                A->>M: Fetch latest price
                M-->>A: Price data
                A->>DB: Store raw response
                A->>K: Produce price event
            end
            A-->>C: Return price
            
            K->>MA: Consume price event
            MA->>DB: Fetch last 5 prices
            MA->>MA: Calculate MA
            MA->>DB: Store MA result
        ```
        
3. **API Documentation**
    - OpenAPI/Swagger spec
    - Example requests/responses, rate limits, error codes
- **Repo Structure**
    
    ```
    market-data-service/
    ├── app/
    │   ├── api/
    │   ├── core/
    │   ├── models/
    │   ├── services/
    │   └── schemas/
    ├── tests(Optional)/
    ├── docs/
    ├── docker(Optional)/
    ├── .github/workflows/
    ├── requirements/
    └── scripts/
    
    ```
    
- **GitHub Actions**
    - Lint (flake8)
    - Test (pytest)
    - Build Docker images
    - (Optional) Deploy to staging

> Tip: Use pre-commit hooks for formatting & basic checks.
> 
- Graceful shutdown
- Logging (ELK)
- Rate limiting
- Caching

Use `pytest`. Example tests:

```python
def test_calculate_moving_average():
    prices = [100,101,99,102,98]
    assert calculate_moving_average(prices) == 100

async def test_get_latest_price():
    r = await client.get("/prices/latest?symbol=AAPL")
    assert r.status_code == 200

```

End-to-end pipeline verification: fetch → DB → Kafka → MA storage.

**Provide a Postman/Insomnia collection with environments & test scripts.**

✅ **Required Deliverables:**

1. **Private GitHub repository with consistent, meaningful commits**
2. **Detailed README.md file with setup instructions, architecture overview, and API documentation**
3. **5-minute video walkthrough (*mandatory*)**
4. **Grant hiring team access (add Yuvraj1907 as a collaborator)**
