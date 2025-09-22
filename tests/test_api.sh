#!/bin/bash

echo "🚀 Testing Inventory Management API"
echo "=================================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

BASE_URL="http://127.0.0.1:8001"

# Function to test endpoint
test_endpoint() {
    local method=$1
    local endpoint=$2
    local data=$3
    local description=$4
    
    echo -e "\n${BLUE}Testing: $description${NC}"
    echo "Method: $method"
    echo "URL: $BASE_URL$endpoint"
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "$BASE_URL$endpoint")
    elif [ "$method" = "POST" ]; then
        response=$(curl -s -w "\n%{http_code}" -X POST -H "Content-Type: application/json" -d "$data" "$BASE_URL$endpoint")
    elif [ "$method" = "PUT" ]; then
        response=$(curl -s -w "\n%{http_code}" -X PUT -H "Content-Type: application/json" -d "$data" "$BASE_URL$endpoint")
    fi
    
    # Split response and status code
    body=$(echo "$response" | head -n -1)
    status_code=$(echo "$response" | tail -n 1)
    
    echo "Status Code: $status_code"
    echo "Response:"
    echo "$body" | python3 -m json.tool 2>/dev/null || echo "$body"
    
    if [ "$status_code" = "200" ] || [ "$status_code" = "201" ]; then
        echo -e "${GREEN}✅ Test passed${NC}"
        return 0
    else
        echo -e "${RED}❌ Test failed${NC}"
        return 1
    fi
}

echo "Make sure Django server is running on port 8001!"
echo "Run: python manage.py runserver 8001"
echo "Press Enter when ready..."
read

# Test 1: Get all products
test_endpoint "GET" "/api/productos/" "" "Get all products"

# Test 2: Get specific product
test_endpoint "GET" "/api/productos/1/" "" "Get product by ID"

# Test 3: Get all warehouses
test_endpoint "GET" "/api/bodegas/" "" "Get all warehouses"

# Test 4: Get warehouse inventory
test_endpoint "GET" "/api/bodegas/1/inventario/" "" "Get warehouse inventory"

# Test 5: Get articles for a product
test_endpoint "GET" "/api/productos/1/articulos/" "" "Get articles for product"

# Test 6: Create a new product
new_product='{"nombre": "Test Product API", "sku": "TEST-API-001", "precio_costo": 50.00, "precio_venta": 75.00, "descripcion": "Product created via API test", "stock_minimo": 5, "stock_maximo": 100}'
test_endpoint "POST" "/api/productos/crear/" "$new_product" "Create new product"

# Test 7: Add new article
new_article='{"producto_id": 1, "bodega_id": 1, "numero_serie": "TEST123456", "codigo_barras": "1234567890123"}'
test_endpoint "POST" "/api/articulos/agregar/" "$new_article" "Add new article"

# Test 8: Update article status
update_data='{"estado": "vendido", "motivo": "Venta realizada via API test"}'
test_endpoint "PUT" "/api/articulos/1/estado/" "$update_data" "Update article status"

# Test 9: Get article movements
test_endpoint "GET" "/api/articulos/1/movimientos/" "" "Get article movements"

echo -e "\n${BLUE}🏁 API Testing Complete!${NC}"