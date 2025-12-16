import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
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
driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

try:
    # 1. Navigate to Replit login page
    print('Step 1: Navigating to Replit login...')
    driver.get('https://replit.com/login')
    time.sleep(3)
    
    # 2. Handle cookie consent if present
    try:
        cookie_button = driver.find_element(By.XPATH, '//button[contains(text(), "Accept") or contains(text(), "Got it")]')
        cookie_button.click()
        print('Cookie consent accepted')
        time.sleep(1)
    except:
        print('No cookie consent found')
    
    # 3. Fill login form
    print('Step 2: Filling login credentials...')
    
    # Find email field using multiple selectors
    try:
        email_field = driver.find_element(By.NAME, 'email')
    except:
        try:
            email_field = driver.find_element(By.CSS_SELECTOR, 'input[type="email"]')
        except:
            try:
                email_field = driver.find_element(By.CSS_SELECTOR, 'input[name="username"]')
            except:
                print('Could not find email field, taking screenshot')
                driver.save_screenshot('login_page.png')
                raise
    
    email_field.clear()
    email_field.send_keys(os.environ['REPLIT_EMAIL'])
    time.sleep(1)
    
    # Find password field
    try:
        password_field = driver.find_element(By.NAME, 'password')
    except:
        try:
            password_field = driver.find_element(By.CSS_SELECTOR, 'input[type="password"]')
        except:
            print('Could not find password field')
            driver.save_screenshot('login_page2.png')
            raise
    
    password_field.clear()
    password_field.send_keys(os.environ['REPLIT_PASSWORD'])
    time.sleep(1)
    
    # 4. Submit login form
    print('Step 3: Submitting login form...')
    try:
        login_button = driver.find_element(By.XPATH, '//button[contains(text(), "Sign in") or contains(text(), "Log in") or @type="submit"]')
        login_button.click()
    except:
        password_field.send_keys(Keys.RETURN)
    
    time.sleep(5)
    
    # 5. Navigate to specific project
    print('Step 4: Navigating to project...')
    project_url = os.environ['REPLIT_PROJECT_URL']
    driver.get(project_url)
    time.sleep(5)
    
    # 6. Open shell/terminal
    print('Step 5: Opening terminal/shell...')
    
    try:
        run_button = driver.find_element(By.XPATH, '//button[contains(text(), "Run")]')
        run_button.click()
        print('Clicked Run button')
        time.sleep(5)
    except:
        print('Run button not found or project already running')
    
    # 7. Find terminal input and execute command
    print('Step 6: Executing command in terminal...')
    command_to_run = os.environ['COMMAND_TO_RUN']
    print(f'Command to execute: {command_to_run}')
    
    terminal_input = None
    for attempt in range(10):
        try:
            selectors = [
                'div[data-cy="terminal-input"]',
                'textarea.terminal-input',
                'div.xterm-helper-textarea',
                'div[contenteditable="true"]',
                'pre.xterm-helper-textarea',
                '.xterm textarea'
            ]
            
            for selector in selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in elements:
                        if elem.is_displayed() and elem.is_enabled():
                            terminal_input = elem
                            print(f'Found terminal input with selector: {selector}')
                            break
                    if terminal_input:
                        break
                except:
                    continue
        
        except Exception as e:
            print(f'Attempt {attempt + 1}: {str(e)}')
        
        if terminal_input:
            break
        time.sleep(2)
    
    if terminal_input:
        terminal_input.click()
        time.sleep(1)
        terminal_input.clear()
        time.sleep(1)
        terminal_input.send_keys(command_to_run)
        time.sleep(1)
        terminal_input.send_keys(Keys.RETURN)
        print('Command sent to terminal')
        time.sleep(5)
        
        print('Step 7: Capturing output...')
        
        output_selectors = [
            'div.xterm-screen',
            'div[data-cy="terminal-output"]',
            '.terminal-output',
            '.xterm-viewport',
            'div[class*="xterm"]'
        ]
        
        terminal_output = None
        for selector in output_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elements:
                    if elem.is_displayed():
                        terminal_output = elem
                        print(f'Found output with selector: {selector}')
                        break
            except:
                continue
        
        if terminal_output:
            output_text = terminal_output.text
            print('=' * 50)
            print('TERMINAL OUTPUT:')
            print('=' * 50)
            print(output_text if output_text else '(No output visible)')
            print('=' * 50)
        else:
            print('Could not capture terminal output')
    else:
        print('ERROR: Could not find terminal input element')
    
    driver.save_screenshot('final_state.png')
    print('Final screenshot saved: final_state.png')
    
except Exception as e:
    print(f'ERROR during automation: {str(e)}')
    import traceback
    traceback.print_exc()
    
    try:
        driver.save_screenshot('error_state.png')
        print('Error screenshot saved: error_state.png')
    except:
        print('Could not save error screenshot')
    
    raise

finally:
    driver.quit()
    print('Automation completed.')
