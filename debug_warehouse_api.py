#!/usr/bin/env python3
"""
Debug script to test warehouse and inventory APIs
"""
import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def test_warehouses():
    """Test warehouse listing API"""
    print("=== Testing Warehouses API ===")
    try:
        response = requests.get(f"{BASE_URL}/api/warehousing/warehouses/?status=ACTIVE")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            warehouses = data.get('results', [])
            print(f"Found {len(warehouses)} warehouses:")
            for wh in warehouses:
                print(f"  - {wh.get('code')} ({wh.get('name')}) - ID: {wh.get('id')}")
            return warehouses
        else:
            print(f"Error: {response.text}")
            return []
    except Exception as e:
        print(f"Exception: {e}")
        return []

def test_warehouse_stock(warehouse_id):
    """Test warehouse stock summary API"""
    print(f"\n=== Testing Stock API for Warehouse {warehouse_id} ===")
    try:
        response = requests.get(f"{BASE_URL}/api/warehousing/warehouses/{warehouse_id}/physical_stock_summary/")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            items = data.get('items', [])
            print(f"Found {len(items)} items with stock:")
            for item in items[:10]:  # Show first 10 items
                print(f"  - {item.get('item_sku')}: {item.get('qty')} units")
            if len(items) > 10:
                print(f"  ... and {len(items) - 10} more items")
            return items
        else:
            print(f"Error: {response.text}")
            return []
    except Exception as e:
        print(f"Exception: {e}")
        return []

def test_catalog_items():
    """Test catalog items API"""
    print(f"\n=== Testing Catalog Items API ===")
    try:
        response = requests.get(f"{BASE_URL}/api/catalog/items/?status=ACTIVE&page_size=100")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            items = data.get('results', [])
            print(f"Found {len(items)} catalog items:")
            for item in items[:5]:  # Show first 5 items
                print(f"  - {item.get('sku')}: {item.get('name')}")
            return items
        else:
            print(f"Error: {response.text}")
            return []
    except Exception as e:
        print(f"Exception: {e}")
        return []

def main():
    print("Warehouse API Debug Tool")
    print("=" * 50)
    
    # Test warehouses
    warehouses = test_warehouses()
    
    # Test catalog items
    catalog_items = test_catalog_items()
    
    # Test stock for each warehouse
    for warehouse in warehouses:
        warehouse_id = warehouse.get('id')
        warehouse_code = warehouse.get('code')
        print(f"\n=== Testing Stock for {warehouse_code} (ID: {warehouse_id}) ===")
        stock_items = test_warehouse_stock(warehouse_id)
        
        if warehouse_code == 'BDVWH':
            print(f"\n*** BDVWH Stock Summary ***")
            print(f"Total items with stock: {len(stock_items)}")
            positive_stock = [item for item in stock_items if item.get('qty', 0) > 0]
            print(f"Items with positive stock: {len(positive_stock)}")

if __name__ == "__main__":
    main()
