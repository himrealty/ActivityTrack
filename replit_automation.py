import os
import time
import base64
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

print('Starting Replit automation...')

# Setup Chrome options for GitHub Actions
chrome_options = Options()
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--headless=new')  # New headless mode
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--window-size=1920,1080')
chrome_options.add_argument('--disable-blink-features=AutomationControlled')
chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
chrome_options.add_experimental_option('useAutomationExtension', False)

# Use webdriver-manager to handle ChromeDriver
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)
wait = WebDriverWait(driver, 20)

driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

def save_screenshot(name):
    """Save screenshot with timestamp"""
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{name}"
    driver.save_screenshot(filename)
    print(f'Screenshot saved: {filename}')
    return filename

def find_and_click(selectors, description):
    """Find and click element from list of selectors"""
    for selector in selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for elem in elements:
                if elem.is_displayed() and elem.is_enabled():
                    elem.click()
                    print(f'Clicked: {description} using selector: {selector}')
                    return True
        except:
            continue
    return False

def find_and_send_keys(selectors, text, description):
    """Find element and send keys"""
    for selector in selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for elem in elements:
                if elem.is_displayed() and elem.is_enabled():
                    elem.click()
                    time.sleep(0.5)
                    elem.clear()
                    elem.send_keys(text)
                    print(f'Entered {description} using selector: {selector}')
                    return elem
        except:
            continue
    return None

try:
    # 1. Navigate to Replit login page
    print('Step 1: Navigating to Replit login...')
    driver.get('https://replit.com/login')
    time.sleep(8)  # Give more time for page to load
    
    # Save initial screenshot
    save_screenshot('initial_page.png')
    
    # Get page title and URL for debugging
    print(f'Page title: {driver.title}')
    print(f'Current URL: {driver.current_url}')
    
    # 2. Check if we're already logged in or redirected
    if 'dashboard' in driver.current_url or '@' in driver.current_url:
        print('Already logged in or on dashboard')
    else:
        print('Step 2: Attempting login...')
        
        # Strategy 1: Look for common login patterns
        # Try multiple login approaches
        
        # Approach A: Direct email/password form
        email_selectors = [
            'input[autocomplete="email"]',
            'input[autocomplete="username"]',
            'input[type="email"]',
            'input[name="email"]',
            'input[name="username"]',
            'input[placeholder*="email" i]',
            'input[placeholder*="username" i]',
            'input[placeholder*="user" i]',
            'input#email',
            'input#username',
            'input[data-cy="login-email"]',
            'input[data-testid="login-email"]',
            'input.login-input',
            'input.form-input',
            'input[type="text"]:not([type="search"]):not([aria-label*="search"])'
        ]
        
        email_field = find_and_send_keys(email_selectors, os.environ['REPLIT_EMAIL'], 'email')
        
        if email_field:
            # Look for continue/next button after email
            continue_selectors = [
                'button[type="submit"]',
                'button:contains("Continue")',
                'button:contains("Next")',
                'button[data-cy*="continue"]',
                'button[data-cy*="next"]',
                'button[aria-label*="Continue" i]',
                'button[aria-label*="Next" i]'
            ]
            
            find_and_click(continue_selectors, 'continue button')
            time.sleep(3)
            save_screenshot('after_email.png')
            
            # Now look for password
            password_selectors = [
                'input[type="password"]',
                'input[autocomplete="current-password"]',
                'input[name="password"]',
                'input#password',
                'input[placeholder*="password" i]',
                'input[data-cy="login-password"]',
                'input[data-testid="login-password"]'
            ]
            
            password_field = find_and_send_keys(password_selectors, os.environ['REPLIT_PASSWORD'], 'password')
            
            if password_field:
                # Submit login
                submit_selectors = [
                    'button[type="submit"]',
                    'button:contains("Sign in")',
                    'button:contains("Log in")',
                    'button[data-cy*="login"]',
                    'button[data-cy*="submit"]',
                    'button[aria-label*="Sign in" i]'
                ]
                
                find_and_click(submit_selectors, 'sign in button')
            else:
                # Maybe it's OAuth or single sign-on
                print('Password field not found, might be OAuth flow')
                email_field.send_keys(Keys.RETURN)
        else:
            # Approach B: Maybe it's a different login flow
            print('Trying alternative login approach...')
            
            # Look for "Continue with Google" or other OAuth buttons
            oauth_selectors = [
                'button:contains("Google")',
                'button:contains("GitHub")',
                'button:contains("Gitlab")',
                'button[data-cy*="google"]',
                'button[data-cy*="github"]',
                'div[data-cy*="google"]',
                'div[data-cy*="github"]'
            ]
            
            for selector in oauth_selectors:
                try:
                    buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                    for btn in buttons:
                        if btn.is_displayed():
                            print(f'Found OAuth button: {selector}')
                            # For now, we can't handle OAuth in automation
                            # Save screenshot and exit
                            save_screenshot('oauth_detected.png')
                            raise Exception('OAuth login detected. Manual login required.')
                except:
                    continue
            
            # Approach C: Try to find any form and submit with credentials
            print('Trying form detection...')
            all_forms = driver.find_elements(By.TAG_NAME, 'form')
            if all_forms:
                print(f'Found {len(all_forms)} form(s) on page')
                for i, form in enumerate(all_forms):
                    try:
                        # Get all inputs in form
                        inputs = form.find_elements(By.TAG_NAME, 'input')
                        print(f'Form {i} has {len(inputs)} input(s)')
                        
                        # Try to fill email/password if we find matching inputs
                        email_input = None
                        password_input = None
                        
                        for inp in inputs:
                            inp_type = inp.get_attribute('type') or ''
                            inp_name = inp.get_attribute('name') or ''
                            inp_id = inp.get_attribute('id') or ''
                            
                            if 'email' in inp_type or 'email' in inp_name or 'email' in inp_id or 'username' in inp_name:
                                email_input = inp
                            elif 'password' in inp_type or 'password' in inp_name or 'password' in inp_id:
                                password_input = inp
                        
                        if email_input and password_input:
                            email_input.click()
                            email_input.send_keys(os.environ['REPLIT_EMAIL'])
                            time.sleep(1)
                            password_input.click()
                            password_input.send_keys(os.environ['REPLIT_PASSWORD'])
                            time.sleep(1)
                            
                            # Try to submit
                            form.submit()
                            print('Form submitted with credentials')
                            break
                            
                    except Exception as e:
                        print(f'Error with form {i}: {e}')
                        continue
    
    # 3. Wait for login and check
    print('Step 3: Waiting for login completion...')
    time.sleep(10)
    save_screenshot('after_login_attempt.png')
    
    # Check if login was successful
    if 'login' not in driver.current_url and 'signin' not in driver.current_url:
        print('Login appears successful')
    else:
        print('Still on login page, login may have failed')
        # Try one more time with direct credentials in URL (not recommended for production)
        print('Trying direct project access...')
    
    # 4. Navigate to specific project
    print('Step 4: Navigating to project...')
    project_url = os.environ['REPLIT_PROJECT_URL']
    driver.get(project_url)
    time.sleep(10)
    save_screenshot('project_page.png')
    
    print(f'Project page title: {driver.title}')
    print(f'Project page URL: {driver.current_url}')
    
    # 5. Try to find and click Run button
    print('Step 5: Looking for Run button...')
    
    run_button_selectors = [
        'button:contains("Run")',
        'button[data-cy="run-button"]',
        'button[aria-label*="Run" i]',
        'div[data-cy="run-button"]',
        'button.run-button',
        'button[title*="Run" i]',
        'button:contains("▶")',  # Play symbol
        'button:contains("▷")'   # Another play symbol
    ]
    
    run_clicked = find_and_click(run_button_selectors, 'Run button')
    
    if run_clicked:
        print('Run button clicked')
        time.sleep(8)
        save_screenshot('after_run.png')
    else:
        print('Run button not found or already running')
    
    # 6. Execute command in terminal
    print('Step 6: Executing command...')
    command_to_run = os.environ['COMMAND_TO_RUN']
    print(f'Command: {command_to_run}')
    
    # Try to find terminal/console area
    terminal_selectors = [
        'div[contenteditable="true"]',
        '.xterm-helper-textarea',
        'textarea',
        'input[type="text"]',
        'div[class*="terminal"]',
        'div[class*="console"]',
        'div[class*="xterm"]',
        'pre[class*="xterm"]',
        '[data-cy*="terminal"]',
        '[data-testid*="terminal"]'
    ]
    
    terminal_found = False
    for selector in terminal_selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for elem in elements:
                if elem.is_displayed() and elem.is_enabled():
                    print(f'Found terminal element: {selector}')
                    
                    # Try to focus and send command
                    try:
                        elem.click()
                        time.sleep(1)
                        
                        # Different methods to send text
                        try:
                            elem.clear()
                        except:
                            pass
                        
                        elem.send_keys(command_to_run)
                        time.sleep(1)
                        elem.send_keys(Keys.RETURN)
                        terminal_found = True
                        print('Command sent to terminal')
                        break
                    except Exception as e:
                        print(f'Error sending to terminal: {e}')
                        continue
            if terminal_found:
                break
        except:
            continue
    
    if not terminal_found:
        print('Could not find terminal input')
        # Try JavaScript injection as last resort
        try:
            driver.execute_script(f"""
                var event = new KeyboardEvent('keydown', {{key: '{command_to_run}', code: 'KeyT'}});
                document.dispatchEvent(event);
                console.log('Command attempted via JS: {command_to_run}');
            """)
            print('Command attempted via JavaScript')
        except:
            print('JavaScript injection also failed')
    
    # 7. Wait and capture output
    print('Step 7: Capturing output...')
    time.sleep(8)
    
    # Get all visible text on page
    try:
        body_text = driver.find_element(By.TAG_NAME, 'body').text
        if body_text:
            print('=' * 60)
            print('PAGE TEXT (last 3000 characters):')
            print('=' * 60)
            # Show last part which might contain terminal output
            output = body_text[-3000:] if len(body_text) > 3000 else body_text
            print(output)
            print('=' * 60)
            
            # Save text to file
            with open('page_output.txt', 'w', encoding='utf-8') as f:
                f.write(body_text)
            print('Page text saved to page_output.txt')
        else:
            print('No text content found on page')
    except:
        print('Could not extract page text')
    
    # Final screenshot
    save_screenshot('final_result.png')
    print('Automation completed successfully!')
    
except Exception as e:
    print(f'ERROR during automation: {str(e)}')
    import traceback
    traceback.print_exc()
    
    try:
        save_screenshot('error_final.png')
    except:
        print('Could not save final error screenshot')
    
    # Save current page source
    try:
        with open('final_page_source.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print('Final page source saved')
    except:
        print('Could not save final page source')
    
    raise

finally:
    driver.quit()
    print('Browser closed. Automation finished.')
