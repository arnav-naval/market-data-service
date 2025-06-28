# End-to-End Tests for Market Data Service

This directory contains comprehensive end-to-end tests for the market data service, testing the complete flow from price events to moving average calculations.

## Test Overview

The tests validate the following end-to-end flow:
1. **Price Event Creation** → **Kafka Publishing** → **Consumer Processing** → **Database Storage** → **Moving Average Calculation**

## Test Cases

### 1. Simple Price Event to Moving Average
- Tests the basic flow with a single price event
- Verifies that moving averages are calculated correctly
- Validates database storage

### 2. Multiple Sequential Price Events
- Tests processing multiple price events in sequence
- Verifies that moving averages are updated correctly
- Ensures proper sliding window behavior

### 3. Moving Average Calculation Accuracy
- Tests mathematical accuracy of moving average calculations
- Uses known price sequences for deterministic results
- Validates 5-point moving average calculations

### 4. Upsert Behavior
- Tests that moving averages are properly upserted
- Verifies no duplicate records are created
- Ensures data consistency

## Prerequisites

1. **Services Running**: Ensure all services are running:
   ```bash
   docker-compose up -d
   ```

2. **Dependencies**: Install test dependencies:
   ```bash
   pip install -r tests/requirements-test.txt
   ```

3. **Database**: Ensure the database is initialized:
   ```bash
   python scripts/init_db.py
   ```

## Running Tests

### Option 1: Using the Test Runner
```bash
python tests/run_tests.py
```

### Option 2: Using pytest directly
```bash
# From the project root
pytest -v tests/test_end_to_end.py --asyncio-mode=auto
```

### Option 3: Run specific test
```bash
# Run a specific test method
pytest -v tests/test_end_to_end.py::TestEndToEndFlow::test_simple_price_event_to_moving_average --asyncio-mode=auto

# Run with more verbose output
pytest -v -s tests/test_end_to_end.py --asyncio-mode=auto
```

## Test Configuration

The tests use the following configuration:
- **Database**: PostgreSQL (localhost:5432)
- **Kafka**: localhost:9092
- **Test Data**: Synthetic price data with known values
- **Moving Average**: 5-point moving average
- **Test Symbols**: Unique symbols generated for each test run

## Test Fixtures

The tests use several pytest fixtures:
- `db_session`: Database session for each test
- `kafka_producer`: Kafka producer for publishing events
- `test_symbol`: Unique symbol for each test
- `setup_price_points`: Initial price data setup
- `cleanup_test_data`: Automatic cleanup after tests

## Understanding Test Results

### Success Indicators
- ✅ All price events processed successfully
- ✅ Moving averages calculated with correct values
- ✅ Database records created/updated properly
- ✅ No duplicate records

### Common Issues
- **Connection Errors**: Ensure services are running
- **Database Errors**: Check database initialization
- **Kafka Errors**: Verify Kafka connectivity
- **Calculation Errors**: Check moving average logic

## Adding New Tests

To add new end-to-end tests:

1. Create a new test method in `TestEndToEndFlow` class
2. Use the provided fixtures for setup/teardown
3. Follow the pattern: Setup → Action → Assert
4. Use synthetic data for deterministic results
5. Add proper cleanup in the test method

## Debugging Tests

For debugging test failures:

1. **Enable verbose output**:
   ```bash
   pytest -v -s tests/test_end_to_end.py --asyncio-mode=auto
   ```

2. **Check service logs**:
   ```bash
   docker-compose logs app
   docker-compose logs consumer
   ```

3. **Verify database state**:
   ```bash
   docker-compose exec postgres psql -U arnav -d market_data
   ```

4. **Check Kafka topics**:
   ```bash
   docker-compose exec kafka kafka-topics --list --bootstrap-server localhost:9092
   ``` 