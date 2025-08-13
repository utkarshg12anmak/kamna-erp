// Employee Form Save Button Diagnostic Script
// Copy and paste this into the browser console on the employee form page

console.log('🔧 Employee Form Save Button Diagnostic');
console.log('=========================================');

// Test 1: Check if elements exist
const form = document.getElementById('employeeForm');
const saveButton = document.querySelector('button[form="employeeForm"]');
const draftButton = document.getElementById('saveAsDraft');

console.log('✅ Element Detection:');
console.log('  Form element:', form ? '✅ FOUND' : '❌ NOT FOUND');
console.log('  Save Employee button:', saveButton ? '✅ FOUND' : '❌ NOT FOUND');
console.log('  Save as Draft button:', draftButton ? '✅ FOUND' : '❌ NOT FOUND');

// Test 2: Check function availability
console.log('\n✅ Function Availability:');
console.log('  saveEmployee function:', typeof saveEmployee === 'function' ? '✅ AVAILABLE' : '❌ NOT AVAILABLE');
console.log('  validateForm function:', typeof validateForm === 'function' ? '✅ AVAILABLE' : '❌ NOT AVAILABLE');

// Test 3: Check event listeners
console.log('\n✅ Event Listener Status:');
if (saveButton) {
    console.log('  Save button onclick:', saveButton.onclick ? '✅ HAS ONCLICK' : '❌ NO ONCLICK');
    console.log('  Save button events:', getEventListeners ? getEventListeners(saveButton) : 'Cannot check (use Chrome)');
}

if (draftButton) {
    console.log('  Draft button onclick:', draftButton.onclick ? '✅ HAS ONCLICK' : '❌ NO ONCLICK');
    console.log('  Draft button events:', getEventListeners ? getEventListeners(draftButton) : 'Cannot check (use Chrome)');
}

// Test 4: Manual click test
console.log('\n🧪 Manual Click Tests:');
if (saveButton) {
    console.log('Testing Save Employee button click...');
    try {
        saveButton.click();
        console.log('✅ Save Employee button clicked successfully');
    } catch (error) {
        console.log('❌ Save Employee button click failed:', error.message);
    }
}

if (draftButton) {
    console.log('Testing Save as Draft button click...');
    try {
        draftButton.click();
        console.log('✅ Save as Draft button clicked successfully');
    } catch (error) {
        console.log('❌ Save as Draft button click failed:', error.message);
    }
}

// Test 5: Direct function call
console.log('\n🔧 Direct Function Call Test:');
if (typeof saveEmployee === 'function') {
    console.log('Testing direct saveEmployee(false) call...');
    try {
        saveEmployee(false);
        console.log('✅ Direct function call successful');
    } catch (error) {
        console.log('❌ Direct function call failed:', error.message);
    }
} else {
    console.log('❌ saveEmployee function not available for direct call');
}

// Test 6: CSS and visibility checks
console.log('\n👁️ Visibility and CSS Checks:');
if (saveButton) {
    const styles = window.getComputedStyle(saveButton);
    console.log('  Save button display:', styles.display);
    console.log('  Save button visibility:', styles.visibility);
    console.log('  Save button pointer-events:', styles.pointerEvents);
    console.log('  Save button z-index:', styles.zIndex);
}

// Test 7: Form state
console.log('\n📋 Form State:');
if (form) {
    console.log('  Form method:', form.method || 'GET');
    console.log('  Form action:', form.action || 'current page');
    console.log('  Form elements count:', form.elements.length);
    console.log('  Form validity:', form.checkValidity ? form.checkValidity() : 'Cannot check');
}

console.log('\n🎯 Summary:');
console.log('Copy this entire console output and share it for diagnosis.');
console.log('========================================');
