# JMeter Load Test for Product Creation

This JMX file is designed to test the product creation endpoint of the inventory management system using Apache JMeter.

## Test Configuration

### Default Settings
- **Threads (Users)**: 10 concurrent users
- **Ramp-up Time**: 30 seconds (gradual user increase)
- **Loops**: 5 iterations per user
- **Server**: http://127.0.0.1:8000 (Django development server)

### What the Test Does

1. **Product Creation Test**: 
   - Creates unique products using dynamic data
   - Uses thread numbers and random values for uniqueness
   - Validates successful creation (200/201 status codes)
   - Checks JSON response structure

2. **Product Listing Test**:
   - Fetches all products after creation
   - Validates the response (200 status code)
   - Includes 1-second delay between requests

## Prerequisites

1. **Apache JMeter**: Download from https://jmeter.apache.org/
2. **Django Server**: Make sure your Django server is running on port 8000

## How to Run

### Option 1: GUI Mode (Recommended for Development)
```bash
# Start your Django server first
cd /Users/pedropablosanintrujillo/GitHub/Inventario
python manage.py runserver 8000

# In another terminal, open JMeter
jmeter -t tests/product_creation_test.jmx
```

### Option 2: Command Line Mode (for CI/CD)
```bash
# Start Django server
python manage.py runserver 8000 &

# Run JMeter test
jmeter -n -t tests/product_creation_test.jmx -l results.jtl -e -o report/

# Stop Django server when done
kill %1
```

### Option 3: Custom Parameters
You can override default settings:
```bash
jmeter -n -t tests/product_creation_test.jmx \
  -Jserver.host=localhost \
  -Jserver.port=8000 \
  -JTHREADS=20 \
  -JRAMP_TIME=60 \
  -JLOOPS=10 \
  -l results.jtl
```

## Test Results Interpretation

### Key Metrics to Monitor
- **Response Time**: How long each request takes
- **Throughput**: Requests per second
- **Error Rate**: Percentage of failed requests
- **Success Rate**: Should be 100% for healthy API

### Expected Behavior
- All requests should return 200 or 201 status codes
- Product creation should return JSON with product ID
- Response times should be consistent (< 1000ms typically)

## Test Data

The test creates products with:
- **Name**: "Test Product JMeter {thread}-{random}"
- **SKU**: "SKU-JMETER-{thread}-{random}"
- **Cost Price**: Random between $10-100
- **Sale Price**: Random between $150-300
- **Description**: Includes thread information
- **Stock Limits**: Random minimum (5-20) and maximum (50-200)

## Assertions Included

1. **HTTP Status Code**: Validates 200/201 responses
2. **JSON Structure**: Ensures product ID is returned
3. **Response Format**: Validates JSON content type

## Troubleshooting

### Common Issues

1. **Connection Refused**
   - Ensure Django server is running on port 8000
   - Check if port is available: `lsof -i :8000`

2. **High Error Rate**
   - Reduce thread count or increase ramp-up time
   - Check Django server logs for errors
   - Verify database connectivity

3. **Slow Response Times**
   - Monitor database performance
   - Check for database locks
   - Consider adding database indexes

### Debugging Tips

1. **Enable View Results Tree**: See individual request/response details
2. **Check Server Logs**: Monitor Django console output
3. **Use Summary Report**: Get overall performance statistics
4. **Graph Results**: Visualize response times over time

## Customization

### Modify Test Parameters
Edit the "User Defined Variables" section in the Test Plan:
- `BASE_URL`: Server address
- `THREADS`: Number of concurrent users
- `RAMP_TIME`: Time to reach full load
- `LOOPS`: Iterations per thread

### Add More Test Scenarios
You can extend this test to include:
- Product updates (PUT requests)
- Product deletion (DELETE requests)
- Article creation after product creation
- Error handling tests (invalid data)

## Integration with CI/CD

Example GitHub Actions workflow:
```yaml
- name: Load Test
  run: |
    python manage.py runserver 8000 &
    sleep 5
    jmeter -n -t tests/product_creation_test.jmx -l results.jtl
    kill %1
```

This JMX file provides a comprehensive load testing solution for your product creation API endpoint.