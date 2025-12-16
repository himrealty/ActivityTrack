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

print('=' * 80)
print('REPLIT AUTOMATION - DEBUG MODE')
print('=' * 80)

# Setup Chrome
chrome_options = Options()
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--headless')  # REQUIRED for GitHub Actions
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--window-size=1920,1080')
chrome_options.add_argument('--disable-blink-features=AutomationControlled')
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)
chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)
wait = WebDriverWait(driver, 20)

# Remove webdriver property
driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

def log_step(step_num, description):
    """Print formatted step header"""
    print('\n' + '=' * 80)
    print(f'STEP {step_num}: {description}')
    print('=' * 80)

def safe_screenshot(name):
    """Take screenshot with error handling"""
    try:
        filename = f'{name}.png'
        driver.save_screenshot(filename)
        print(f'✓ Screenshot saved: {filename}')
        return True
    except Exception as e:
        print(f'✗ Failed to save screenshot {name}: {e}')
        return False

def save_page_source(name):
    """Save page source HTML"""
    try:
        filename = f'{name}.html'
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print(f'✓ Page source saved: {filename}')
        return True
    except Exception as e:
        print(f'✗ Failed to save page source: {e}')
        return False

def check_for_errors():
    """Check page for error messages"""
    error_selectors = ['.error', '[role="alert"]', '.alert', '.message', '.error-message']
    for selector in error_selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for elem in elements:
                if elem.is_displayed() and elem.text.strip():
                    print(f'⚠ Error message found ({selector}): {elem.text}')
        except:
            pass

def print_all_inputs():
    """Print all input fields for debugging"""
    try:
        inputs = driver.find_elements(By.TAG_NAME, 'input')
        print(f'\nFound {len(inputs)} input elements:')
        for i, inp in enumerate(inputs):
            try:
                print(f'  [{i}] type={inp.get_attribute("type")}, '
                      f'name={inp.get_attribute("name")}, '
                      f'id={inp.get_attribute("id")}, '
                      f'placeholder={inp.get_attribute("placeholder")}, '
                      f'visible={inp.is_displayed()}')
            except:
                pass
    except Exception as e:
        print(f'Could not list inputs: {e}')

try:
    # ========================================================================
    # STEP 1: Navigate to Login Page
    # ========================================================================
    log_step(1, 'Navigate to Login Page')
    
    driver.get('https://replit.com/login')
    time.sleep(5)
    
    current_url = driver.current_url
    print(f'Current URL: {current_url}')
    print(f'Page Title: {driver.title}')
    
    safe_screenshot('01_initial_page')
    save_page_source('01_initial_page')
    
    # ========================================================================
    # STEP 2: Find and Fill Email/Username
    # ========================================================================
    log_step(2, 'Find and Fill Email/Username')
    
    print_all_inputs()
    
    # Try multiple selectors
    email_selectors = [
        "input[type='email']",
        "input[name*='email' i]",
        "input[name*='username' i]",
        "input[placeholder*='email' i]",
        "input[placeholder*='username' i]",
        "input[id*='email' i]",
        "input[id*='username' i]",
        "input[autocomplete='email']",
        "input[autocomplete='username']",
    ]
    
    email_input = None
    selector_used = None
    
    for selector in email_selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for elem in elements:
                if elem.is_displayed():
                    email_input = elem
                    selector_used = selector
                    print(f'✓ Found email field using: {selector}')
                    break
            if email_input:
                break
        except Exception as e:
            continue
    
    if not email_input:
        print('✗ Email field not found with CSS selectors, trying JavaScript...')
        email_input = driver.execute_script("""
            const inputs = Array.from(document.querySelectorAll('input'));
            return inputs.find(input => {
                const style = window.getComputedStyle(input);
                const isVisible = style.display !== 'none' && 
                                style.visibility !== 'hidden' && 
                                input.offsetParent !== null;
                if (!isVisible) return false;
                
                const type = (input.type || '').toLowerCase();
                const name = (input.name || '').toLowerCase();
                const placeholder = (input.placeholder || '').toLowerCase();
                
                return type === 'email' || type === 'text' ||
                       name.includes('email') || name.includes('username') ||
                       placeholder.includes('email') || placeholder.includes('username');
            }) || null;
        """)
        
        if email_input:
            print('✓ Found email field using JavaScript')
    
    if not email_input:
        print('✗✗✗ FAILED: Could not find email input field')
        safe_screenshot('02_email_field_not_found')
        check_for_errors()
        raise Exception('Email field not found')
    
    # Fill email
    email = os.environ.get('REPLIT_EMAIL', '')
    if not email:
        raise Exception('REPLIT_EMAIL environment variable not set')
    
    print(f'Filling email: {email[:3]}***{email[-3:] if len(email) > 6 else ""}')
    
    email_input.clear()
    email_input.send_keys(email)
    time.sleep(1)
    
    filled_value = email_input.get_attribute('value')
    print(f'Email field value: {filled_value[:3]}***{filled_value[-3:] if len(filled_value) > 6 else ""}')
    
    if filled_value != email:
        print('⚠ WARNING: Email value mismatch!')
    
    safe_screenshot('02_email_filled')
    
    # ========================================================================
    # STEP 3: Find and Fill Password
    # ========================================================================
    log_step(3, 'Find and Fill Password')
    
    password_input = None
    try:
        password_input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password']"))
        )
        print('✓ Found password field')
    except:
        print('✗ Password field not found with wait, trying JavaScript...')
        password_input = driver.execute_script("""
            const inputs = Array.from(document.querySelectorAll('input[type="password"]'));
            return inputs.find(input => {
                const style = window.getComputedStyle(input);
                return style.display !== 'none' && 
                       style.visibility !== 'hidden' && 
                       input.offsetParent !== null;
            }) || null;
        """)
    
    if not password_input:
        print('✗✗✗ FAILED: Could not find password field')
        safe_screenshot('03_password_field_not_found')
        check_for_errors()
        raise Exception('Password field not found')
    
    password = os.environ.get('REPLIT_PASSWORD', '')
    if not password:
        raise Exception('REPLIT_PASSWORD environment variable not set')
    
    print(f'Filling password: {"*" * len(password)}')
    password_input.clear()
    password_input.send_keys(password)
    time.sleep(1)
    
    safe_screenshot('03_password_filled')
    
    # ========================================================================
    # STEP 4: Submit Login Form
    # ========================================================================
    log_step(4, 'Submit Login Form')
    
    # Find submit button
    submit_button = None
    buttons = driver.find_elements(By.TAG_NAME, 'button')
    
    print(f'Found {len(buttons)} buttons on page:')
    for i, btn in enumerate(buttons):
        try:
            if btn.is_displayed():
                text = btn.text.strip()
                btn_type = btn.get_attribute('type')
                print(f'  [{i}] Text: "{text}", Type: {btn_type}, Visible: True')
                
                if any(word in text.lower() for word in ['log in', 'sign in', 'continue', 'submit']) or btn_type == 'submit':
                    if not submit_button:
                        submit_button = btn
                        print(f'  --> Selected this button')
        except:
            pass
    
    if not submit_button:
        print('✗ Submit button not found, trying Enter key instead')
        password_input.send_keys(Keys.RETURN)
        print('✓ Pressed Enter key')
    else:
        print(f'✓ Clicking submit button: "{submit_button.text}"')
        submit_button.click()
    
    safe_screenshot('04_form_submitted')
    
    # Wait for navigation
    print('Waiting for login to complete...')
    time.sleep(10)
    
    # ========================================================================
    # STEP 5: Verify Login Success
    # ========================================================================
    log_step(5, 'Verify Login Success')
    
    current_url = driver.current_url
    print(f'Current URL: {current_url}')
    print(f'Page Title: {driver.title}')
    
    safe_screenshot('05_after_login')
    save_page_source('05_after_login')
    check_for_errors()
    
    if '/login' in current_url:
        print('✗✗✗ FAILED: Still on login page after submission')
        print('\nPossible reasons:')
        print('  1. Incorrect username/password')
        print('  2. 2FA/MFA is enabled')
        print('  3. CAPTCHA required')
        print('  4. Account locked or requires verification')
        print('  5. Replit detected automation')
        
        # Check for specific error indicators
        page_text = driver.find_element(By.TAG_NAME, 'body').text.lower()
        if 'captcha' in page_text:
            print('\n⚠ CAPTCHA detected on page')
        if 'verify' in page_text or 'verification' in page_text:
            print('\n⚠ Verification required')
        if '2fa' in page_text or 'two-factor' in page_text or 'authenticator' in page_text:
            print('\n⚠ 2FA/MFA detected')
        
        print('\n⚠ Waiting additional 10 seconds...')
        time.sleep(10)
        current_url = driver.current_url
        print(f'URL after additional wait: {current_url}')
        
        if '/login' in current_url:
            raise Exception('Login failed - still on login page')
    else:
        print('✓✓✓ LOGIN SUCCESSFUL - Redirected from login page')
    
    # ========================================================================
    # STEP 6: Navigate to Project
    # ========================================================================
    log_step(6, 'Navigate to Project')
    
    project_url = os.environ.get('REPLIT_PROJECT_URL', '')
    if not project_url:
        raise Exception('REPLIT_PROJECT_URL environment variable not set')
    
    print(f'Project URL: {project_url}')
    driver.get(project_url)
    time.sleep(10)
    
    current_url = driver.current_url
    print(f'Current URL: {current_url}')
    print(f'Page Title: {driver.title}')
    
    safe_screenshot('06_project_page')
    save_page_source('06_project_page')
    
    if 'replit.com/@' not in current_url and 'replit.com/~/' not in current_url:
        print('⚠ WARNING: May not be on project page')
    else:
        print('✓ Project page loaded successfully')
    
    # ========================================================================
    # STEP 7: Find and Click Run Button or Execute Command
    # ========================================================================
    log_step(7, 'Execute Command or Click Run Button')
    
    command = os.environ.get('COMMAND_TO_RUN', 'run').strip()
    print(f'Command to run: {command}')
    
    time.sleep(5)
    
    # Check if we should click Run button
    should_click_run = command.lower() in ['run', 'click run', 'start', '']
    
    if should_click_run:
        print('Attempting to find and click Run button...')
        
        # List all buttons
        buttons = driver.find_elements(By.TAG_NAME, 'button')
        print(f'\nFound {len(buttons)} buttons:')
        for i, btn in enumerate(buttons[:20]):  # Show first 20
            try:
                if btn.is_displayed():
                    text = btn.text.strip()
                    aria = btn.get_attribute('aria-label') or ''
                    title = btn.get_attribute('title') or ''
                    print(f'  [{i}] Text: "{text}", Aria: "{aria}", Title: "{title}"')
            except:
                pass
        
        run_button = driver.execute_script("""
            const buttons = Array.from(document.querySelectorAll('button, [role="button"]'));
            
            for (const btn of buttons) {
                const text = (btn.textContent || '').trim().toLowerCase();
                const ariaLabel = (btn.getAttribute('aria-label') || '').toLowerCase();
                const title = (btn.getAttribute('title') || '').toLowerCase();
                
                if (text === 'run' || text.includes('▶') || 
                    ariaLabel.includes('run') || title.includes('run')) {
                    
                    const style = window.getComputedStyle(btn);
                    if (style.display !== 'none' && 
                        style.visibility !== 'hidden' && 
                        btn.offsetParent !== null) {
                        return btn;
                    }
                }
            }
            return null;
        """)
        
        if run_button:
            print('✓ Found Run button, clicking...')
            run_button.click()
            time.sleep(3)
            safe_screenshot('07_run_clicked')
        else:
            print('✗ Run button not found')
            safe_screenshot('07_run_not_found')
    
    else:
        print(f'Attempting to execute command in shell: {command}')
        
        # Try to open Shell tab
        shell_opened = driver.execute_script("""
            const tabs = Array.from(document.querySelectorAll('[role="tab"], button, .tab'));
            for (const tab of tabs) {
                const text = (tab.textContent || '').trim().toLowerCase();
                if (text === 'shell' || text === 'console') {
                    tab.click();
                    return true;
                }
            }
            return false;
        """)
        
        if shell_opened:
            print('✓ Shell tab opened')
            time.sleep(2)
        
        # Execute command
        escaped_command = command.replace("'", "\\'")
        result = driver.execute_script(f"""
            const command = '{escaped_command}';
            let executed = false;
            
            // Try xterm textarea
            const xtermElements = document.querySelectorAll('.xterm-helper-textarea, textarea');
            for (const elem of xtermElements) {{
                try {{
                    elem.focus();
                    elem.value = command;
                    elem.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    
                    const enterEvent = new KeyboardEvent('keydown', {{
                        key: 'Enter',
                        code: 'Enter',
                        keyCode: 13,
                        which: 13,
                        bubbles: true
                    }});
                    elem.dispatchEvent(enterEvent);
                    executed = true;
                    break;
                }} catch(e) {{}}
            }}
            
            return executed ? 'Command sent' : 'No terminal found';
        """)
        
        print(f'Shell interaction result: {result}')
        safe_screenshot('07_command_sent')
    
    # ========================================================================
    # STEP 8: Wait and Capture Output
    # ========================================================================
    log_step(8, 'Wait and Capture Output')
    
    wait_time = int(os.environ.get('WAIT_TIME', '15'))
    print(f'Waiting {wait_time} seconds for execution...')
    
    for i in range(0, wait_time, 5):
        time.sleep(5)
        safe_screenshot(f'08_progress_{i+5}s')
        print(f'  ... {i+5}s elapsed')
    
    # Capture output
    page_text = driver.execute_script("return document.body.innerText || '';")
    
    console_output = driver.execute_script("""
        const selectors = ['.console', '.terminal', '.output', '[class*="console"]', '[class*="terminal"]'];
        let output = '';
        for (const sel of selectors) {
            const elems = document.querySelectorAll(sel);
            for (const elem of elems) {
                const text = elem.innerText || '';
                if (text.length > output.length) output = text;
            }
        }
        return output || 'No console output found';
    """)
    
    print('\n' + '=' * 80)
    print('PAGE TEXT OUTPUT:')
    print('=' * 80)
    print(page_text[-2000:] if len(page_text) > 2000 else page_text)
    
    with open('page_output.txt', 'w', encoding='utf-8') as f:
        f.write(page_text)
    print('\n✓ Full output saved to page_output.txt')
    
    print('\n' + '=' * 80)
    print('CONSOLE OUTPUT:')
    print('=' * 80)
    print(console_output[-1000:] if len(console_output) > 1000 else console_output)
    
    with open('console_output.txt', 'w', encoding='utf-8') as f:
        f.write(console_output)
    print('\n✓ Console output saved to console_output.txt')
    
    safe_screenshot('08_final')
    
    print('\n' + '=' * 80)
    print('✓✓✓ AUTOMATION COMPLETED SUCCESSFULLY')
    print('=' * 80)
    
except Exception as e:
    print('\n' + '=' * 80)
    print('✗✗✗ ERROR OCCURRED')
    print('=' * 80)
    print(f'Error: {e}')
    
    import traceback
    print('\nFull traceback:')
    traceback.print_exc()
    
    safe_screenshot('error')
    save_page_source('error_page')
    
    print('\n' + '=' * 80)
    print('DEBUG FILES SAVED:')
    print('  - error.png')
    print('  - error_page.html')
    print('  - Check all numbered screenshots for the failure point')
    print('=' * 80)
    
    raise

finally:
    print('\nClosing browser...')
    try:
        driver.quit()
    except:
        pass
    print('Done!')
