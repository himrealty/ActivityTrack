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

# Setup Chrome
chrome_options = Options()
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--headless')
chrome_options.add_argument('--window-size=1920,1080')
chrome_options.add_argument('--disable-blink-features=AutomationControlled')
chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)
wait = WebDriverWait(driver, 20)

def wait_for_page_load():
    """Wait for page to be fully loaded"""
    time.sleep(3)
    driver.execute_script("return document.readyState") == "complete"

def safe_screenshot(name):
    """Take screenshot with error handling"""
    try:
        driver.save_screenshot(f'{name}.png')
        print(f'Screenshot saved: {name}.png')
    except Exception as e:
        print(f'Failed to save screenshot {name}: {e}')

try:
    # 1. Go to login page
    print('Step 1: Navigating to login page')
    driver.get('https://replit.com/login')
    wait_for_page_load()
    safe_screenshot('1_initial_page')
    
    # Wait for any initial redirects or page loads
    time.sleep(5)
    
    # Check current URL
    current_url = driver.current_url
    print(f'Current URL: {current_url}')
    
    # Save page source for debugging
    with open('page_source.html', 'w', encoding='utf-8') as f:
        f.write(driver.page_source)
    print('Page source saved to page_source.html')
    
    # 2. Look for email/username field with multiple strategies
    print('Step 2: Looking for email/username field')
    
    # Strategy 1: Wait for input fields to be present
    input_selectors = [
        "input[type='email']",
        "input[name*='email' i]",
        "input[name*='username' i]",
        "input[placeholder*='email' i]",
        "input[placeholder*='username' i]",
        "input[id*='email' i]",
        "input[id*='username' i]",
        "input[autocomplete='email']",
        "input[autocomplete='username']"
    ]
    
    email_input = None
    for selector in input_selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for elem in elements:
                if elem.is_displayed():
                    email_input = elem
                    print(f'Found email field using selector: {selector}')
                    break
            if email_input:
                break
        except Exception as e:
            continue
    
    # Strategy 2: Use JavaScript to find first visible text/email input
    if not email_input:
        print('Trying JavaScript approach to find email field...')
        email_input = driver.execute_script("""
            // Find all input elements
            const inputs = Array.from(document.querySelectorAll('input'));
            
            // Filter for visible inputs that could be email/username
            const candidates = inputs.filter(input => {
                const style = window.getComputedStyle(input);
                const isVisible = style.display !== 'none' && 
                                style.visibility !== 'hidden' && 
                                input.offsetParent !== null;
                
                if (!isVisible) return false;
                
                const type = (input.type || '').toLowerCase();
                const name = (input.name || '').toLowerCase();
                const placeholder = (input.placeholder || '').toLowerCase();
                const id = (input.id || '').toLowerCase();
                const autocomplete = (input.autocomplete || '').toLowerCase();
                
                // Check if it's likely an email/username field
                return type === 'email' || 
                       type === 'text' ||
                       name.includes('email') || 
                       name.includes('username') ||
                       placeholder.includes('email') ||
                       placeholder.includes('username') ||
                       id.includes('email') ||
                       id.includes('username') ||
                       autocomplete === 'email' ||
                       autocomplete === 'username';
            });
            
            console.log('Found candidates:', candidates.length);
            return candidates[0] || null;
        """)
    
    if not email_input:
        print('ERROR: Could not find email input field')
        # Take screenshot and save HTML for debugging
        safe_screenshot('2_email_not_found')
        
        # Print all visible inputs for debugging
        all_inputs = driver.find_elements(By.TAG_NAME, 'input')
        print(f'\nFound {len(all_inputs)} total input elements:')
        for i, inp in enumerate(all_inputs):
            try:
                print(f'  Input {i}: type={inp.get_attribute("type")}, '
                      f'name={inp.get_attribute("name")}, '
                      f'id={inp.get_attribute("id")}, '
                      f'placeholder={inp.get_attribute("placeholder")}, '
                      f'visible={inp.is_displayed()}')
            except:
                pass
        raise Exception('Email field not found')
    
    # 3. Fill email
    print('Step 3: Filling email field')
    email = os.environ['REPLIT_EMAIL']
    
    # Clear and fill using multiple methods for reliability
    try:
        email_input.clear()
    except:
        pass
    
    email_input.send_keys(email)
    
    # Verify value was set
    time.sleep(1)
    current_value = email_input.get_attribute('value')
    print(f'Email field value after fill: {current_value}')
    
    safe_screenshot('3_email_filled')
    
    # 4. Find and fill password field
    print('Step 4: Looking for password field')
    
    password_input = None
    try:
        password_input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password']"))
        )
        print('Found password field')
    except:
        # Fallback to JavaScript
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
        print('ERROR: Could not find password field')
        safe_screenshot('4_password_not_found')
        raise Exception('Password field not found')
    
    password = os.environ['REPLIT_PASSWORD']
    try:
        password_input.clear()
    except:
        pass
    
    password_input.send_keys(password)
    time.sleep(1)
    
    safe_screenshot('4_password_filled')
    
    # 5. Find and click submit button
    print('Step 5: Looking for submit button')
    
    # Try multiple selectors for submit button
    submit_selectors = [
        "button[type='submit']",
        "button:contains('Sign in')",
        "button:contains('Log in')",
        "button:contains('Continue')",
        "input[type='submit']"
    ]
    
    submit_button = None
    for selector in submit_selectors:
        try:
            buttons = driver.find_elements(By.CSS_SELECTOR, selector.split(':')[0])
            for btn in buttons:
                if btn.is_displayed():
                    text = btn.text.lower()
                    if any(word in text for word in ['sign in', 'log in', 'continue', 'submit']):
                        submit_button = btn
                        print(f'Found submit button with text: {btn.text}')
                        break
            if submit_button:
                break
        except:
            continue
    
    # Fallback to JavaScript
    if not submit_button:
        print('Using JavaScript to find submit button...')
        submit_button = driver.execute_script("""
            const buttons = Array.from(document.querySelectorAll('button, input[type="submit"]'));
            return buttons.find(btn => {
                const style = window.getComputedStyle(btn);
                const isVisible = style.display !== 'none' && 
                                style.visibility !== 'hidden' && 
                                btn.offsetParent !== null;
                
                if (!isVisible) return false;
                
                const text = (btn.textContent || btn.value || '').toLowerCase();
                return text.includes('sign in') || 
                       text.includes('log in') || 
                       text.includes('continue') ||
                       btn.type === 'submit';
            }) || null;
        """)
    
    if not submit_button:
        # Last resort: submit form with Enter key
        print('Submit button not found, trying Enter key')
        password_input.send_keys(Keys.RETURN)
    else:
        submit_button.click()
        print('Submit button clicked')
    
    time.sleep(8)
    safe_screenshot('5_after_submit')
    
    # Check if login was successful
    current_url = driver.current_url
    print(f'Current URL after login: {current_url}')
    
    # 6. Navigate to project
    print('Step 6: Navigating to project')
    project_url = os.environ['REPLIT_PROJECT_URL']
    driver.get(project_url)
    time.sleep(10)
    safe_screenshot('6_project_page')
    
    # 7. Click Run button or execute command
    print('Step 7: Looking for Run button or Shell')
    command = os.environ.get('COMMAND_TO_RUN', '').strip()
    print(f'Command to run: {command}')
    
    # Wait for page to fully load
    time.sleep(5)
    
    # Strategy 1: Try to click the Run button first
    run_clicked = False
    if not command or command.lower() in ['run', 'click run', 'start']:
        print('Attempting to click Run button...')
        
        # Try multiple selectors for Run button
        run_button = driver.execute_script("""
            // Look for Run button
            const buttons = Array.from(document.querySelectorAll('button, [role="button"], .run-button'));
            
            for (const btn of buttons) {
                const text = (btn.textContent || btn.innerText || '').trim().toLowerCase();
                const ariaLabel = (btn.getAttribute('aria-label') || '').toLowerCase();
                const title = (btn.getAttribute('title') || '').toLowerCase();
                const className = (btn.className || '').toLowerCase();
                
                // Check if it's a Run button
                if (text === 'run' || 
                    text.includes('▶') || 
                    ariaLabel.includes('run') || 
                    title.includes('run') ||
                    className.includes('run')) {
                    
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
            try:
                run_button.click()
                print('✓ Run button clicked!')
                run_clicked = True
                time.sleep(3)
                safe_screenshot('7a_run_button_clicked')
            except Exception as e:
                print(f'Failed to click run button: {e}')
        else:
            print('Run button not found')
    
    # Strategy 2: If no Run button or need to execute a specific command
    if not run_clicked and command and command.lower() not in ['run', 'click run', 'start']:
        print(f'Attempting to execute command in shell: {command}')
        
        # First, try to open/focus the Shell tab
        shell_opened = driver.execute_script("""
            // Look for Shell tab
            const tabs = Array.from(document.querySelectorAll('[role="tab"], .tab, button'));
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
            print('Shell tab opened')
            time.sleep(2)
            safe_screenshot('7b_shell_opened')
        
        # Now try to interact with shell
        time.sleep(2)
        
        # Escape command for JavaScript
        escaped_command = command.replace("'", "\\'")
        result = driver.execute_script(f"""
            const command = '{escaped_command}';
            let executed = false;
            
            // Method 1: Look for Xterm.js terminal (common in Replit)
            const xtermElements = document.querySelectorAll('.xterm-helper-textarea, .terminal textarea');
            for (const elem of xtermElements) {{
                try {{
                    elem.focus();
                    elem.value = command;
                    elem.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    
                    // Send Enter
                    const enterEvent = new KeyboardEvent('keydown', {{
                        key: 'Enter',
                        code: 'Enter',
                        keyCode: 13,
                        which: 13,
                        bubbles: true,
                        cancelable: true
                    }});
                    elem.dispatchEvent(enterEvent);
                    executed = true;
                    console.log('Command sent via xterm textarea');
                    break;
                }} catch(e) {{ console.error(e); }}
            }}
            
            // Method 2: Look for contenteditable divs
            if (!executed) {{
                const editables = document.querySelectorAll('[contenteditable="true"]');
                for (const elem of editables) {{
                    try {{
                        elem.focus();
                        elem.textContent = command;
                        elem.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        
                        const enterEvent = new KeyboardEvent('keydown', {{
                            key: 'Enter',
                            code: 'Enter',
                            keyCode: 13,
                            which: 13,
                            bubbles: true,
                            cancelable: true
                        }});
                        elem.dispatchEvent(enterEvent);
                        executed = true;
                        console.log('Command sent via contenteditable');
                        break;
                    }} catch(e) {{ console.error(e); }}
                }}
            }}
            
            // Method 3: Try regular textareas
            if (!executed) {{
                const textareas = document.querySelectorAll('textarea');
                for (const elem of textareas) {{
                    try {{
                        elem.focus();
                        elem.value = command;
                        elem.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        elem.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        
                        const enterEvent = new KeyboardEvent('keydown', {{
                            key: 'Enter',
                            code: 'Enter',
                            keyCode: 13,
                            which: 13,
                            bubbles: true,
                            cancelable: true
                        }});
                        elem.dispatchEvent(enterEvent);
                        executed = true;
                        console.log('Command sent via textarea');
                        break;
                    }} catch(e) {{ console.error(e); }}
                }}
            }}
            
            // Method 4: Try to find any focused element and send keys
            if (!executed) {{
                try {{
                    const active = document.activeElement;
                    if (active) {{
                        active.value = command;
                        active.textContent = command;
                        active.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        
                        const enterEvent = new KeyboardEvent('keydown', {{
                            key: 'Enter',
                            code: 'Enter',
                            keyCode: 13,
                            which: 13,
                            bubbles: true,
                            cancelable: true
                        }});
                        active.dispatchEvent(enterEvent);
                        executed = true;
                        console.log('Command sent to active element');
                    }}
                }} catch(e) {{ console.error(e); }}
            }}
            
            return executed ? 'Command sent to shell' : 'No shell input found';
        """)
        
        print(f'Shell interaction result: {result}')
        
        # Alternative: Use Selenium to send keys directly
        if 'No shell input found' in result:
            print('Trying Selenium sendKeys as fallback...')
            try:
                # Find any textarea or input that might be the shell
                shell_inputs = driver.find_elements(By.CSS_SELECTOR, 
                    'textarea, input[type="text"], .xterm-helper-textarea, [contenteditable="true"]')
                
                for elem in shell_inputs:
                    try:
                        if elem.is_displayed():
                            elem.click()
                            time.sleep(0.5)
                            elem.send_keys(command)
                            elem.send_keys(Keys.RETURN)
                            print('Command sent via Selenium sendKeys')
                            break
                    except:
                        continue
            except Exception as e:
                print(f'Selenium fallback failed: {e}')
    
    time.sleep(8)  # Wait longer for command to execute
    safe_screenshot('7_after_command')
    
    # 8. Wait and capture output
    print('Step 8: Waiting for execution and capturing output')
    
    # Get wait time from environment or default to 15 seconds
    wait_time = int(os.environ.get('WAIT_TIME', '15'))
    print(f'Waiting {wait_time} seconds for command to complete...')
    
    # Wait and take periodic screenshots
    for i in range(0, wait_time, 5):
        time.sleep(5)
        safe_screenshot(f'8_progress_{i+5}s')
        print(f'  ... {i+5}s elapsed')
    
    # Capture final state
    print('\nCapturing final output...')
    
    # Get all text from page
    page_text = driver.execute_script("""
        return document.body.innerText || document.body.textContent || '';
    """)
    
    # Try to get console/shell output specifically
    console_output = driver.execute_script("""
        // Try to find console/terminal output areas
        const consoleSelectors = [
            '.console-output',
            '.terminal-output', 
            '.xterm-rows',
            '.shell-output',
            '[class*="console"]',
            '[class*="terminal"]',
            '[class*="output"]'
        ];
        
        let output = '';
        for (const selector of consoleSelectors) {
            const elements = document.querySelectorAll(selector);
            for (const elem of elements) {
                const text = elem.innerText || elem.textContent || '';
                if (text.length > output.length) {
                    output = text;
                }
            }
        }
        
        return output || 'No console output found';
    """)
    
    # Get browser console logs
    try:
        logs = driver.get_log('browser')
        console_logs = '\n'.join([f"{log['level']}: {log['message']}" for log in logs])
    except:
        console_logs = 'Could not retrieve browser console logs'
    
    print('=' * 70)
    print('PAGE TEXT OUTPUT:')
    print('=' * 70)
    if page_text:
        # Print last 2000 characters
        print(page_text[-2000:] if len(page_text) > 2000 else page_text)
        with open('page_output.txt', 'w', encoding='utf-8') as f:
            f.write(page_text)
        print('\nFull page output saved to page_output.txt')
    else:
        print('No page text captured')
    
    print('\n' + '=' * 70)
    print('CONSOLE/SHELL OUTPUT:')
    print('=' * 70)
    if console_output and console_output != 'No console output found':
        print(console_output[-2000:] if len(console_output) > 2000 else console_output)
        with open('console_output.txt', 'w', encoding='utf-8') as f:
            f.write(console_output)
        print('\nFull console output saved to console_output.txt')
    else:
        print(console_output)
    
    print('\n' + '=' * 70)
    print('BROWSER CONSOLE LOGS:')
    print('=' * 70)
    print(console_logs[-1000:] if len(console_logs) > 1000 else console_logs)
    with open('browser_logs.txt', 'w', encoding='utf-8') as f:
        f.write(console_logs)
    print('\nBrowser logs saved to browser_logs.txt')
    print('=' * 70)
    
    safe_screenshot('8_final')
    print('\n✅ Automation completed successfully')
    
except Exception as e:
    print(f'\n❌ Error occurred: {e}')
    import traceback
    traceback.print_exc()
    
    safe_screenshot('error')
    
    try:
        with open('error_page_source.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print('Error page source saved to error_page_source.html')
    except:
        pass
    
    raise

finally:
    print('Closing browser...')
    driver.quit()
    print('Done!')
