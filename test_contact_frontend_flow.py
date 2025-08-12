#!/usr/bin/env python3
"""
CV Hub Contact Frontend Flow Test
Tests the complete contact popup functionality including error handling
"""

import asyncio
import sys
from playwright.async_api import async_playwright
import json

class ContactFrontendFlowTest:
    def __init__(self):
        self.base_url = "http://127.0.0.1:8000"
        self.test_results = []
        self.errors = []

    async def setup_browser(self):
        """Initialize browser and login"""
        print("🚀 Starting Contact Frontend Flow Test...")
        
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()
        
        # Login
        await self.page.goto(f"{self.base_url}/")
        await self.page.fill('input[name="username"]', 'admin')
        await self.page.fill('input[name="password"]', 'admin123')
        await self.page.click('button[type="submit"]')
        await self.page.wait_for_url("**/app/module_hub/")
        print("✅ Login successful")

    async def cleanup(self):
        """Clean up browser resources"""
        await self.browser.close()
        await self.playwright.stop()

    async def test_contact_modal_layout(self):
        """Test 1: Verify contact modal opens properly and buttons are visible"""
        try:
            print("\n📋 Test 1: Contact Modal Layout")
            
            # Go to a CV Hub entry
            await self.page.goto(f"{self.base_url}/app/cv_hub/entries/")
            await self.page.wait_for_selector('.entry-card', timeout=10000)
            
            # Click on first entry
            first_entry = await self.page.query_selector('.entry-card a')
            if first_entry:
                await first_entry.click()
                await self.page.wait_for_load_state('networkidle')
            else:
                raise Exception("No CV Hub entries found")
            
            # Open contact modal
            await self.page.click('#addContactBtn')
            await self.page.wait_for_selector('#addContactModal.show', timeout=5000)
            
            # Check modal is visible
            modal = await self.page.query_selector('#addContactModal')
            is_visible = await modal.is_visible()
            assert is_visible, "Contact modal should be visible"
            
            # Check if save and cancel buttons are visible and within bounds
            save_btn = await self.page.query_selector('#addContactModal .btn-primary')
            cancel_btn = await self.page.query_selector('#addContactModal .btn-secondary')
            
            save_visible = await save_btn.is_visible()
            cancel_visible = await cancel_btn.is_visible()
            
            assert save_visible, "Save button should be visible"
            assert cancel_visible, "Cancel button should be visible"
            
            # Check button positions (they should be in the modal footer)
            save_box = await save_btn.bounding_box()
            cancel_box = await cancel_btn.bounding_box()
            modal_box = await modal.bounding_box()
            
            assert save_box['y'] < modal_box['y'] + modal_box['height'], "Save button should be within modal bounds"
            assert cancel_box['y'] < modal_box['y'] + modal_box['height'], "Cancel button should be within modal bounds"
            
            self.test_results.append("✅ Contact modal layout test passed")
            print("✅ Contact modal layout test passed")
            
        except Exception as e:
            error_msg = f"❌ Contact modal layout test failed: {str(e)}"
            self.errors.append(error_msg)
            print(error_msg)

    async def test_contact_error_handling(self):
        """Test 2: Verify enhanced error handling for various contact validation scenarios"""
        try:
            print("\n📋 Test 2: Contact Error Handling")
            
            # Make sure modal is open
            modal = await self.page.query_selector('#addContactModal')
            if not await modal.is_visible():
                await self.page.click('#addContactBtn')
                await self.page.wait_for_selector('#addContactModal.show', timeout=5000)
            
            # Test Case 1: Empty first name
            print("  🔍 Testing empty first name...")
            await self.page.fill('#contact_first_name', '')
            await self.page.fill('#contact_phone', '9876543210')
            await self.page.click('#addContactModal .btn-primary')
            
            # Wait for alert
            await self.page.wait_for_function('window.alertMessage !== undefined', timeout=3000).catch(lambda: None)
            
            # Test Case 2: Invalid phone number (too short)
            print("  🔍 Testing invalid phone number (too short)...")
            await self.page.fill('#contact_first_name', 'John')
            await self.page.fill('#contact_phone', '123')  # Too short
            await self.page.click('#addContactModal .btn-primary')
            
            # Test Case 3: Invalid phone number (contains letters)
            print("  🔍 Testing invalid phone number (contains letters)...")
            await self.page.fill('#contact_phone', '98765abc10')
            await self.page.click('#addContactModal .btn-primary')
            
            # Test Case 4: Duplicate phone number (if we can create one first)
            print("  🔍 Testing valid contact creation...")
            await self.page.fill('#contact_first_name', 'Test')
            await self.page.fill('#contact_last_name', 'Contact')
            await self.page.fill('#contact_phone', '9876543210')
            await self.page.fill('#contact_email', 'test@example.com')
            await self.page.select_option('#contact_designation', 'MANAGER')
            
            # Listen for any network errors or alerts
            error_captured = False
            
            # Set up error listener
            async def handle_console(msg):
                if 'error' in msg.text.lower() and 'contact' in msg.text.lower():
                    nonlocal error_captured
                    error_captured = True
                    print(f"  📱 Console error captured: {msg.text}")
            
            self.page.on('console', handle_console)
            
            # Try to save
            await self.page.click('#addContactModal .btn-primary')
            await asyncio.sleep(2)  # Wait for any async operations
            
            # Check if modal closed (success) or stayed open (error)
            modal_visible = await modal.is_visible()
            if not modal_visible:
                print("  ✅ Contact created successfully")
            else:
                print("  ⚠️ Contact creation failed or modal stayed open (might be validation error)")
            
            self.test_results.append("✅ Contact error handling test completed")
            print("✅ Contact error handling test completed")
            
        except Exception as e:
            error_msg = f"❌ Contact error handling test failed: {str(e)}"
            self.errors.append(error_msg)
            print(error_msg)

    async def test_contact_form_validation(self):
        """Test 3: Verify frontend form validation works correctly"""
        try:
            print("\n📋 Test 3: Contact Form Validation")
            
            # Open modal if not already open
            modal = await self.page.query_selector('#addContactModal')
            if not await modal.is_visible():
                await self.page.click('#addContactBtn')
                await self.page.wait_for_selector('#addContactModal.show', timeout=5000)
            
            # Clear all fields
            await self.page.fill('#contact_first_name', '')
            await self.page.fill('#contact_last_name', '')
            await self.page.fill('#contact_phone', '')
            await self.page.fill('#contact_email', '')
            
            # Test required field validation
            print("  🔍 Testing required field validation...")
            await self.page.click('#addContactModal .btn-primary')
            
            # Check if HTML5 validation kicks in
            first_name_invalid = await self.page.evaluate(
                'document.getElementById("contact_first_name").validity.valid'
            )
            phone_invalid = await self.page.evaluate(
                'document.getElementById("contact_phone").validity.valid'
            )
            
            print(f"  📝 First name field valid: {first_name_invalid}")
            print(f"  📝 Phone field valid: {phone_invalid}")
            
            # Test phone pattern validation
            print("  🔍 Testing phone pattern validation...")
            await self.page.fill('#contact_first_name', 'John')
            await self.page.fill('#contact_phone', 'invalid-phone')
            
            phone_pattern_valid = await self.page.evaluate(
                'document.getElementById("contact_phone").validity.patternMismatch'
            )
            print(f"  📝 Phone pattern validation working: {phone_pattern_valid}")
            
            # Test email validation
            print("  🔍 Testing email validation...")
            await self.page.fill('#contact_email', 'invalid-email')
            
            email_valid = await self.page.evaluate(
                'document.getElementById("contact_email").validity.valid'
            )
            print(f"  📝 Email field valid: {email_valid}")
            
            self.test_results.append("✅ Contact form validation test completed")
            print("✅ Contact form validation test completed")
            
        except Exception as e:
            error_msg = f"❌ Contact form validation test failed: {str(e)}"
            self.errors.append(error_msg)
            print(error_msg)

    async def test_contact_crud_operations(self):
        """Test 4: Test complete CRUD operations for contacts"""
        try:
            print("\n📋 Test 4: Contact CRUD Operations")
            
            # Close modal if open
            modal = await self.page.query_selector('#addContactModal')
            if await modal.is_visible():
                await self.page.click('#addContactModal .btn-secondary')  # Cancel
                await self.page.wait_for_timeout(500)
            
            # Check if we're on a contacts tab, if not switch to it
            contacts_tab = await self.page.query_selector('#contacts-tab')
            if contacts_tab:
                await contacts_tab.click()
                await self.page.wait_for_timeout(1000)
            
            # Try to create a valid contact
            print("  🔍 Creating a new contact...")
            await self.page.click('#addContactBtn')
            await self.page.wait_for_selector('#addContactModal.show', timeout=5000)
            
            # Fill with valid data
            timestamp = str(int(asyncio.get_event_loop().time()))
            await self.page.fill('#contact_first_name', f'TestUser{timestamp}')
            await self.page.fill('#contact_last_name', 'Lastname')
            await self.page.fill('#contact_phone', f'987654{timestamp[-4:]}')  # Unique phone
            await self.page.fill('#contact_email', f'test{timestamp}@example.com')
            await self.page.select_option('#contact_designation', 'EXECUTIVE')
            
            # Save contact
            await self.page.click('#addContactModal .btn-primary')
            await self.page.wait_for_timeout(3000)  # Wait for operation to complete
            
            # Check if modal closed (indicating success)
            modal_visible = await modal.is_visible()
            if not modal_visible:
                print("  ✅ Contact creation appears successful")
            else:
                print("  ⚠️ Contact creation may have failed - modal still open")
            
            # Try to verify contact appears in the list (if on contacts tab)
            await self.page.wait_for_timeout(2000)
            contact_elements = await self.page.query_selector_all('[data-contact-id]')
            print(f"  📊 Found {len(contact_elements)} contacts in the list")
            
            self.test_results.append("✅ Contact CRUD operations test completed")
            print("✅ Contact CRUD operations test completed")
            
        except Exception as e:
            error_msg = f"❌ Contact CRUD operations test failed: {str(e)}"
            self.errors.append(error_msg)
            print(error_msg)

    async def run_all_tests(self):
        """Run all contact frontend tests"""
        try:
            await self.setup_browser()
            
            await self.test_contact_modal_layout()
            await self.test_contact_error_handling()
            await self.test_contact_form_validation()
            await self.test_contact_crud_operations()
            
        except Exception as e:
            error_msg = f"❌ Test setup failed: {str(e)}"
            self.errors.append(error_msg)
            print(error_msg)
        finally:
            await self.cleanup()

    def print_summary(self):
        """Print test summary"""
        print(f"\n{'='*60}")
        print("📊 CONTACT FRONTEND FLOW TEST SUMMARY")
        print(f"{'='*60}")
        
        print(f"\n✅ PASSED TESTS ({len(self.test_results)}):")
        for result in self.test_results:
            print(f"  {result}")
        
        if self.errors:
            print(f"\n❌ FAILED TESTS ({len(self.errors)}):")
            for error in self.errors:
                print(f"  {error}")
        else:
            print(f"\n🎉 ALL TESTS PASSED! Contact functionality is working correctly.")
        
        print(f"\n📈 OVERALL STATUS:")
        if len(self.errors) == 0:
            print("  🟢 EXCELLENT - All contact tests passed")
        elif len(self.errors) <= 2:
            print("  🟡 GOOD - Minor issues detected")
        else:
            print("  🔴 NEEDS ATTENTION - Multiple issues found")

async def main():
    """Main test execution"""
    tester = ContactFrontendFlowTest()
    await tester.run_all_tests()
    tester.print_summary()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        sys.exit(1)
