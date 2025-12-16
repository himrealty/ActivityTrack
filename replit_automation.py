import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

print('Starting Replit automation...')

# Setup Chrome
chrome_options = Options()
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--headless')
chrome_options.add_argument('--window-size=1920,1080')

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

try:
    # 1. Go to login page
    print('Step 1: Go to login page')
    driver.get('https://replit.com/login')
    time.sleep(5)
    driver.save_screenshot('1_page.png')
    
    # 2. Look for "Log in" link (it's on the signup page)
    print('Step 2: Find Log in link')
    
    # The page shows "Sign Up" but has "Log in" link somewhere
    # Try to find and click "Log in"
    login_found = False
    
    # Method 1: Look for "Log in" text
    elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Log in') or contains(text(), 'Sign in')]")
    for elem in elements:
        try:
            if elem.is_displayed():
                print(f'Found login text: {elem.text}')
                elem.click()
                login_found = True
                print('Clicked login link')
                time.sleep(3)
                break
        except:
            continue
    
    # Method 2: Look for links with login
    if not login_found:
        links = driver.find_elements(By.TAG_NAME, 'a')
        for link in links:
            try:
                href = link.get_attribute('href') or ''
                text = link.text or ''
                if ('login' in href.lower() or 'log in' in text.lower() or 'sign in' in text.lower()) and link.is_displayed():
                    link.click()
                    login_found = True
                    print('Clicked login link')
                    time.sleep(3)
                    break
            except:
                continue
    
    driver.save_screenshot('2_after_login_click.png')
    
    # 3. Fill email - use JavaScript to find and fill
    print('Step 3: Fill email')
    
    # Execute JavaScript to find and fill email field
    driver.execute_script("""
        // Find all input fields
        var inputs = document.getElementsByTagName('input');
        var emailInput = null;
        
        for (var i = 0; i < inputs.length; i++) {
            var inp = inputs[i];
            var type = inp.type || '';
            var name = inp.name || '';
            var placeholder = inp.placeholder || '';
            var id = inp.id || '';
            
            // Check if this is likely an email field
            if (type.toLowerCase() === 'email' || 
                name.toLowerCase().includes('email') || 
                name.toLowerCase().includes('username') ||
                placeholder.toLowerCase().includes('email') ||
                placeholder.toLowerCase().includes('username') ||
                id.toLowerCase().includes('email') ||
                id.toLowerCase().includes('username')) {
                
                if (inp.offsetParent !== null) { // Check if visible
                    emailInput = inp;
                    break;
                }
            }
        }
        
        // If no email field found, use first visible text input
        if (!emailInput) {
            for (var i = 0; i < inputs.length; i++) {
                var inp = inputs[i];
                if (inp.type === 'text' && inp.offsetParent !== null) {
                    emailInput = inp;
                    break;
                }
            }
        }
        
        // Fill email
        if (emailInput) {
            emailInput.value = arguments[0];
            emailInput.dispatchEvent(new Event('input', { bubbles: true }));
            emailInput.dispatchEvent(new Event('change', { bubbles: true }));
            return 'Email field found and filled';
        }
        
        return 'No email field found';
    """, os.environ['REPLIT_EMAIL'])
    
    time.sleep(2)
    driver.save_screenshot('3_email_filled.png')
    
    # 4. Fill password - use JavaScript
    print('Step 4: Fill password')
    
    driver.execute_script("""
        // Find password field
        var inputs = document.getElementsByTagName('input');
        var passwordInput = null;
        
        for (var i = 0; i < inputs.length; i++) {
            var inp = inputs[i];
            if (inp.type === 'password' && inp.offsetParent !== null) {
                passwordInput = inp;
                break;
            }
        }
        
        // Fill password
        if (passwordInput) {
            passwordInput.value = arguments[0];
            passwordInput.dispatchEvent(new Event('input', { bubbles: true }));
            passwordInput.dispatchEvent(new Event('change', { bubbles: true }));
            return 'Password field found and filled';
        }
        
        return 'No password field found';
    """, os.environ['REPLIT_PASSWORD'])
    
    time.sleep(2)
    driver.save_screenshot('4_password_filled.png')
    
    # 5. Submit form - use JavaScript
    print('Step 5: Submit form')
    
    driver.execute_script("""
        // Try to find and click submit button
        var buttons = document.getElementsByTagName('button');
        var submitted = false;
        
        for (var i = 0; i < buttons.length; i++) {
            var btn = buttons[i];
            var text = btn.textContent || btn.innerText || '';
            
            if ((text.toLowerCase().includes('sign in') || 
                 text.toLowerCase().includes('log in') || 
                 text.toLowerCase().includes('continue') ||
                 btn.type === 'submit') && 
                btn.offsetParent !== null) {
                
                btn.click();
                submitted = true;
                return 'Submit button clicked: ' + text;
            }
        }
        
        // If no button found, try to submit form
        var forms = document.getElementsByTagName('form');
        if (forms.length > 0 && !submitted) {
            forms[0].submit();
            return 'Form submitted';
        }
        
        return 'No submit method found';
    """)
    
    print('Form submitted')
    time.sleep(8)
    driver.save_screenshot('5_after_submit.png')
    
    # 6. Go to project
    print('Step 6: Go to project')
    driver.get(os.environ['REPLIT_PROJECT_URL'])
    time.sleep(8)
    driver.save_screenshot('6_project.png')
    
    # 7. Run command via JavaScript
    print('Step 7: Run command')
    command = os.environ['COMMAND_TO_RUN']
    print(f'Command: {command}')
    
    driver.execute_script(f"""
        // Try to find terminal/console
        var found = false;
        
        // Look for contenteditable divs (terminal)
        var editables = document.querySelectorAll('[contenteditable="true"]');
        for (var i = 0; i < editables.length; i++) {{
            try {{
                editables[i].textContent = '{command}';
                editables[i].dispatchEvent(new Event('input', {{ bubbles: true }}));
                
                // Send Enter key
                var enterEvent = new KeyboardEvent('keydown', {{
                    key: 'Enter',
                    code: 'Enter',
                    keyCode: 13,
                    bubbles: true
                }});
                editables[i].dispatchEvent(enterEvent);
                found = true;
                break;
            }} catch(e) {{}}
        }}
        
        // Look for textareas
        if (!found) {{
            var textareas = document.getElementsByTagName('textarea');
            for (var i = 0; i < textareas.length; i++) {{
                try {{
                    textareas[i].value = '{command}';
                    textareas[i].dispatchEvent(new Event('input', {{ bubbles: true }}));
                    
                    var enterEvent = new KeyboardEvent('keydown', {{
                        key: 'Enter',
                        code: 'Enter',
                        keyCode: 13,
                        bubbles: true
                    }});
                    textareas[i].dispatchEvent(enterEvent);
                    found = true;
                    break;
                }} catch(e) {{}}
            }}
        }}
        
        return found ? 'Command sent' : 'No terminal found';
    """)
    
    print('Command executed')
    time.sleep(5)
    driver.save_screenshot('7_after_command.png')
    
    # 8. Get output
    print('Step 8: Get output')
    output = driver.execute_script("return document.body.innerText || document.body.textContent;")
    
    if output:
        print('=' * 50)
        print('OUTPUT:')
        print('=' * 50)
        print(output[-3000:] if len(output) > 3000 else output)
        print('=' * 50)
        
        with open('output.txt', 'w', encoding='utf-8') as f:
            f.write(output)
    
    driver.save_screenshot('8_final.png')
    print('✅ Done')
    
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
    
    try:
        driver.save_screenshot('error.png')
    except:
        pass
    
    try:
        with open('source.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
    except:
        pass
    
    raise

finally:
    driver.quit()
