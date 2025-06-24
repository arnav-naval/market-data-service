# Kafka Producer Setup and Usage

## Overview

The Kafka producer is integrated into the market data service to publish price events for downstream processing. When a price is fetched from an external provider, it's stored in the database and then published to Kafka for further processing (like calculating moving averages).

## Architecture

```
FastAPI → Market Data Service → Kafka Producer → price-events topic
```

## Configuration

The Kafka producer is configured via environment variables:

```bash
# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_PRICE_EVENTS_TOPIC=price-events
KAFKA_SECURITY_PROTOCOL=PLAINTEXT
```

## Message Schema

Price events are published with the following schema:

```json
{
  "symbol": "AAPL",
  "price": 150.25,
  "timestamp": "2024-03-20T10:30:00Z",
  "source": "alpha_vantage",
  "raw_response_id": "uuid-here"
}
```

## Usage

### 1. Start the Services

```bash
# Start all services including Kafka
docker-compose up -d

# Or start just Kafka and dependencies
docker-compose up -d zookeeper kafka
```

### 2. Test the Producer

```bash
# Run the test script
python scripts/test_kafka_producer.py
```

### 3. Monitor Messages

Access Kafka UI at http://localhost:8080 to monitor:
- Topics
- Messages
- Consumer groups
- Broker status

### 4. API Usage

The Kafka producer is automatically used when you call the API:

```bash
# This will fetch price, store raw data, and publish to Kafka
curl "http://localhost:8000/v1/prices/latest?symbol=AAPL"
```

## Producer Features

- **Reliable Delivery**: Uses `acks=all` for maximum reliability
- **Retries**: Automatically retries failed messages (3 attempts)
- **Compression**: Uses Snappy compression for efficiency
- **Batching**: Batches messages for better throughput
- **Error Handling**: Comprehensive error handling and logging
- **Graceful Shutdown**: Properly closes connections on shutdown

## Troubleshooting

### Common Issues

1. **Connection Refused**
   - Ensure Kafka is running: `docker-compose ps`
   - Check bootstrap servers configuration

2. **Topic Not Found**
   - Kafka auto-creates topics by default
   - Check `KAFKA_AUTO_CREATE_TOPICS_ENABLE=true`

3. **Message Not Delivered**
   - Check producer logs for errors
   - Verify topic exists and is accessible

### Debug Commands

```bash
# Check Kafka status
docker-compose logs kafka

# List topics
docker exec kafka kafka-topics --list --bootstrap-server localhost:9092

# Monitor messages
docker exec kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic price-events --from-beginning
```

## Next Steps

The Kafka producer is ready for consumers to process price events. Next, implement:
1. Kafka consumer for moving average calculation
2. Additional event types (alerts, notifications)
3. Event sourcing and replay capabilities 