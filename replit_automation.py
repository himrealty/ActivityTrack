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

# Setup Chrome options for GitHub Actions
chrome_options = Options()
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--headless')
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

try:
    # 1. Navigate to Replit login page
    print('Step 1: Navigating to Replit login...')
    driver.get('https://replit.com/login')
    time.sleep(5)
    
    # Save initial screenshot
    driver.save_screenshot('initial_page.png')
    print('Initial screenshot saved')
    
    # 2. Handle cookie consent if present
    try:
        cookie_buttons = driver.find_elements(By.XPATH, '//button[contains(text(), "Accept") or contains(text(), "Got it") or contains(text(), "Agree")]')
        if cookie_buttons:
            cookie_buttons[0].click()
            print('Cookie consent accepted')
            time.sleep(2)
    except:
        print('No cookie consent found')
    
    # 3. Look for email/username field using multiple strategies
    print('Step 2: Looking for login fields...')
    
    # Try to find if it's a different login flow (might be Google OAuth or other)
    page_source = driver.page_source.lower()
    
    # Check for different login options
    login_selectors = [
        # New Replit login selectors
        ('input[data-cy="login-email-input"]', 'data-cy email input'),
        ('input[placeholder*="email" i]', 'email placeholder'),
        ('input[placeholder*="username" i]', 'username placeholder'),
        ('input[placeholder*="user" i]', 'user placeholder'),
        ('input[autocomplete="email"]', 'autocomplete email'),
        ('input[autocomplete="username"]', 'autocomplete username'),
        ('input[type="text"][name*="email"]', 'text email'),
        ('input[type="text"][name*="user"]', 'text user'),
        ('input#email', 'email id'),
        ('input#username', 'username id'),
        ('input.login-email', 'login-email class'),
        ('input.login-input', 'login-input class'),
        ('input.form-input', 'form-input class'),
        # More generic selectors
        ('input[type="text"]:not([type="search"])', 'generic text input'),
        ('input:not([type="hidden"])', 'any visible input')
    ]
    
    email_field = None
    password_field = None
    
    # First try to find email field
    for selector, description in login_selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for elem in elements:
                if elem.is_displayed() and elem.is_enabled():
                    # Check if it's likely an email field
                    elem_location = elem.location
                    elem_size = elem.size
                    # Save screenshot of found element
                    driver.save_screenshot(f'found_element_{description.replace(" ", "_")}.png')
                    email_field = elem
                    print(f'Found potential email field: {description}')
                    break
            if email_field:
                break
        except:
            continue
    
    if not email_field:
        # Last resort: try to click any visible input
        try:
            all_inputs = driver.find_elements(By.TAG_NAME, 'input')
            for inp in all_inputs:
                if inp.is_displayed() and inp.is_enabled() and inp.get_attribute('type') != 'hidden':
                    email_field = inp
                    print('Found input field as last resort')
                    break
        except:
            pass
    
    if email_field:
        email_field.click()
        time.sleep(1)
        email_field.clear()
        email_field.send_keys(os.environ['REPLIT_EMAIL'])
        print('Email entered')
        time.sleep(2)
        
        # Try to find and click Continue/Next button
        continue_buttons = [
            'button[type="submit"]',
            'button:contains("Continue")',
            'button:contains("Next")',
            'button[data-cy*="continue"]',
            'button[data-cy*="next"]'
        ]
        
        for button_selector in continue_buttons:
            try:
                buttons = driver.find_elements(By.CSS_SELECTOR, button_selector)
                for btn in buttons:
                    if btn.is_displayed():
                        btn.click()
                        print('Clicked Continue/Next button')
                        time.sleep(3)
                        break
            except:
                continue
        
        # Now look for password field
        print('Looking for password field...')
        password_selectors = [
            'input[type="password"]',
            'input[data-cy="login-password-input"]',
            'input[placeholder*="password" i]',
            'input[autocomplete="current-password"]',
            'input#password',
            'input.password-input'
        ]
        
        for selector in password_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elements:
                    if elem.is_displayed():
                        password_field = elem
                        print('Found password field')
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
            
            # Submit login
            submit_selectors = [
                'button[type="submit"]',
                'button:contains("Sign in")',
                'button:contains("Log in")',
                'button[data-cy*="login"]',
                'button[data-cy*="submit"]'
            ]
            
            for selector in submit_selectors:
                try:
                    buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                    for btn in buttons:
                        if btn.is_displayed():
                            btn.click()
                            print('Clicked Sign in button')
                            time.sleep(3)
                            break
                    break
                except:
                    continue
        else:
            # If no password field found, maybe it's OAuth or different flow
            print('No password field found, trying Enter key')
            email_field.send_keys(Keys.RETURN)
            time.sleep(3)
    else:
        print('ERROR: Could not find any login input field')
        driver.save_screenshot('no_login_field.png')
        raise Exception('No login field found')
    
    # 4. Wait for login to complete and check if successful
    print('Step 3: Waiting for login to complete...')
    time.sleep(8)
    
    # Check if login was successful by looking for user avatar or dashboard elements
    driver.save_screenshot('after_login.png')
    
    # 5. Navigate to specific project
    print('Step 4: Navigating to project...')
    project_url = os.environ['REPLIT_PROJECT_URL']
    driver.get(project_url)
    time.sleep(8)
    driver.save_screenshot('project_page.png')
    
    # 6. Try to find and interact with terminal
    print('Step 5: Looking for terminal/shell...')
    
    # Try Run button
    run_button_found = False
    run_button_selectors = [
        'button:contains("Run")',
        'button[data-cy="run-button"]',
        'button.run-button',
        '[aria-label*="Run" i]',
        'button[title*="Run" i]'
    ]
    
    for selector in run_button_selectors:
        try:
            buttons = driver.find_elements(By.CSS_SELECTOR, selector)
            for btn in buttons:
                if btn.is_displayed():
                    btn.click()
                    print('Clicked Run button')
                    run_button_found = True
                    time.sleep(5)
                    break
            if run_button_found:
                break
        except:
            continue
    
    if not run_button_found:
        print('Run button not found or project already running')
    
    # 7. Find terminal input and execute command
    print('Step 6: Looking for terminal input...')
    command_to_run = os.environ['COMMAND_TO_RUN']
    print(f'Command to execute: {command_to_run}')
    
    terminal_input = None
    terminal_selectors = [
        'div[contenteditable="true"]',
        '.xterm-helper-textarea',
        'textarea.xterm-helper-textarea',
        'div.xterm-textarea',
        'pre.xterm-helper-textarea',
        '.terminal-input',
        '[data-cy="terminal-input"]',
        'div[class*="terminal"]',
        'div[class*="xterm"]',
        'textarea',
        'input[type="text"]'
    ]
    
    for selector in terminal_selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for elem in elements:
                if elem.is_displayed() and elem.is_enabled():
                    terminal_input = elem
                    print(f'Found terminal input with selector: {selector}')
                    driver.save_screenshot(f'terminal_found_{selector.replace("[", "").replace("]", "").replace(".", "")}.png')
                    break
            if terminal_input:
                break
        except:
            continue
    
    if terminal_input:
        terminal_input.click()
        time.sleep(2)
        
        # Try different ways to input text
        try:
            terminal_input.clear()
        except:
            pass
        
        terminal_input.send_keys(command_to_run)
        time.sleep(1)
        terminal_input.send_keys(Keys.RETURN)
        print('Command sent to terminal')
        
        # Wait for output
        time.sleep(8)
        
        # 8. Capture any visible output
        print('Step 7: Capturing output...')
        driver.save_screenshot('after_command.png')
        
        # Try to get page source which might contain output
        page_text = driver.page_source
        if len(page_text) > 1000:  # If there's substantial content
            # Extract visible text
            all_text = driver.find_element(By.TAG_NAME, 'body').text
            print('=' * 50)
            print('PAGE TEXT CONTENT:')
            print('=' * 50)
            # Show last 2000 chars which might contain terminal output
            print(all_text[-2000:] if len(all_text) > 2000 else all_text)
            print('=' * 50)
        else:
            print('Page seems empty, command may not have executed')
        
    else:
        print('WARNING: Could not find terminal input')
        print('Taking full page screenshot for debugging')
    
    # 9. Final screenshot
    driver.save_screenshot('final_state.png')
    print('Final screenshot saved: final_state.png')
    print('Check uploaded screenshots for debugging')
    
except Exception as e:
    print(f'ERROR during automation: {str(e)}')
    import traceback
    traceback.print_exc()
    
    try:
        driver.save_screenshot('error_state.png')
        print('Error screenshot saved: error_state.png')
    except:
        print('Could not save error screenshot')
    
    # Try to save page source for debugging
    try:
        with open('page_source.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print('Page source saved: page_source.html')
    except:
        print('Could not save page source')
    
    raise

finally:
    driver.quit()
    print('Automation completed.')
