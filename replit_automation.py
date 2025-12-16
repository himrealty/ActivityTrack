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
wait = WebDriverWait(driver, 30)

driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

try:
    # 1. Navigate directly to login page
    print('Step 1: Navigating to Replit login...')
    driver.get('https://replit.com/login')
    time.sleep(8)
    driver.save_screenshot('login_page.png')
    
    # 2. Look for "Already have an account? Log in" link
    print('Step 2: Looking for login link...')
    
    # The page shows "Sign Up" but has a "Log in" link
    login_link = None
    login_selectors = [
        'a:contains("Log in")',
        'a:contains("Sign in")',
        'a[href*="login"]',
        'button:contains("Log in")',
        'button:contains("Sign in")',
        'span:contains("Log in")',
        'div:contains("Log in")'
    ]
    
    for selector in login_selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for elem in elements:
                if elem.is_displayed():
                    login_link = elem
                    print(f'Found login link with selector: {selector}')
                    break
            if login_link:
                break
        except:
            continue
    
    if login_link:
        login_link.click()
        print('Clicked login link')
        time.sleep(5)
        driver.save_screenshot('after_click_login.png')
    else:
        print('Login link not found, trying to find login form directly')
    
    # 3. Now look for email/username field
    print('Step 3: Looking for email/username field...')
    
    # Wait for login form to appear
    time.sleep(3)
    
    # Try multiple selectors for email field
    email_selectors = [
        'input[type="email"]',
        'input[name="email"]',
        'input[name="username"]',
        'input[autocomplete="email"]',
        'input[autocomplete="username"]',
        'input[placeholder*="email" i]',
        'input[placeholder*="username" i]',
        'input[data-cy*="email"]',
        'input[data-cy*="username"]',
        'input#email',
        'input#username'
    ]
    
    email_field = None
    for selector in email_selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for elem in elements:
                if elem.is_displayed() and elem.is_enabled():
                    email_field = elem
                    print(f'Found email field with selector: {selector}')
                    break
            if email_field:
                break
        except:
            continue
    
    if not email_field:
        # Try to find any visible input that could be email
        all_inputs = driver.find_elements(By.TAG_NAME, 'input')
        for inp in all_inputs:
            if inp.is_displayed() and inp.is_enabled() and inp.get_attribute('type') != 'hidden':
                email_field = inp
                print('Found input field as email')
                break
    
    if email_field:
        email_field.click()
        time.sleep(1)
        email_field.clear()
        email_field.send_keys(os.environ['REPLIT_EMAIL'])
        print('Email entered')
        time.sleep(2)
    else:
        print('ERROR: Could not find email field')
        driver.save_screenshot('email_not_found.png')
        raise Exception('Email field not found')
    
    # 4. Look for password field
    print('Step 4: Looking for password field...')
    
    password_selectors = [
        'input[type="password"]',
        'input[name="password"]',
        'input[autocomplete="current-password"]',
        'input[placeholder*="password" i]',
        'input[data-cy*="password"]',
        'input#password'
    ]
    
    password_field = None
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
    else:
        print('ERROR: Could not find password field')
        driver.save_screenshot('password_not_found.png')
        raise Exception('Password field not found')
    
    # 5. Submit login form
    print('Step 5: Submitting login form...')
    
    # Try to find submit button
    submit_selectors = [
        'button[type="submit"]',
        'button:contains("Sign in")',
        'button:contains("Log in")',
        'button:contains("Continue")',
        'button[data-cy*="submit"]',
        'button[data-cy*="login"]',
        'input[type="submit"]'
    ]
    
    submitted = False
    for selector in submit_selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for elem in elements:
                if elem.is_displayed():
                    elem.click()
                    print(f'Clicked submit button with selector: {selector}')
                    submitted = True
                    break
            if submitted:
                break
        except:
            continue
    
    if not submitted:
        # Try Enter key
        password_field.send_keys(Keys.RETURN)
        print('Submitted with Enter key')
    
    # 6. Wait for login to complete
    print('Step 6: Waiting for login...')
    time.sleep(10)
    driver.save_screenshot('after_login.png')
    
    # Check if login successful
    if 'login' not in driver.current_url and 'auth' not in driver.current_url:
        print('Login appears successful')
    else:
        print('Still on login page, checking for error messages')
        # Look for error messages
        try:
            error_elements = driver.find_elements(By.CSS_SELECTOR, '[class*="error"], [class*="Error"], [data-cy*="error"]')
            for error in error_elements:
                if error.is_displayed():
                    print(f'Error message: {error.text}')
        except:
            pass
    
    # 7. Navigate to project
    print('Step 7: Navigating to project...')
    project_url = os.environ['REPLIT_PROJECT_URL']
    driver.get(project_url)
    time.sleep(10)
    driver.save_screenshot('project_page.png')
    
    print(f'Project page title: {driver.title}')
    print(f'Project page URL: {driver.current_url}')
    
    # 8. Look for Run button
    print('Step 8: Looking for Run button...')
    
    run_selectors = [
        'button:contains("Run")',
        'button[aria-label*="Run" i]',
        'button[title*="Run" i]',
        'button[data-cy*="run"]',
        'div[data-cy*="run"]',
        'button:contains("▶")',
        'button:contains("▷")'
    ]
    
    run_clicked = False
    for selector in run_selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for elem in elements:
                if elem.is_displayed():
                    elem.click()
                    print(f'Clicked Run button with selector: {selector}')
                    run_clicked = True
                    time.sleep(5)
                    break
            if run_clicked:
                break
        except:
            continue
    
    if run_clicked:
        driver.save_screenshot('after_run.png')
    else:
        print('Run button not found or already running')
    
    # 9. Execute command
    print('Step 9: Executing command...')
    command_to_run = os.environ['COMMAND_TO_RUN']
    print(f'Command: {command_to_run}')
    
    # Look for terminal input
    terminal_selectors = [
        'div[contenteditable="true"]',
        'textarea',
        'input[type="text"]',
        'div[class*="xterm"]',
        'div[class*="terminal"]',
        'pre[class*="xterm"]',
        '[data-cy*="terminal"]'
    ]
    
    terminal_found = False
    for selector in terminal_selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for elem in elements:
                if elem.is_displayed() and elem.is_enabled():
                    try:
                        elem.click()
                        time.sleep(1)
                        elem.send_keys(command_to_run)
                        time.sleep(1)
                        elem.send_keys(Keys.RETURN)
                        terminal_found = True
                        print(f'Command sent via selector: {selector}')
                        break
                    except:
                        continue
            if terminal_found:
                break
        except:
            continue
    
    if not terminal_found:
        print('Could not find terminal input')
    
    # 10. Wait and capture output
    print('Step 10: Capturing output...')
    time.sleep(8)
    driver.save_screenshot('after_command.png')
    
    # Try to get visible text
    try:
        body = driver.find_element(By.TAG_NAME, 'body')
        text = body.text
        if text:
            print('=' * 60)
            print('PAGE TEXT (last 2000 chars):')
            print('=' * 60)
            print(text[-2000:] if len(text) > 2000 else text)
            print('=' * 60)
            
            # Save to file
            with open('output.txt', 'w', encoding='utf-8') as f:
                f.write(text)
            print('Output saved to output.txt')
    except:
        print('Could not extract page text')
    
    # Final screenshot
    driver.save_screenshot('final.png')
    print('Automation completed successfully!')
    
except Exception as e:
    print(f'ERROR: {str(e)}')
    import traceback
    traceback.print_exc()
    
    try:
        driver.save_screenshot('error.png')
        print('Error screenshot saved')
    except:
        print('Could not save error screenshot')
    
    # Save page source
    try:
        with open('error_source.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print('Page source saved')
    except:
        print('Could not save page source')
    
    raise

finally:
    driver.quit()
    print('Browser closed.')
