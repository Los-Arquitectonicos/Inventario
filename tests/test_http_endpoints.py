#!/usr/bin/env python
"""
Quick HTTP test using Python requests (if available) or direct function calls
"""
import os
import sys
import subprocess
import time

# Test if server is running
def test_server_running():
    try:
        import urllib.request
        response = urllib.request.urlopen('http://127.0.0.1:8001/api/productos/', timeout=2)
        return response.getcode() == 200
    except:
        return False

def test_with_curl():
    """Test using curl commands"""
    print("🌐 TESTING HTTP ENDPOINTS WITH CURL")
    print("=" * 50)
    
    tests = [
        {
            "name": "GET Products List",
            "cmd": ["curl", "-s", "-w", "\\nSTATUS:%{http_code}", "http://127.0.0.1:8001/api/productos/"]
        },
        {
            "name": "GET Specific Product",
            "cmd": ["curl", "-s", "-w", "\\nSTATUS:%{http_code}", "http://127.0.0.1:8001/api/productos/1/"]
        },
        {
            "name": "GET Warehouses",
            "cmd": ["curl", "-s", "-w", "\\nSTATUS:%{http_code}", "http://127.0.0.1:8001/api/bodegas/"]
        },
        {
            "name": "POST Create Product",
            "cmd": ["curl", "-s", "-w", "\\nSTATUS:%{http_code}", "-X", "POST", 
                   "-H", "Content-Type: application/json",
                   "-d", '{"nombre":"HTTP Test Product","sku":"HTTP-001","precio_costo":10.0,"precio_venta":20.0}',
                   "http://127.0.0.1:8001/api/productos/crear/"]
        }
    ]
    
    for i, test in enumerate(tests, 1):
        print(f"\n{i}. {test['name']}")
        try:
            result = subprocess.run(test['cmd'], capture_output=True, text=True, timeout=5)
            output = result.stdout
            
            if "STATUS:200" in output or "STATUS:201" in output:
                print("✅ SUCCESS")
                # Show first 200 chars of response
                response_data = output.split("STATUS:")[0]
                if response_data.strip():
                    print(f"Response preview: {response_data[:200]}...")
            else:
                print("❌ FAILED")
                print(f"Output: {output}")
                
        except subprocess.TimeoutExpired:
            print("❌ TIMEOUT")
        except Exception as e:
            print(f"❌ ERROR: {e}")

def main():
    print("🔧 INVENTORY API HTTP TEST")
    print("=" * 40)
    
    # Check if server is running
    if test_server_running():
        print("✅ Server is running on http://127.0.0.1:8001")
        test_with_curl()
    else:
        print("❌ Server not running. Let me start it...")
        
        # Start server
        try:
            subprocess.Popen(["python", "manage.py", "runserver", "8001"], 
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print("🚀 Starting server...")
            time.sleep(4)
            
            if test_server_running():
                print("✅ Server started successfully")
                test_with_curl()
            else:
                print("❌ Failed to start server. Using direct function tests instead.")
                # Fall back to direct testing
                os.system("python test_complete_api.py")
        except Exception as e:
            print(f"❌ Error starting server: {e}")
            print("Using direct function tests instead.")
            os.system("python test_complete_api.py")

if __name__ == "__main__":
    main()