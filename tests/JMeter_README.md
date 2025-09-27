# JMeter Load Testing Suite for Inventario System

This comprehensive JMeter test suite is designed to perform load testing on the entire Inventario management system, covering all API endpoints with realistic usage patterns.

## Available Test Files

### 1. `inventario_load_test.jmx` - Complete Load Test Suite
Comprehensive load testing covering all API endpoints with realistic scenarios.

### 2. `inventario_get_only_test.jmx` - Product Inventory GET Tests
Focused testing on product and inventory GET operations only.

### 3. `pedidos_get_test.jmx` - Order Management GET Tests ⭐ NEW
Specialized testing for order management system GET operations, including the main `obtener_ubicaciones_productos()` function.

### 4. `product_creation_test.jmx` - Product Creation Focus
Focused testing on product creation endpoint with high concurrency.

## Test Configuration

### Default Settings for Complete Suite (`inventario_load_test.jmx`)
- **Read Operations**: 15 concurrent users (GET requests)
- **Write Operations**: 5 concurrent users (POST/PUT requests)
- **Ramp-up Time**: 30 seconds (gradual user increase)
- **Loops**: 3 iterations per thread
- **Server**: http://127.0.0.1:8000 (configurable)

### What the Complete Suite Tests

#### **Read Operations Thread Group (GET Requests)**
1. **Get All Products** - Tests product listing performance
2. **Get Product by ID** - Tests individual product retrieval with random IDs
3. **Get All Warehouses** - Tests warehouse listing
4. **Get Warehouse Inventory** - Tests complex inventory queries
5. **Get Product Articles** - Tests product-article relationships
6. **Get Article Movements** - Tests movement history tracking

#### **Write Operations Thread Group (POST/PUT Requests)**
1. **Create Products** - Tests product creation with unique data
2. **Add Articles** - Tests article addition to existing products
3. **Update Article Status** - Tests status changes and movement tracking

### Dynamic Data Generation
- **Unique Product Names**: Uses thread numbers and timestamps
- **Random Pricing**: Realistic cost and sale price ranges
- **Random SKUs**: Prevents conflicts during concurrent testing
- **Variable Status Updates**: Tests different article states
- **Time-based Identifiers**: Ensures data uniqueness

## Prerequisites

1. **Apache JMeter**: Download from https://jmeter.apache.org/
2. **Django Server**: Make sure your Django server is running on port 8000

## How to Run

### Preparation
1. **Ensure Test Data Exists**:
   ```bash
   cd /Users/pedropablosanintrujillo/GitHub/Inventario
   python tests/create_test_data.py
   ```

2. **Start Django Server**:
   ```bash
   python manage.py runserver 8000
   ```

### Option 1: Complete Load Test Suite (Recommended)
```bash
# GUI Mode (for development and monitoring)
jmeter -t tests/inventario_load_test.jmx

# Command Line Mode (for CI/CD)
jmeter -n -t tests/inventario_load_test.jmx -l results.jtl -e -o report/
```

### Option 2: Product Inventory GET Tests
```bash
# GUI Mode
jmeter -t tests/inventario_get_only_test.jmx

# Command Line Mode
jmeter -n -t tests/inventario_get_only_test.jmx -l inventory_results.jtl -e -o inventory_report/
```

### Option 3: Order Management GET Tests (PEDIDOS) ⭐
```bash
# GUI Mode
jmeter -t tests/pedidos_get_test.jmx

# Command Line Mode - Tests the main obtener_ubicaciones_productos() function
jmeter -n -t tests/pedidos_get_test.jmx -l orders_results.jtl -e -o orders_report/

# With custom parameters
jmeter -n -t tests/pedidos_get_test.jmx \
  -Jthreads=20 \
  -Jramp.time=30 \
  -Jloops=5 \
  -l orders_stress.jtl \
  -e -o orders_stress_report/
```

### Option 4: Product Creation Focus Test
```bash
# GUI Mode
jmeter -t tests/product_creation_test.jmx

# Command Line Mode
jmeter -n -t tests/product_creation_test.jmx -l product_results.jtl -e -o product_report/
```

## Test Focus: Order Management System (`pedidos_get_test.jmx`)

### Endpoints Tested
1. **GET /pedidos/** - Lista todos los pedidos
2. **GET /pedidos/{id}/** - Obtiene pedido específico
3. **GET /pedidos/{id}/detalles/** - Detalles del pedido
4. **GET /pedidos/{id}/ubicaciones/** - 🎯 **FUNCIÓN PRINCIPAL** `obtener_ubicaciones_productos()`

### Test Configuration for Orders
- **Threads**: 15 concurrent users (configurable)
- **Ramp-up**: 20 seconds
- **Loops**: 3 iterations per thread
- **Timer**: 800ms between requests
- **Timeouts**: 10s normal, 15s for ubicaciones (complex query)

### What Makes This Test Special
This test specifically validates the **core requested functionality**:
- **Products**: Returns product names and quantities
- **Quantities**: Shows requested amounts per order
- **Locations**: Shows warehouse locations for each product
- **Performance**: Tests the complex join queries in `obtener_ubicaciones_productos()`

### Expected JSON Response for Main Function
```json
{
  "pedido_id": 1,
  "productos_ubicaciones": [
    {
      "producto_nombre": "Laptop Dell",
      "cantidad_solicitada": 2,
      "articulos_disponibles": [
        {
          "articulo_id": 101,
          "codigo": "LAP001", 
          "ubicacion": "Bodega A - Zona Electrónicos"
        }
      ]
    }
  ]
}
```

### Assertions for Orders Test
- **HTTP 200**: All requests must succeed
- **JSON Structure**: Validates pedidos array, detalles structure
- **Core Function**: Validates pedido_id and productos_ubicaciones fields
- **Data Integrity**: Ensures all required fields are present

### Option 5: Custom Parameters for Load Test
You can override default settings:
```bash
jmeter -n -t tests/inventario_load_test.jmx \
  -Jserver.host=127.0.0.1 \
  -Jserver.port=8000 \
  -Jread.threads=25 \
  -Jwrite.threads=8 \
  -Jramp.time=45 \
  -Jloops=5 \
  -l custom_results.jtl \
  -e -o custom_report/
```

### Option 4: High Load Testing
For stress testing:
```bash
jmeter -n -t tests/inventario_load_test.jmx \
  -Jread.threads=50 \
  -Jwrite.threads=15 \
  -Jramp.time=60 \
  -Jloops=10 \
  -l stress_test.jtl \
  -e -o stress_report/
```

## Test Results Interpretation

### Key Metrics to Monitor

#### **Performance Metrics**
- **Average Response Time**: Should be < 500ms for GET, < 1000ms for POST/PUT
- **95th Percentile**: Should be < 1000ms for GET, < 2000ms for POST/PUT
- **Throughput**: Target 50+ req/sec for reads, 10+ req/sec for writes
- **Error Rate**: Should be 0% under normal load

#### **Expected Response Times by Endpoint**
- **GET /api/productos/**: 50-200ms (simple list)
- **GET /api/bodegas/{id}/inventario/**: 200-800ms (complex query)
- **POST /api/productos/crear/**: 300-1000ms (database write)
- **POST /api/articulos/agregar/**: 200-600ms (simple insert)
- **PUT /api/articulos/{id}/estado/**: 300-800ms (update + movement log)

#### **Scalability Indicators**
- **Linear Response Time**: Response times should scale linearly with load
- **Stable Throughput**: Throughput should remain stable during test
- **Memory Usage**: Django server memory should remain stable
- **Database Connections**: Should not exceed connection pool limits

## Test Data Patterns

### Products Created
- **Name**: "Load Test Product {thread}-{random}"
- **SKU**: "LOAD-{thread}-{random}" (unique identifier)
- **Cost Price**: $50-200 (random with cents)
- **Sale Price**: $250-500 (realistic markup)
- **Description**: Includes thread info and timestamp
- **Stock Limits**: Min 5-25, Max 100-300

### Articles Added
- **Product ID**: Random from existing products (1-6)
- **Warehouse ID**: Random from existing warehouses (1-2)
- **Serial Number**: "LOAD-{thread}-{random6digits}"
- **Barcode**: 13-digit random number
- **Lot**: "LOTE-{random4digits}"

### Status Updates
- **States**: Random from "reservado", "vendido", "mantenimiento"
- **Reasons**: Include thread info and timestamp
- **Movement Tracking**: Automatically logged in MovimientoArticulo

## Assertions and Validations

### HTTP Response Assertions
- **GET Requests**: Must return 200 OK
- **POST Requests**: Must return 200 OK or 201 Created
- **PUT Requests**: Must return 200 OK

### JSON Structure Assertions
- **Product Lists**: Must contain "productos" array
- **Product Creation**: Must return product with "id" field
- **Article Addition**: Must return "success": true
- **Status Updates**: Must return success confirmation

### Performance Assertions (Optional)
Can be enabled for performance requirements:
- **Response Time**: < 2000ms for all requests
- **Throughput**: > 10 requests/second minimum

### Content Type Validation
- All responses must be "application/json"
- Request headers properly set for JSON content

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
The complete load test supports these variables:
- `SERVER_HOST`: Server address (default: 127.0.0.1)
- `SERVER_PORT`: Server port (default: 8000)
- `READ_THREADS`: Concurrent read operations (default: 15)
- `WRITE_THREADS`: Concurrent write operations (default: 5)
- `RAMP_TIME`: Time to reach full load (default: 30s)
- `LOOPS`: Iterations per thread (default: 3)

### Test Scenarios Extension
You can extend these tests to include:

#### **Additional Read Scenarios**
- Category-based product filtering
- Supplier-based queries
- Date-range movement queries
- Advanced inventory reporting

#### **Additional Write Scenarios**
- Product updates (PUT /api/productos/{id}/)
- Product deletion (DELETE requests)
- Bulk operations
- Category and supplier management

#### **Error Handling Tests**
- Invalid product IDs
- Malformed JSON data
- Missing required fields
- Database constraint violations

### Thread Group Customization
```xml
<!-- Example: Add a third thread group for admin operations -->
<ThreadGroup testname="Admin Operations">
  <stringProp name="ThreadGroup.num_threads">2</stringProp>
  <stringProp name="ThreadGroup.ramp_time">10</stringProp>
  <!-- Add admin-specific endpoints -->
</ThreadGroup>
```

## Integration with CI/CD

### GitHub Actions Example
```yaml
name: Load Testing
on: [push, pull_request]

jobs:
  load-test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Setup database
      run: |
        python manage.py migrate
        python tests/create_test_data.py
    
    - name: Start Django server
      run: |
        python manage.py runserver 8000 &
        sleep 10
    
    - name: Install JMeter
      run: |
        wget https://dlcdn.apache.org/jmeter/binaries/apache-jmeter-5.6.2.tgz
        tar -xzf apache-jmeter-5.6.2.tgz
    
    - name: Run Load Tests
      run: |
        ./apache-jmeter-5.6.2/bin/jmeter -n \
          -t tests/inventario_load_test.jmx \
          -Jread.threads=10 \
          -Jwrite.threads=3 \
          -Jloops=2 \
          -l load_test_results.jtl \
          -e -o load_test_report/
    
    - name: Upload Results
      uses: actions/upload-artifact@v2
      with:
        name: load-test-results
        path: load_test_report/
```

### Jenkins Pipeline Example
```groovy
pipeline {
    agent any
    stages {
        stage('Setup') {
            steps {
                sh 'pip install -r requirements.txt'
                sh 'python manage.py migrate'
                sh 'python tests/create_test_data.py'
            }
        }
        stage('Load Test') {
            steps {
                sh 'python manage.py runserver 8000 &'
                sh 'sleep 10'
                sh '''
                    jmeter -n -t tests/inventario_load_test.jmx \
                    -l results.jtl -e -o report/
                '''
            }
            post {
                always {
                    publishHTML([
                        allowMissing: false,
                        alwaysLinkToLastBuild: true,
                        keepAll: true,
                        reportDir: 'report',
                        reportFiles: 'index.html',
                        reportName: 'JMeter Load Test Report'
                    ])
                }
            }
        }
    }
}
```

## Test Results Analysis

### Report Files Generated
- **index.html**: Main dashboard with overview
- **content/pages/**: Detailed reports by request type
- **content/js/**: Interactive charts and graphs
- **statistics.json**: Raw performance data

### Key Reports to Review
1. **Dashboard**: Overall performance summary
2. **APDEX**: Application Performance Index
3. **Requests Summary**: Per-endpoint performance
4. **Errors Report**: Failed request analysis
5. **Response Times Over Time**: Performance trends

This comprehensive JMeter suite provides enterprise-grade load testing for your complete Inventario system.