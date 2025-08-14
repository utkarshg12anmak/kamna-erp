"""
Frontend smoke tests for inventory management templates
"""
import requests
from bs4 import BeautifulSoup


def test_inventory_frontend():
    """Test that all inventory management pages render correctly"""
    base_url = "http://127.0.0.1:8000"
    
    # Test pages (without authentication for smoke test)
    test_pages = [
        "/app/inventory",
        "/app/inventory/stn", 
        "/app/inventory/stn/new"
    ]
    
    print("🧪 Testing Inventory Management Frontend Pages")
    print("=" * 50)
    
    for page in test_pages:
        url = f"{base_url}{page}"
        try:
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ {page} - OK ({response.status_code})")
                
                # Parse HTML to check for basic elements
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Check for Bootstrap CSS
                bootstrap_css = soup.find('link', {'href': lambda x: x and 'bootstrap' in x})
                if bootstrap_css:
                    print(f"   📦 Bootstrap CSS found")
                
                # Check for title
                title = soup.find('title')
                if title:
                    print(f"   📄 Title: {title.get_text()}")
                
                # Check for main content
                main_content = soup.find(id='moduleContent') or soup.find('div', class_='card-like')
                if main_content:
                    print(f"   📝 Main content container found")
                
                # Check for specific inventory elements
                if 'inventory' in page:
                    if 'STN' in response.text or 'Stock Transfer' in response.text:
                        print(f"   📋 Inventory-specific content found")
                
            elif response.status_code == 302:
                print(f"🔄 {page} - Redirect ({response.status_code}) - likely auth required")
            else:
                print(f"❌ {page} - Error ({response.status_code})")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ {page} - Connection error: {e}")
        
        print()
    
    print("🏁 Frontend smoke test completed")


if __name__ == "__main__":
    test_inventory_frontend()
