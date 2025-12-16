import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
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

driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

def save_screenshot(name):
    driver.save_screenshot(name)
    print(f'Screenshot saved: {name}')
    return name

def find_and_click(selectors, description):
    for selector in selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for elem in elements:
                if elem.is_displayed():
                    elem.click()
                    print(f'Clicked: {description}')
                    return True
        except:
            continue
    return False

def find_and_send_keys(selectors, text, description):
    for selector in selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for elem in elements:
                if elem.is_displayed() and elem.is_enabled():
                    elem.click()
                    time.sleep(0.5)
                    elem.clear()
                    elem.send_keys(text)
                    print(f'Entered: {description}')
                    return elem
        except:
            continue
    return None

try:
    # 1. Navigate to Replit login
    print('Step 1: Navigating to Replit login...')
    driver.get('https://replit.com/login')
    time.sleep(8)
    save_screenshot('1_login_page.png')
    
    # 2. Click "Log in" link (page shows Sign Up but has Log in link)
    print('Step 2: Clicking Log in link...')
    login_clicked = find_and_click([
        'a:contains("Log in")',
        'a:contains("Sign in")',
        'button:contains("Log in")',
        'button:contains("Sign in")'
    ], 'Log in link')
    
    if login_clicked:
        time.sleep(5)
        save_screenshot('2_after_login_click.png')
    else:
        print('Log in link not found, trying to find login form directly')
    
    # 3. Enter email
    print('Step 3: Entering email...')
    email_field = find_and_send_keys([
        'input[type="email"]',
        'input[name="email"]',
        'input[name="username"]',
        'input[autocomplete="email"]',
        'input[autocomplete="username"]',
        'input[placeholder*="email" i]',
        'input[placeholder*="username" i]'
    ], os.environ['REPLIT_EMAIL'], 'email')
    
    if not email_field:
        raise Exception('Email field not found')
    
    time.sleep(2)
    
    # 4. Enter password
    print('Step 4: Entering password...')
    password_field = find_and_send_keys([
        'input[type="password"]',
        'input[name="password"]',
        'input[autocomplete="current-password"]',
        'input[placeholder*="password" i]'
    ], os.environ['REPLIT_PASSWORD'], 'password')
    
    if not password_field:
        raise Exception('Password field not found')
    
    time.sleep(2)
    save_screenshot('3_credentials_entered.png')
    
    # 5. Submit login
    print('Step 5: Submitting login...')
    submitted = find_and_click([
        'button[type="submit"]',
        'button:contains("Sign in")',
        'button:contains("Log in")',
        'button:contains("Continue")'
    ], 'submit button')
    
    if not submitted:
        password_field.send_keys(Keys.RETURN)
        print('Submitted with Enter key')
    
    # 6. Wait for login
    print('Step 6: Waiting for login...')
    time.sleep(10)
    save_screenshot('4_after_login.png')
    
    # 7. Navigate to project
    print('Step 7: Navigating to project...')
    driver.get(os.environ['REPLIT_PROJECT_URL'])
    time.sleep(10)
    save_screenshot('5_project_page.png')
    
    # 8. Click Run button
    print('Step 8: Clicking Run button...')
    run_clicked = find_and_click([
        'button:contains("Run")',
        'button[aria-label*="Run" i]',
        'button[title*="Run" i]',
        'button:contains("▶")'
    ], 'Run button')
    
    if run_clicked:
        time.sleep(5)
        save_screenshot('6_after_run.png')
    else:
        print('Run button not found or already running')
    
    # 9. Execute command
    print('Step 9: Executing command...')
    command = os.environ['COMMAND_TO_RUN']
    print(f'Command: {command}')
    
    # Try to find and use terminal
    terminal_found = False
    for selector in ['div[contenteditable="true"]', 'textarea', 'input[type="text"]', 'div[class*="xterm"]']:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for elem in elements:
                if elem.is_displayed() and elem.is_enabled():
                    elem.click()
                    time.sleep(1)
                    elem.send_keys(command)
                    time.sleep(1)
                    elem.send_keys(Keys.RETURN)
                    terminal_found = True
                    print('Command sent to terminal')
                    break
            if terminal_found:
                break
        except:
            continue
    
    if not terminal_found:
        print('Terminal input not found')
    
    # 10. Capture output
    print('Step 10: Capturing output...')
    time.sleep(8)
    save_screenshot('7_after_command.png')
    
    # Get page text
    try:
        text = driver.find_element(By.TAG_NAME, 'body').text
        if text:
            print('=' * 60)
            print('OUTPUT:')
            print('=' * 60)
            print(text[-3000:] if len(text) > 3000 else text)
            print('=' * 60)
            
            with open('output.txt', 'w', encoding='utf-8') as f:
                f.write(text)
            print('Output saved to output.txt')
    except:
        print('Could not extract text')
    
    save_screenshot('8_final.png')
    print('✅ Automation completed successfully!')
    
except Exception as e:
    print(f'❌ ERROR: {str(e)}')
    import traceback
    traceback.print_exc()
    
    try:
        save_screenshot('error.png')
    except:
        pass
    
    try:
        with open('error_source.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
    except:
        pass
    
    raise

finally:
    driver.quit()
    print('Browser closed.')
