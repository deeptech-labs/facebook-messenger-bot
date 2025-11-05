#src/utils.py
"""
Pomocnicze funkcje.
"""
import time
import logging
import os
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from config import settings


def setup_logging():
    """Ustawia podstawowe logowanie do pliku i konsoli."""
    log_file = os.path.join(settings.LOG_DIR, "bot.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )


def wait_for_element_and_click(driver, locator, timeout=10, retry_count=3):
    """
    Czeka na element i próbuje go kliknąć z obsługą przeszkód.
    
    Args:
        driver: Instancja WebDriver
        locator: Tuple (By.XXX, "selector")
        timeout: Maksymalny czas oczekiwania
        retry_count: Liczba prób kliknięcia
        
    Returns:
        element lub None
    """
    for attempt in range(retry_count):
        try:
            element = WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable(locator)
            )
            
            # Przewiń do elementu
            driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(0.5)
            
            # Spróbuj kliknąć normalnie
            element.click()
            return element
            
        except ElementClickInterceptedException:
            print(f"Element przesłonięty, próba {attempt + 1}/{retry_count}")
            
            # Próba kliknięcia przez JavaScript jako fallback
            try:
                element = driver.find_element(*locator)
                driver.execute_script("arguments[0].click();", element)
                print(f"✓ Kliknięto element przez JavaScript")
                return element
            except Exception as js_error:
                print(f"✗ JS click też nie zadziałał: {js_error}")
                
            if attempt < retry_count - 1:
                time.sleep(1)
            else:
                print(f"✗ Nie udało się kliknąć elementu po {retry_count} próbach: {locator}")
                raise
                
        except TimeoutException:
            print(f"✗ Timeout: Nie można kliknąć elementu: {locator}")
            return None
        except Exception as e:
            print(f"✗ Nieoczekiwany błąd podczas klikania: {e}")
            if attempt < retry_count - 1:
                time.sleep(1)
            else:
                raise
    
    return None



def wait_for_element_and_send_keys(driver, locator, text, timeout=10):
    """
    Czeka na element i wpisuje tekst.
    
    Args:
        driver: Instancja WebDriver
        locator: Tuple (By.XXX, "selector")
        text: Tekst do wpisania
        timeout: Maksymalny czas oczekiwania
        
    Returns:
        element lub None
    """
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located(locator)
        )
        element.clear()
        element.send_keys(text)
        return element
    except TimeoutException:
        print(f"✗ Nie można wpisać tekstu do elementu: {locator}")
        return None
    except Exception as e:
        print(f"✗ Błąd podczas wpisywania tekstu: {e}")
        return None


def wait_for_element_presence(driver, locator, timeout=10):
    """
    Czeka na pojawienie się elementu.
    
    Args:
        driver: Instancja WebDriver
        locator: Tuple (By.XXX, "selector")
        timeout: Maksymalny czas oczekiwania
        
    Returns:
        element lub None
    """
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located(locator)
        )
        return element
    except TimeoutException:
        print(f"✗ Element nie pojawił się: {locator}")
        return None
    except Exception as e:
        print(f"✗ Błąd podczas oczekiwania na element: {e}")
        return None


def handle_cookie_popup(driver, timeout=10):
    """
    Obsługuje popup z cookies na Facebooku - ODMAWIA opcjonalnych cookies.
    
    Args:
        driver: Instancja WebDriver
        timeout: Maksymalny czas oczekiwania na popup
        
    Returns:
        bool: True jeśli popup został obsłużony, False w przeciwnym razie
    """
    try:
        print("🍪 Sprawdzam popup cookies...")
        
        # Zwiększony timeout i bardziej agresywne wyszukiwanie
        time.sleep(2)  # Daj czas na pełne załadowanie popupu
        
        # PRIORYTET 1: Szukaj po dokładnym tekście "Decline optional cookies"
        decline_selectors = [
            # Najbardziej specyficzne - button zawierający dokładny tekst
            (By.XPATH, "//button[contains(., 'Decline optional cookies')]"),
            (By.XPATH, "//button[.//text()[contains(., 'Decline optional cookies')]]"),
            
            # Przez div z data-testid (często używane przez FB)
            (By.XPATH, "//div[@role='button' and contains(., 'Decline optional cookies')]"),
            (By.CSS_SELECTOR, "[data-testid*='cookie'][data-testid*='decline']"),
            
            # Przez aria-label
            (By.XPATH, "//button[@aria-label='Decline optional cookies']"),
            (By.XPATH, "//div[@aria-label='Decline optional cookies']"),
            
            # Przez klasę i tekst
            (By.XPATH, "//button[contains(@class, 'x1i10hfl') and contains(., 'Decline')]"),
            
            # Szukanie po strukturze - button wewnątrz dialog z tekstem Decline
            (By.XPATH, "//div[@role='dialog']//button[contains(., 'Decline')]"),
            
            # Najbardziej ogólne - jakikolwiek klikalny element z Decline
            (By.XPATH, "//*[contains(text(), 'Decline optional cookies')]"),
            
            # Polski
            (By.XPATH, "//button[contains(., 'Odrzuć opcjonalne pliki cookie')]"),
        ]
        
        for i, selector in enumerate(decline_selectors):
            try:
                print(f"   🔍 Próba {i+1}/{len(decline_selectors)}: {selector[1][:60]}...")
                
                # Znajdź element
                button = WebDriverWait(driver, timeout).until(
                    EC.presence_of_element_located(selector)
                )
                
                print(f"   ✓ Znaleziono element!")
                
                # Upewnij się że element jest widoczny
                driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", button)
                time.sleep(1)
                
                # Sprawdź czy element jest interaktywny
                print(f"   📍 Element tag: {button.tag_name}, Text: {button.text[:50]}")
                
                # Próba 1: Normalny click
                try:
                    WebDriverWait(driver, 5).until(EC.element_to_be_clickable(selector))
                    button.click()
                    print("   ✓ Kliknięto (normalny click)")
                    time.sleep(2)
                    
                    # Sprawdź czy popup zniknął
                    try:
                        WebDriverWait(driver, 3).until_not(
                            EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Allow the use of cookies')]"))
                        )
                        print("✓ Popup cookies został zamknięty!")
                        return True
                    except:
                        print("   ℹ Popup może być jeszcze widoczny, sprawdzam...")
                        pass
                    
                    return True
                    
                except ElementClickInterceptedException:
                    print("   ⚠ Element przesłonięty, próbuję JavaScript...")
                    pass
                except Exception as e:
                    print(f"   ⚠ Normalny click nie zadziałał: {e}")
                    pass
                
                # Próba 2: JavaScript click
                try:
                    driver.execute_script("arguments[0].click();", button)
                    print("   ✓ Kliknięto (JavaScript)")
                    time.sleep(2)
                    return True
                except Exception as e:
                    print(f"   ✗ JavaScript click nie zadziałał: {e}")
                
                # Próba 3: Actions
                try:
                    from selenium.webdriver.common.action_chains import ActionChains
                    actions = ActionChains(driver)
                    actions.move_to_element(button).click().perform()
                    print("   ✓ Kliknięto (Actions)")
                    time.sleep(2)
                    return True
                except Exception as e:
                    print(f"   ✗ Actions click nie zadziałał: {e}")
                
            except TimeoutException:
                continue
            except Exception as e:
                print(f"   ✗ Błąd: {e}")
                continue
        
        # PLAN B: Znajdź wszystkie buttony i sprawdź ich tekst
        print("\n   🔄 Plan B: Szukam wszystkich buttonów w dialogu...")
        try:
            dialog = driver.find_element(By.XPATH, "//div[@role='dialog' and contains(., 'cookies')]")
            buttons = dialog.find_elements(By.TAG_NAME, "button")
            
            print(f"   📋 Znaleziono {len(buttons)} buttonów")
            
            for idx, btn in enumerate(buttons):
                try:
                    btn_text = btn.text.strip()
                    print(f"      Button {idx+1}: '{btn_text}'")
                    
                    if "decline" in btn_text.lower() or "odrzuć" in btn_text.lower():
                        print(f"   🎯 Znaleziono właściwy button: '{btn_text}'")
                        
                        # Przewiń i kliknij
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                        time.sleep(0.5)
                        
                        try:
                            btn.click()
                            print("   ✓ SUKCES! Kliknięto 'Decline' (Plan B)")
                            time.sleep(2)
                            return True
                        except:
                            driver.execute_script("arguments[0].click();", btn)
                            print("   ✓ SUKCES! Kliknięto 'Decline' przez JS (Plan B)")
                            time.sleep(2)
                            return True
                            
                except Exception as e:
                    continue
                    
        except Exception as e:
            print(f"   ✗ Plan B nie zadziałał: {e}")
        
        # OSTATECZNOŚĆ: Zapisz screenshot i HTML dla debugowania
        print("\n   ⚠ Nie udało się kliknąć przycisku, zapisuję debug info...")
        try:
            debug_dir = "/tmp/cookie_debug"
            os.makedirs(debug_dir, exist_ok=True)
            
            driver.save_screenshot(f"{debug_dir}/cookie_popup.png")
            with open(f"{debug_dir}/page_source.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            
            print(f"   💾 Debug zapisany w: {debug_dir}/")
        except:
            pass
        
        print("❌ Nie udało się obsłużyć popupu cookies!")
        return False
        
    except Exception as e:
        print(f"✗ Krytyczny błąd podczas obsługi cookies: {e}")
        import traceback
        traceback.print_exc()
        return False


def handle_decline_cookies(driver, timeout=5):
    """
    Alternatywna funkcja - odmawia opcjonalnych cookies (Essential only).
    
    Args:
        driver: Instancja WebDriver
        timeout: Maksymalny czas oczekiwania
        
    Returns:
        bool: True jeśli popup został obsłużony, False w przeciwnym razie
    """
    try:
        decline_selectors = [
            # Angielski
            (By.XPATH, "//button[contains(text(), 'Decline optional cookies')]"),
            (By.XPATH, "//button[contains(text(), 'Only essential')]"),
            # Polski
            (By.XPATH, "//button[contains(text(), 'Odrzuć opcjonalne pliki cookie')]"),
            (By.XPATH, "//button[contains(text(), 'Tylko niezbędne')]"),
        ]
        
        for selector in decline_selectors:
            try:
                button = WebDriverWait(driver, timeout).until(
                    EC.element_to_be_clickable(selector)
                )
                
                driver.execute_script("arguments[0].scrollIntoView(true);", button)
                time.sleep(0.3)
                
                try:
                    button.click()
                except ElementClickInterceptedException:
                    driver.execute_script("arguments[0].click();", button)
                
                print("✓ Opcjonalne cookies zostały odrzucone")
                time.sleep(1)
                return True
                
            except TimeoutException:
                continue
            except Exception as e:
                print(f"Próba kliknięcia decline nie powiodła się: {e}")
                continue
                
        print("ℹ Nie znaleziono przycisku decline cookies")
        return False
        
    except Exception as e:
        print(f"✗ Błąd podczas odrzucania cookies: {e}")
        return False


def wait_for_page_load(driver, timeout=10):
    """
    Czeka aż strona się w pełni załaduje.
    
    Args:
        driver: Instancja WebDriver
        timeout: Maksymalny czas oczekiwania
        
    Returns:
        bool: True jeśli strona się załadowała
    """
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        return True
    except TimeoutException:
        print(f"⚠ Timeout podczas oczekiwania na załadowanie strony")
        return False
    except Exception as e:
        print(f"✗ Błąd podczas sprawdzania załadowania strony: {e}")
        return False
