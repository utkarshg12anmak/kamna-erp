// EMPLOYEE FORM COMPREHENSIVE DIAGNOSTIC SCRIPT
// Copy and paste this entire script into the browser console on the employee form page

console.log('🔧 STARTING COMPREHENSIVE FORM DIAGNOSTIC...');

// Function to run all diagnostic checks
function runFormDiagnostic() {
    console.log('\n🔍 === ELEMENT EXISTENCE CHECKS ===');
    
    // Check for form elements
    const form = document.getElementById('employeeForm');
    const saveAsDraftBtn = document.getElementById('saveAsDraft');
    const submitBtn = document.querySelector('button[form="employeeForm"]');
    const allSubmitBtns = document.querySelectorAll('button[type="submit"]');
    
    console.log('Form element:', form ? '✅ FOUND' : '❌ NOT FOUND');
    console.log('Save as Draft button:', saveAsDraftBtn ? '✅ FOUND' : '❌ NOT FOUND');
    console.log('Submit button with form attr:', submitBtn ? '✅ FOUND' : '❌ NOT FOUND');
    console.log('All submit buttons count:', allSubmitBtns.length);
    
    // Check form structure
    if (form) {
        console.log('Form ID:', form.id);
        console.log('Form method:', form.method || 'GET (default)');
        console.log('Form action:', form.action);
        console.log('Form child elements:', form.children.length);
    }
    
    console.log('\n🔍 === FUNCTION AVAILABILITY CHECKS ===');
    console.log('saveEmployee function:', typeof window.saveEmployee);
    console.log('debugElementCheck function:', typeof window.debugElementCheck);
    console.log('logButtonClick function:', typeof window.logButtonClick);
    console.log('testSaveEmployee function:', typeof window.testSaveEmployee);
    
    console.log('\n🔍 === EVENT LISTENER CHECKS ===');
    
    // Test if event listeners are working
    if (form) {
        const listeners = getEventListeners ? getEventListeners(form) : 'getEventListeners not available';
        console.log('Form event listeners:', listeners);
    }
    
    if (saveAsDraftBtn) {
        const listeners = getEventListeners ? getEventListeners(saveAsDraftBtn) : 'getEventListeners not available';
        console.log('Save as Draft button listeners:', listeners);
    }
    
    console.log('\n🔍 === MANUAL TESTS ===');
    
    // Test element checks if available
    if (typeof window.debugElementCheck === 'function') {
        window.debugElementCheck('#employeeForm', 1);
        window.debugElementCheck('#saveAsDraft', 1);
        window.debugElementCheck('button[type="submit"]');
    } else {
        console.warn('debugElementCheck function not available');
    }
    
    console.log('\n🔍 === FORM SUBMISSION TEST ===');
    
    // Test form submission
    if (form) {
        console.log('Testing form submission...');
        const submitEvent = new Event('submit', { bubbles: true, cancelable: true });
        
        // Add temporary listener to see if events fire
        form.addEventListener('submit', function(e) {
            console.log('🎯 Form submit event captured in diagnostic!');
            e.preventDefault();
        }, { once: true });
        
        form.dispatchEvent(submitEvent);
    }
    
    console.log('\n🔍 === BUTTON CLICK TESTS ===');
    
    // Test button clicks
    if (saveAsDraftBtn) {
        console.log('Testing Save as Draft button click...');
        const clickEvent = new MouseEvent('click', { bubbles: true, cancelable: true });
        
        // Add temporary listener
        saveAsDraftBtn.addEventListener('click', function(e) {
            console.log('🎯 Save as Draft click captured in diagnostic!');
            e.preventDefault();
        }, { once: true });
        
        saveAsDraftBtn.dispatchEvent(clickEvent);
    }
    
    if (submitBtn) {
        console.log('Testing Submit button click...');
        const clickEvent = new MouseEvent('click', { bubbles: true, cancelable: true });
        
        submitBtn.addEventListener('click', function(e) {
            console.log('🎯 Submit button click captured in diagnostic!');
            e.preventDefault();
        }, { once: true });
        
        submitBtn.dispatchEvent(clickEvent);
    }
    
    console.log('\n🔍 === SAVE FUNCTION TEST ===');
    
    if (typeof window.saveEmployee === 'function') {
        console.log('Testing saveEmployee function...');
        try {
            // Test if function can be called without errors
            console.log('saveEmployee is callable, but not executing to avoid side effects');
            console.log('To test manually, run: window.testSaveEmployee()');
        } catch (error) {
            console.error('Error testing saveEmployee:', error);
        }
    } else {
        console.error('saveEmployee function not found!');
    }
    
    console.log('\n✅ DIAGNOSTIC COMPLETE');
    console.log('If any elements show ❌ NOT FOUND, that\'s the issue!');
    console.log('If functions show "undefined", the script didn\'t load properly');
    console.log('If events don\'t trigger, there\'s an event listener issue');
}

// Function to monitor button clicks in real-time
function startClickMonitor() {
    console.log('\n👀 STARTING REAL-TIME CLICK MONITOR...');
    console.log('Click any button on the page and see detailed logs');
    
    document.addEventListener('click', function(e) {
        if (e.target.tagName === 'BUTTON') {
            console.log('🖱️ BUTTON CLICKED:', {
                id: e.target.id || 'no-id',
                type: e.target.type || 'no-type',
                form: e.target.getAttribute('form') || 'no-form-attr',
                textContent: e.target.textContent.trim(),
                className: e.target.className,
                timestamp: new Date().toLocaleTimeString()
            });
        }
    }, true);
    
    console.log('✅ Click monitor active - try clicking buttons now!');
}

// Function to test manual save
function testManualSave() {
    console.log('\n🧪 TESTING MANUAL SAVE...');
    
    if (typeof window.testSaveEmployee === 'function') {
        try {
            window.testSaveEmployee();
        } catch (error) {
            console.error('Error in manual save test:', error);
        }
    } else if (typeof window.saveEmployee === 'function') {
        console.log('testSaveEmployee not available, trying saveEmployee directly...');
        try {
            window.saveEmployee(true); // Save as draft to be safe
        } catch (error) {
            console.error('Error in saveEmployee:', error);
        }
    } else {
        console.error('No save functions available!');
    }
}

// Run the diagnostic immediately
runFormDiagnostic();

// Make functions available globally for manual testing
window.runFormDiagnostic = runFormDiagnostic;
window.startClickMonitor = startClickMonitor;
window.testManualSave = testManualSave;

console.log('\n📋 AVAILABLE COMMANDS:');
console.log('runFormDiagnostic() - Run full diagnostic again');
console.log('startClickMonitor() - Monitor all button clicks');
console.log('testManualSave() - Test save functionality');

console.log('\n🎯 NEXT STEPS:');
console.log('1. Check the diagnostic results above');
console.log('2. Try clicking the actual Save buttons');
console.log('3. Run startClickMonitor() to see real-time click events');
console.log('4. If issues persist, share the console output');
