# Kafka Consumer Service

## Overview

The Kafka Consumer Service is a standalone service that processes price events from Kafka and calculates moving averages. It runs independently from the FastAPI application in its own container.

## Architecture

```
FastAPI App (Producer) → Kafka Topic → Consumer Service → Database
```

## Features

- **Event Processing**: Consumes price events from Kafka
- **Moving Average Calculation**: Calculates 5-point moving averages
- **Database Storage**: Stores calculated averages in PostgreSQL
- **Graceful Shutdown**: Handles SIGINT/SIGTERM signals properly
- **Error Handling**: Comprehensive error handling and logging
- **Auto-restart**: Configured to restart unless explicitly stopped

## Configuration

The consumer service uses the following environment variables:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://arnav:market123@postgres:5432/market_data

# Kafka
KAFKA_BOOTSTRAP_SERVERS=kafka:29092
KAFKA_PRICE_EVENTS_TOPIC=price-events
KAFKA_SECURITY_PROTOCOL=PLAINTEXT
```

## Running the Service

### Using Docker Compose

```bash
# Start all services including consumer
docker-compose up -d

# Start only consumer and dependencies
docker-compose up -d postgres kafka consumer

# View consumer logs
docker-compose logs -f consumer
```

### Manual Testing

```bash
# Test the consumer locally
python scripts/test_consumer.py
```

## Service Lifecycle

### Startup
1. Connects to Kafka using configured bootstrap servers
2. Subscribes to the `price-events` topic
3. Begins polling for messages

### Message Processing
1. Receives price event from Kafka
2. Looks up associated price point in database
3. Retrieves recent prices for the symbol
4. Calculates 5-point moving average
5. Stores result in `moving_averages` table
6. Commits Kafka offset

### Shutdown
1. Receives SIGINT/SIGTERM signal
2. Stops consuming messages
3. Closes Kafka consumer connection
4. Exits gracefully

## Monitoring

### Logs
The service logs all activities with timestamps:
- Consumer startup/shutdown
- Message processing
- Moving average calculations
- Errors and warnings

### Health Check
The container includes a basic health check that verifies the process is running.

## Scaling

You can scale the consumer service independently:

```bash
# Scale to multiple instances
docker-compose up -d --scale consumer=3
```

Each consumer instance will:
- Join the same consumer group (`moving-average-consumer`)
- Automatically partition work among instances
- Process different messages to avoid duplication

## Troubleshooting

### Common Issues

1. **Consumer Not Starting**
   - Check Kafka connectivity: `docker-compose logs kafka`
   - Verify topic exists: `docker exec kafka kafka-topics --list --bootstrap-server localhost:9092`

2. **No Messages Processed**
   - Check if producer is publishing: `docker-compose logs app`
   - Verify consumer group: `docker exec kafka kafka-consumer-groups --bootstrap-server localhost:9092 --describe --group moving-average-consumer`

3. **Database Connection Issues**
   - Check PostgreSQL logs: `docker-compose logs postgres`
   - Verify DATABASE_URL environment variable

### Debug Commands

```bash
# Check consumer status
docker-compose ps consumer

# View real-time logs
docker-compose logs -f consumer

# Access consumer container
docker-compose exec consumer bash

# Check Kafka topics
docker exec kafka kafka-topics --list --bootstrap-server localhost:9092

# Monitor consumer group
docker exec kafka kafka-consumer-groups --bootstrap-server localhost:9092 --describe --group moving-average-consumer
```

## Development

### Local Development

```bash
# Run consumer locally (requires Kafka and PostgreSQL)
python -m app.services.kafka_consumer
```

### Testing

```bash
# Run consumer test
python scripts/test_consumer.py

# Run with specific settings
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/db python -m app.services.kafka_consumer
```

## Integration

The consumer service integrates with:

- **FastAPI App**: Receives price events via Kafka
- **PostgreSQL**: Stores moving averages and reads price data
- **Kafka**: Message queue for event processing

The service is designed to be stateless and can be easily scaled horizontally. 