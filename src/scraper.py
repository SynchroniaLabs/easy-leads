from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time, pandas as pd, re, os

def scraper(query: str, location: str, save_path: str) -> None:
    """Scrape Google Maps for business data and save to Excel."""
    
    driver = webdriver.Chrome()
    driver.maximize_window()  # Full screen so details show in side panel
    businesses = []

    try:
        # Navigate to Google Maps
        driver.get(f"https://www.google.com/maps/search/{query}+in+{location}")
        time.sleep(5)

        # Handle consent popup
        if "consent.google.com" in driver.current_url:
            try:
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Tout accepter']/parent::button"))).click()
                time.sleep(3)
            except:
                pass

        # Scroll to load more results
        elements = driver.find_elements(By.CSS_SELECTOR, 'div.Nv2PK')
        if elements:
            current = elements[0]
            for _ in range(10):
                try:
                    parent = current.find_element(By.XPATH, '..')
                    if driver.execute_script("return window.getComputedStyle(arguments[0]).overflowY;", parent) in ['scroll', 'auto']:
                        for i in range(5):
                            driver.execute_script("arguments[0].scrollTop += 500;", parent)
                            time.sleep(2)
                        break
                    current = parent
                except:
                    break
        
        # Process each business by clicking individually  
        current_elements = driver.find_elements(By.CSS_SELECTOR, 'div.Nv2PK')
        max_businesses = min(10, len(current_elements))
        
        for i in range(max_businesses):
            try:
                # Re-get elements to avoid stale references
                current_elements = driver.find_elements(By.CSS_SELECTOR, 'div.Nv2PK')
                if i >= len(current_elements):
                    break
                    
                element = current_elements[i]
                print(f"\nProcessing business {i+1}/{max_businesses}")
                
                # Click on the business to get detailed view
                try:
                    clickable = element.find_element(By.CSS_SELECTOR, 'a')
                    driver.execute_script("arguments[0].click();", clickable)
                    time.sleep(4)
                    
                    # Extract ALL data from detail page
                    # Get business name from detail panel (using exact selectors)
                    name = 'N/A'
                    try:
                        # Target the exact selectors you identified
                        selectors = [
                            'h1.DUwDvf.lfPIob',           # Main business title h1
                            '.qBF1Pd.fontHeadlineSmall',  # Alternative business title div
                            'h1.DUwDvf',                  # Fallback h1 with DUwDvf class
                        ]
                        
                        for selector in selectors:
                            try:
                                name_elem = driver.find_element(By.CSS_SELECTOR, selector)
                                text = name_elem.text.strip()
                                # Only filter out obvious ads, not business names
                                if text and text not in ['Sponsorisé', 'Sponsored', 'Résultats', 'Results', 'Annonce']:
                                    name = text
                                    break
                            except:
                                continue
                    except:
                        pass
                    
                    # Get address
                    address = 'N/A'
                    try:
                        addr_elem = driver.find_element(By.CSS_SELECTOR, 'button[data-item-id="address"]')
                        address = addr_elem.get_attribute('aria-label').replace('Adresse: ', '')
                    except:
                        try:
                            addr_elem = driver.find_element(By.CSS_SELECTOR, '[data-item-id="address"] .Io6YTe')
                            address = addr_elem.text.strip()
                        except:
                            pass
                    
                    # Get phone
                    phone = 'N/A'
                    try:
                        phone_elem = driver.find_element(By.CSS_SELECTOR, 'button[data-item-id*="phone"]')
                        phone_text = phone_elem.get_attribute('aria-label') or phone_elem.text
                        phone_match = re.search(r'0[1-9](?:\s?\d{2}){4}', phone_text)
                        if phone_match:
                            phone = phone_match.group(0)
                    except:
                        pass
                    
                    # Get website  
                    website = 'N/A'
                    try:
                        website_elem = driver.find_element(By.CSS_SELECTOR, 'a[data-item-id*="authority"]')
                        website = website_elem.get_attribute('href')
                    except:
                        pass
                    
                    # Get rating
                    rating = 'N/A'
                    try:
                        rating_elem = driver.find_element(By.CSS_SELECTOR, '.F7nice span[aria-hidden="true"]')
                        rating = rating_elem.text.strip()
                    except:
                        pass
                    
                    # Get reviews count (simplified but robust)
                    reviews = 'N/A'
                    try:
                        # Try the most common working selectors
                        for selector in ['.F7nice .UY7F9', '.F7nice span:not([aria-hidden])', '.jALQTb']:
                            try:
                                elem = driver.find_element(By.CSS_SELECTOR, selector)
                                text = elem.text.strip()
                                if '(' in text or 'review' in text.lower() or 'avis' in text.lower():
                                    match = re.search(r'(\d+)', text)
                                    if match:
                                        reviews = match.group(1)
                                        break
                            except:
                                continue

                        # Aria-label fallback (this was the key working part!)
                        if reviews == 'N/A':
                            for elem in driver.find_elements(By.CSS_SELECTOR, '.F7nice *'):
                                aria_label = elem.get_attribute('aria-label') or ''
                                if 'review' in aria_label.lower() or 'avis' in aria_label.lower():
                                    match = re.search(r'(\d+)', aria_label)
                                    if match:
                                        reviews = match.group(1)
                                        break
                    except:
                        pass
                    
                    print(f"  → {name}: {address}, {phone}, {website}")
                    
                    # Add to results
                    businesses.append({
                        'Name': name,
                        'Address': address, 
                        'Rating': rating,
                        'Reviews': reviews,
                        'Phone': phone,
                        'Website': website
                    })
                    
                except Exception as e:
                    print(f"  → Failed to process: {e}")
                    continue
                    
            except Exception as e:
                print(f"Error on business {i+1}: {e}")
                continue
        
        print(f"Extracted {len(businesses)} businesses")
    
    except Exception as e:
        print(f"Error: {e}")

    finally:
        # Save to Excel
        if not save_path.endswith('.xlsx'):
            filename = f"{query}_{location.replace(',', '_').replace(' ', '_')}_results.xlsx"
            save_path = os.path.join(save_path, filename)
        
        pd.DataFrame(businesses).to_excel(save_path, index=False)
        print(f"Results saved to: {save_path}")
        driver.quit()