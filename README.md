uvicorn api:app --reload --host 0.0.0.0 --port 8000


# Bot do monitorowania Messenger (Selenium)

## Opis
Ten projekt tworzy bota do monitorowania wiadomości na Messengerze przy użyciu Selenium.
**UWAGA: Takie podejście może łamać Zasady korzystania z Facebooka i może prowadzić do zbanowania konta.**

## Wymagania
- Python 3.x
- pip
- ChromeDriver (lub inny WebDriver)

## Instalacja
1. Sklonuj repozytorium.
2. Utwórz i aktywuj wirtualne środowisko Pythona.
3. Zainstaluj zależności: `pip install -r requirements.txt`
4. Skonfiguruj plik `.env` z danymi logowania.
5. Upewnij się, że WebDriver (np. chromedriver) jest dostępny w PATH lub w katalogu `drivers/`.
6. Uruchom `python main.py`.

## Struktura projektu
- `main.py`: Główny punkt wejścia.
- `config/settings.py`: Ustawienia projektu.
- `src/facebook_bot.py`: Logika logowania i interakcji z Facebookiem.
- `src/messenger_monitor.py`: Logika monitorowania wiadomości.
- `src/utils.py`: Pomocnicze funkcje.
- `tests/`: Testy (opcjonalne).
- `logs/`: Logi działania bota.
