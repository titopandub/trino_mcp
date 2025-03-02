#!/usr/bin/env python3
"""
Direct test of Trino client session catalog handling.
This script tests various ways to set the catalog name in Trino.
"""
import sys
import time
import traceback
import trino

def test_trino_sessions():
    """Test different approaches to setting the catalog in Trino sessions"""
    print("🔬 Testing Trino session catalog handling")
    
    # Test 1: Default connection and USE statements
    print("\n=== Test 1: Default connection with USE statements ===")
    try:
        conn = trino.dbapi.connect(
            host="trino",
            port=8080,
            user="trino",
            http_scheme="http"
        )
        
        print("Connection established")
        cursor1 = conn.cursor()
        
        # Try to set catalog with USE statement
        print("Setting catalog with USE statement")
        cursor1.execute("USE memory")
        
        # Try a query with the set catalog
        print("Executing query with set catalog")
        try:
            cursor1.execute("SELECT 1 as test")
            result = cursor1.fetchall()
            print(f"Result: {result}")
        except Exception as e:
            print(f"❌ Query failed: {e}")
            
        conn.close()
    except Exception as e:
        print(f"❌ Test 1 failed: {e}")
        traceback.print_exception(type(e), e, e.__traceback__)
    
    # Test 2: Connection with catalog parameter
    print("\n=== Test 2: Connection with catalog parameter ===")
    try:
        conn = trino.dbapi.connect(
            host="trino",
            port=8080,
            user="trino",
            http_scheme="http",
            catalog="memory"
        )
        
        print("Connection established with catalog parameter")
        cursor2 = conn.cursor()
        
        # Try a query with the catalog parameter
        print("Executing query with catalog parameter")
        try:
            cursor2.execute("SELECT 1 as test")
            result = cursor2.fetchall()
            print(f"Result: {result}")
        except Exception as e:
            print(f"❌ Query failed: {e}")
            
        conn.close()
    except Exception as e:
        print(f"❌ Test 2 failed: {e}")
        traceback.print_exception(type(e), e, e.__traceback__)
    
    # Test 3: Explicit catalog in query
    print("\n=== Test 3: Explicit catalog in query ===")
    try:
        conn = trino.dbapi.connect(
            host="trino",
            port=8080,
            user="trino",
            http_scheme="http"
        )
        
        print("Connection established")
        cursor3 = conn.cursor()
        
        # Try a query with explicit catalog in the query
        print("Executing query with explicit catalog")
        try:
            cursor3.execute("SELECT 1 as test FROM memory.information_schema.tables WHERE 1=0")
            result = cursor3.fetchall()
            print(f"Result: {result}")
        except Exception as e:
            print(f"❌ Query failed: {e}")
            
        conn.close()
    except Exception as e:
        print(f"❌ Test 3 failed: {e}")
        traceback.print_exception(type(e), e, e.__traceback__)
    
    # Test 4: Connection parameters with session properties
    print("\n=== Test 4: Connection with session properties ===")
    try:
        conn = trino.dbapi.connect(
            host="trino",
            port=8080,
            user="trino",
            http_scheme="http",
            catalog="memory",
            session_properties={"catalog": "memory"}
        )
        
        print("Connection established with session properties")
        cursor4 = conn.cursor()
        
        # Try a query with session properties
        print("Executing query with session properties")
        try:
            cursor4.execute("SELECT 1 as test")
            result = cursor4.fetchall()
            print(f"Result: {result}")
        except Exception as e:
            print(f"❌ Query failed: {e}")
            
        conn.close()
    except Exception as e:
        print(f"❌ Test 4 failed: {e}")
        traceback.print_exception(type(e), e, e.__traceback__)
    
    print("\n🏁 Testing complete!")

if __name__ == "__main__":
    test_trino_sessions() 