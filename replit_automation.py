import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

print('Starting Replit automation...')

# Setup Chrome options
chrome_options = Options()
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--window-size=1920,1080')
chrome_options.add_argument('--disable-blink-features=AutomationControlled')
chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
chrome_options.add_experimental_option('useAutomationExtension', False)

# Use webdriver-manager
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)
wait = WebDriverWait(driver, 20)

driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

def save_screenshot(name):
    driver.save_screenshot(name)
    print(f'Screenshot saved: {name}')

def find_element_by_xpath_with_text(text):
    """Find element containing text (case insensitive)"""
    try:
        return driver.find_element(By.XPATH, f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text.lower()}')]")
    except:
        return None

try:
    # 1. Navigate to Replit login
    print('Step 1: Navigating to Replit login...')
    driver.get('https://replit.com/login')
    time.sleep(8)
    save_screenshot('1_login_page.png')
    
    # 2. Get page source for debugging
    page_source = driver.page_source
    print(f'Page title: {driver.title}')
    print(f'Page contains "Log in": {"Log in" in page_source}')
    print(f'Page contains "Sign in": {"Sign in" in page_source}')
    print(f'Page contains "email": {"email" in page_source.lower()}')
    print(f'Page contains "password": {"password" in page_source.lower()}')
    
    # 3. Switch to login form (the page has both signup and login)
    print('Step 2: Switching to login form...')
    
    # Method 1: Look for "Log in" text and click it
    login_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Log in') or contains(text(), 'Sign in')]")
    for elem in login_elements:
        try:
            if elem.is_displayed() and elem.tag_name in ['button', 'a', 'div', 'span']:
                elem.click()
                print('Clicked login element')
                time.sleep(3)
                break
        except:
            continue
    
    # 4. Try to find email field with multiple strategies
    print('Step 3: Finding email field...')
    time.sleep(3)
    save_screenshot('2_before_login.png')
    
    # Strategy A: Look for all input fields and identify email
    all_inputs = driver.find_elements(By.TAG_NAME, 'input')
    print(f'Found {len(all_inputs)} input fields')
    
    email_field = None
    password_field = None
    
    for inp in all_inputs:
        if inp.is_displayed():
            inp_type = inp.get_attribute('type') or ''
            inp_name = inp.get_attribute('name') or ''
            inp_placeholder = inp.get_attribute('placeholder') or ''
            inp_id = inp.get_attribute('id') or ''
            
            print(f'Input: type={inp_type}, name={inp_name}, placeholder={inp_placeholder}, id={inp_id}')
            
            if 'email' in inp_type.lower() or 'email' in inp_name.lower() or 'email' in inp_placeholder.lower() or 'username' in inp_name.lower():
                email_field = inp
                print('Identified as email field')
            elif 'password' in inp_type.lower() or 'password' in inp_name.lower() or 'password' in inp_placeholder.lower():
                password_field = inp
                print('Identified as password field')
    
    # Strategy B: If not found, try common selectors
    if not email_field:
        selectors = [
            'input[type="email"]',
            'input[name="email"]',
            'input[name="username"]',
            'input[autocomplete="email"]',
            'input[autocomplete="username"]',
            'input[placeholder*="email" i]',
            'input[placeholder*="username" i]',
            'input[data-cy*="email"]',
            'input[data-cy*="username"]'
        ]
        
        for selector in selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elements:
                    if elem.is_displayed():
                        email_field = elem
                        print(f'Found email field with selector: {selector}')
                        break
                if email_field:
                    break
            except:
                continue
    
    # Strategy C: First visible text input
    if not email_field and all_inputs:
        for inp in all_inputs:
            if inp.is_displayed() and inp.is_enabled() and inp.get_attribute('type') in ['text', 'email', '']:
                email_field = inp
                print('Using first visible text input as email field')
                break
    
    if email_field:
        email_field.click()
        time.sleep(1)
        email_field.clear()
        email_field.send_keys(os.environ['REPLIT_EMAIL'])
        print('Email entered')
        time.sleep(2)
        save_screenshot('3_email_entered.png')
    else:
        print('ERROR: Email field not found after all strategies')
        # Save all inputs info
        with open('inputs_debug.txt', 'w') as f:
            for i, inp in enumerate(all_inputs):
                f.write(f'Input {i}: type={inp.get_attribute("type")}, name={inp.get_attribute("name")}, placeholder={inp.get_attribute("placeholder")}, id={inp.get_attribute("id")}, displayed={inp.is_displayed()}\n')
        raise Exception('Email field not found')
    
    # 5. Find password field
    print('Step 4: Finding password field...')
    
    if not password_field:
        password_selectors = [
            'input[type="password"]',
            'input[name="password"]',
            'input[autocomplete="current-password"]',
            'input[placeholder*="password" i]'
        ]
        
        for selector in password_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elements:
                    if elem.is_displayed():
                        password_field = elem
                        print(f'Found password field with selector: {selector}')
                        break
                if password_field:
                    break
            except:
                continue
    
    if password_field:
        password_field.click()
        time.sleep(1)
        password_field.clear()
        password_field.send_keys(os.environ['REPLIT_PASSWORD'])
        print('Password entered')
        time.sleep(2)
        save_screenshot('4_password_entered.png')
    else:
        print('ERROR: Password field not found')
        raise Exception('Password field not found')
    
    # 6. Submit form
    print('Step 5: Submitting form...')
    
    # Try to find submit button
    submit_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Sign in') or contains(text(), 'Log in') or contains(text(), 'Continue') or @type='submit']")
    
    submitted = False
    for btn in submit_buttons:
        try:
            if btn.is_displayed():
                btn.click()
                print('Clicked submit button')
                submitted = True
                break
        except:
            continue
    
    if not submitted:
        # Try Enter key
        password_field.send_keys(Keys.RETURN)
        print('Submitted with Enter key')
    
    # 7. Wait for login
    print('Step 6: Waiting for login...')
    time.sleep(10)
    save_screenshot('5_after_login.png')
    
    # Check URL
    print(f'Current URL after login: {driver.current_url}')
    
    # 8. Navigate to project
    print('Step 7: Navigating to project...')
    driver.get(os.environ['REPLIT_PROJECT_URL'])
    time.sleep(10)
    save_screenshot('6_project_page.png')
    
    # 9. Run command
    print('Step 8: Running command...')
    command = os.environ['COMMAND_TO_RUN']
    print(f'Command: {command}')
    
    # Try to send command via JavaScript (simpler approach)
    driver.execute_script(f"""
        // Try to find and focus terminal
        var terminals = document.querySelectorAll('div[contenteditable="true"], textarea, input[type="text"]');
        for (var i = 0; i < terminals.length; i++) {{
            try {{
                terminals[i].focus();
                terminals[i].value = '{command}';
                terminals[i].dispatchEvent(new Event('input', {{ bubbles: true }}));
                
                // Simulate Enter key
                var enterEvent = new KeyboardEvent('keydown', {{
                    key: 'Enter',
                    code: 'Enter',
                    keyCode: 13,
                    which: 13,
                    bubbles: true
                }});
                terminals[i].dispatchEvent(enterEvent);
                
                console.log('Command sent via JavaScript');
                break;
            }} catch(e) {{
                console.log('Error with terminal ' + i + ': ' + e);
            }}
        }}
    """)
    
    print('Command executed via JavaScript')
    time.sleep(5)
    save_screenshot('7_after_command.png')
    
    # 10. Get output
    print('Step 9: Getting output...')
    output = driver.execute_script("return document.body.innerText;")
    
    if output:
        print('=' * 60)
        print('OUTPUT:')
        print('=' * 60)
        print(output[-5000:] if len(output) > 5000 else output)
        print('=' * 60)
        
        with open('output.txt', 'w', encoding='utf-8') as f:
            f.write(output)
        print('Output saved to output.txt')
    
    save_screenshot('8_final.png')
    print('✅ Automation completed successfully!')
    
except Exception as e:
    print(f'❌ ERROR: {str(e)}')
    import traceback
    traceback.print_exc()
    
    try:
        save_screenshot('error_final.png')
    except:
        pass
    
    try:
        with open('page_source.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print('Page source saved')
    except:
        pass
    
    raise

finally:
    driver.quit()
    print('Browser closed.')
