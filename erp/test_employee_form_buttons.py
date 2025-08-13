#!/usr/bin/env python3
"""
Test script to verify Employee Form Save Button functionality
Tests both Save Employee and Save as Draft button interactions
"""

import os

def test_employee_form_buttons():
    """Test that save buttons are properly implemented in employee form"""
    print("🔧 Testing Employee Form Save Button Functionality")
    print("=" * 60)
    
    template_path = "/Users/dealshare/Documents/GitHub/kamna-erp/erp/templates/hr/employee_form.html"
    
    if not os.path.exists(template_path):
        print("❌ Employee form template not found")
        return False
    
    with open(template_path, 'r') as f:
        content = f.read()
    
    # Test 1: Check button structure
    print("\n1️⃣ Testing Button Structure...")
    
    save_employee_button = 'button[form="employeeForm"]' in content
    save_draft_button = 'id="saveAsDraft"' in content
    
    if save_employee_button:
        print("✅ Save Employee button found with correct form attribute")
    else:
        print("❌ Save Employee button missing or incorrectly configured")
    
    if save_draft_button:
        print("✅ Save as Draft button found")
    else:
        print("❌ Save as Draft button missing")
    
    # Test 2: Check event listeners
    print("\n2️⃣ Testing Event Listeners...")
    
    event_listeners_count = content.count('addEventListener')
    form_submit_listener = 'form.addEventListener(\'submit\'' in content
    draft_click_listener = 'saveAsDraft').addEventListener(\'click\'' in content
    save_button_click = 'saveButton.addEventListener(\'click\'' in content
    
    print(f"✅ Total addEventListener calls: {event_listeners_count}")
    
    if form_submit_listener:
        print("✅ Form submit listener implemented")
    else:
        print("❌ Form submit listener missing")
    
    if draft_click_listener:
        print("✅ Save as Draft click listener implemented")
    else:
        print("❌ Save as Draft click listener missing")
    
    if save_button_click:
        print("✅ Additional save button click listener implemented")
    else:
        print("⚠️  Additional save button click listener not found")
    
    # Test 3: Check saveEmployee function
    print("\n3️⃣ Testing saveEmployee Function...")
    
    save_function = 'async function saveEmployee(' in content
    loading_state = 'spinner-border spinner-border-sm' in content
    validation_check = 'validateForm()' in content
    toast_notifications = 'showToast(' in content
    
    if save_function:
        print("✅ saveEmployee function implemented")
    else:
        print("❌ saveEmployee function missing")
    
    if loading_state:
        print("✅ Loading state with spinner implemented")
    else:
        print("❌ Loading state missing")
    
    if validation_check:
        print("✅ Form validation check implemented")
    else:
        print("❌ Form validation missing")
    
    if toast_notifications:
        print("✅ Toast notifications implemented")
    else:
        print("❌ Toast notifications missing")
    
    # Test 4: Check for duplicate event listeners (common issue)
    print("\n4️⃣ Testing for Duplicate Event Listeners...")
    
    submit_listeners = content.count('addEventListener(\'submit\'')
    click_listeners = content.count('saveAsDraft\').addEventListener(\'click\'')
    
    if submit_listeners == 1:
        print("✅ Single form submit listener (no duplicates)")
    else:
        print(f"⚠️  Multiple form submit listeners found: {submit_listeners}")
    
    if click_listeners == 1:
        print("✅ Single Save as Draft listener (no duplicates)")
    else:
        print(f"⚠️  Multiple Save as Draft listeners found: {click_listeners}")
    
    # Test 5: Check error handling
    print("\n5️⃣ Testing Error Handling...")
    
    try_catch = 'try {' in content and 'catch (error)' in content
    finally_block = 'finally {' in content
    button_restore = 'saveButton.disabled = false' in content
    
    if try_catch:
        print("✅ Try-catch error handling implemented")
    else:
        print("❌ Try-catch error handling missing")
    
    if finally_block:
        print("✅ Finally block for cleanup implemented")
    else:
        print("❌ Finally block missing")
    
    if button_restore:
        print("✅ Button state restoration implemented")
    else:
        print("❌ Button state restoration missing")
    
    # Test 6: Check debug logging
    print("\n6️⃣ Testing Debug Features...")
    
    debug_logs = content.count('console.log(')
    
    if debug_logs >= 3:
        print(f"✅ Debug logging implemented ({debug_logs} console.log statements)")
    else:
        print(f"⚠️  Limited debug logging ({debug_logs} console.log statements)")
    
    print("\n" + "=" * 60)
    print("🎯 DIAGNOSIS SUMMARY:")
    
    all_checks = [
        save_employee_button,
        save_draft_button,
        form_submit_listener,
        draft_click_listener,
        save_function,
        loading_state,
        validation_check,
        toast_notifications,
        try_catch,
        finally_block
    ]
    
    passed_checks = sum(all_checks)
    total_checks = len(all_checks)
    
    print(f"   📊 Checks passed: {passed_checks}/{total_checks}")
    
    if passed_checks >= 8:
        print("   ✅ Employee form save buttons should be working correctly")
        print("   🔍 If buttons still not working, check browser console for errors")
    elif passed_checks >= 6:
        print("   ⚠️  Most functionality implemented, minor issues may exist")
        print("   🔧 Check browser console and network tab for specific errors")
    else:
        print("   ❌ Significant issues found with save button implementation")
        print("   🚨 Multiple fixes needed")
    
    print("\n💡 TROUBLESHOOTING STEPS:")
    print("   1. Open browser console (F12) and check for JavaScript errors")
    print("   2. Click Save Employee button and check console output")
    print("   3. Click Save as Draft button and check console output") 
    print("   4. Verify form validation is working correctly")
    print("   5. Check if toast notifications appear")
    
    return passed_checks >= 8

if __name__ == '__main__':
    test_employee_form_buttons()
