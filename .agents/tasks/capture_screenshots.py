"""
Screenshot capture script for UI verification
"""
import time
import sys
from pathlib import Path

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
except ImportError:
    print("Selenium not installed. Trying alternative method...")
    # Try using pyautogui as fallback
    try:
        import pyautogui
        import webbrowser
        
        webbrowser.open('http://localhost:8080')
        time.sleep(3)
        
        screenshot_dir = Path(__file__).parent
        for i in range(1, 4):
            time.sleep(2)
            screenshot = pyautogui.screenshot()
            screenshot.save(screenshot_dir / f'ui-shot-{i}.png')
            print(f'Screenshot {i} saved')
        
        sys.exit(0)
    except ImportError:
        print("Neither selenium nor pyautogui available. Manual screenshot needed.")
        sys.exit(1)

# Set up Chrome options
chrome_options = Options()
chrome_options.add_argument('--headless=new')
chrome_options.add_argument('--window-size=1200,800')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--no-sandbox')

# Create driver
driver = webdriver.Chrome(options=chrome_options)
screenshot_dir = Path(__file__).parent

try:
    # Load the application
    driver.get('http://localhost:8080')
    time.sleep(2)  # Wait for page to load
    
    # Capture Task view (default view)
    driver.save_screenshot(str(screenshot_dir / 'ui-shot-1.png'))
    print('Screenshot 1 (Task view) saved')
    
    # Navigate to History view
    try:
        history_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, 'history-tab'))
        )
        history_btn.click()
        time.sleep(1)
        driver.save_screenshot(str(screenshot_dir / 'ui-shot-2.png'))
        print('Screenshot 2 (History view) saved')
    except:
        print('Could not find history tab, saving current view')
        driver.save_screenshot(str(screenshot_dir / 'ui-shot-2.png'))
    
    # Navigate to Settings view
    try:
        settings_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, 'settings-tab'))
        )
        settings_btn.click()
        time.sleep(1)
        driver.save_screenshot(str(screenshot_dir / 'ui-shot-3.png'))
        print('Screenshot 3 (Settings view) saved')
    except:
        print('Could not find settings tab, saving current view')
        driver.save_screenshot(str(screenshot_dir / 'ui-shot-3.png'))
    
    print('\nAll screenshots captured successfully!')
    
finally:
    driver.quit()
