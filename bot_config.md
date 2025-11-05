# Facebook Messenger Bot - Plik Konfiguracyjny

Wersja: 1.0
Data: 2025-11-05

---

## 📋 SPIS TREŚCI

1. [Ustawienia Ogólne](#1-ustawienia-ogólne)
2. [Konfiguracja Konwersacji](#2-konfiguracja-konwersacji)
3. [Pobieranie Danych](#3-pobieranie-danych)
4. [Funkcje Bota](#4-funkcje-bota)
5. [Akcje i Automatyzacja](#5-akcje-i-automatyzacja)
6. [Export Danych](#6-export-danych)
7. [Zaawansowane](#7-zaawansowane)

---

## 1. USTAWIENIA OGÓLNE

### 1.1 Tryb Działania
```yaml
# Wybierz tryb działania bota:
# - "monitor"     : Tylko monitorowanie (odczyt)
# - "interactive" : Interakcje (wysyłanie wiadomości, reakcje)
# - "extract"     : Ekstrakcja danych historycznych
# - "auto"        : Automatyczne odpowiedzi

mode: "monitor"
```

### 1.2 Harmonogram
```yaml
# Czy bot ma działać stale czy w określonych godzinach?
schedule:
  enabled: false              # true = używaj harmonogramu, false = działaj zawsze
  active_hours:
    start: "08:00"            # Godzina rozpoczęcia (format 24h)
    end: "22:00"              # Godzina zakończenia
  active_days:                # Dni tygodnia (1=poniedziałek, 7=niedziela)
    - 1
    - 2
    - 3
    - 4
    - 5
```

### 1.3 Parametry Monitorowania
```yaml
polling_interval: 10          # Interwał sprawdzania (w sekundach)
wait_timeout: 10              # Timeout dla oczekiwania na elementy (w sekundach)
headless_mode: false          # true = przeglądarka ukryta, false = widoczna
```

---

## 2. KONFIGURACJA KONWERSACJI

### 2.1 Zakres Monitorowania
```yaml
# Wybierz zakres konwersacji do monitorowania:
# - "all"      : Wszystkie konwersacje
# - "specific" : Tylko wybrane konwersacje (definiowane poniżej)
# - "groups"   : Tylko konwersacje grupowe
# - "private"  : Tylko konwersacje prywatne

scope: "specific"
```

### 2.2 Określone Konwersacje
```yaml
# Lista konkretnych konwersacji do monitorowania
# Możesz użyć nazwy użytkownika, ID profilu lub numeru telefonu

specific_conversations:
  - name: "Rafał Szuwalski"           # Nazwa użytkownika na Messengerze
    priority: "high"                   # Priorytet: "high", "medium", "low"
    enabled: true                      # Czy włączone
    actions:                           # Akcje specyficzne dla tej konwersacji
      - "monitor"                      # Monitoruj wiadomości
      - "save_messages"                # Zapisuj historię
      - "notify"                       # Powiadomienia
    custom_function: null              # Nazwa funkcji niestandardowej (null = brak)

  - name: "Jan Kowalski"
    priority: "medium"
    enabled: false
    actions:
      - "monitor"
    custom_function: null

  # Dodaj więcej konwersacji według potrzeb:
  # - name: "Nazwa Użytkownika"
  #   priority: "medium"
  #   enabled: true
  #   actions: ["monitor"]
  #   custom_function: null
```

### 2.3 Filtry Konwersacji
```yaml
# Dodatkowe filtry dla konwersacji
filters:
  exclude_archived: true              # Wyklucz zarchiwizowane konwersacje
  exclude_muted: false                # Wyklucz wyciszone konwersacje
  only_unread: false                  # Tylko nieprzeczytane wiadomości
  min_message_count: 0                # Minilmalna liczba wiadomości w konwersacji
```

---

## 3. POBIERANIE DANYCH

### 3.1 Rodzaje Danych do Pobrania
```yaml
# Wybierz, jakie dane mają być pobierane
data_to_collect:
  messages:
    enabled: true                     # Pobieraj treść wiadomości
    include_reactions: true           # Reakcje na wiadomości
    include_timestamps: true          # Znaczniki czasu
    include_sender_info: true         # Informacje o nadawcy

  media:
    enabled: true                     # Pobieraj media
    types:                            # Typy mediów do pobrania
      - "images"                      # Zdjęcia
      - "videos"                      # Filmy
      - "audio"                       # Pliki audio
      - "documents"                   # Dokumenty
    download_files: false             # Czy pobierać pliki lokalnie

  metadata:
    enabled: true                     # Pobieraj metadane
    include_read_status: true         # Status przeczytania
    include_delivery_status: true     # Status dostarczenia
    include_conversation_info: true   # Info o konwersacji (nazwa, uczestnicy)

  user_info:
    enabled: false                    # Pobieraj informacje o użytkownikach
    fields:                           # Które pola
      - "name"
      - "profile_picture"
      - "status"
```

### 3.2 Zakres Czasowy
```yaml
# Określ zakres czasowy dla pobieranych danych
time_range:
  mode: "realtime"                    # "realtime", "historical", "custom"

  # Dla trybu "historical":
  start_date: null                    # Format: "2024-01-01" lub null
  end_date: null                      # Format: "2024-12-31" lub null

  # Dla trybu "custom":
  last_n_days: 30                     # Ostatnie N dni
  last_n_messages: 100                # Ostatnie N wiadomości
```

---

## 4. FUNKCJE BOTA

### 4.1 Monitoring
```yaml
monitoring:
  enabled: true                       # Włącz monitoring
  detect_new_messages: true           # Wykrywaj nowe wiadomości
  detect_typing: false                # Wykrywaj gdy ktoś pisze
  detect_online_status: false         # Wykrywaj status online
  track_message_count: true           # Śledź licznik wiadomości
```

### 4.2 Powiadomienia
```yaml
notifications:
  enabled: true                       # Włącz powiadomienia
  methods:                            # Metody powiadomień
    - "console"                       # Wyświetl w konsoli
    - "log_file"                      # Zapisz do pliku logów
    # - "email"                       # Email (wymaga konfiguracji)
    # - "webhook"                     # Webhook (wymaga URL)

  triggers:                           # Kiedy powiadamiać
    on_new_message: true              # Przy nowej wiadomości
    on_specific_keywords: false       # Przy słowach kluczowych
    on_mention: false                 # Przy wzmiance o tobie

  keywords:                           # Słowa kluczowe do monitorowania
    - "urgent"
    - "pilne"
    - "help"
```

### 4.3 Automatyczne Odpowiedzi
```yaml
auto_reply:
  enabled: false                      # Włącz auto-odpowiedzi (OSTROŻNIE!)
  delay: 5                            # Opóźnienie przed odpowiedzią (sekundy)

  rules:                              # Reguły odpowiedzi
    - trigger: "keyword"              # Typ: "keyword", "regex", "all"
      pattern: "hello|hi|cześć"       # Wzorzec dopasowania
      response: "Cześć! Jestem automatycznym botem."
      enabled: false

    - trigger: "all"
      pattern: null
      response: "Obecnie jestem niedostępny. Odezwę się później."
      enabled: false
```

### 4.4 Funkcje Niestandardowe
```yaml
# Definiuj niestandardowe funkcje dla konkretnych scenariuszy
custom_functions:
  # Przykład: funkcja zbierająca linki
  - name: "extract_links"
    enabled: false
    description: "Ekstrahuje wszystkie linki z wiadomości"
    target: "all"                     # "all" lub konkretna konwersacja

  # Przykład: funkcja zliczająca słowa
  - name: "count_words"
    enabled: false
    description: "Zlicza słowa w wiadomościach"
    target: "all"

  # Dodaj własne funkcje:
  # - name: "custom_function_name"
  #   enabled: false
  #   description: "Opis funkcji"
  #   target: "all"
```

---

## 5. AKCJE I AUTOMATYZACJA

### 5.1 Akcje na Nowych Wiadomościach
```yaml
on_new_message:
  actions:
    - type: "log"                     # Zaloguj wiadomość
      enabled: true

    - type: "mark_as_read"            # Oznacz jako przeczytane
      enabled: false                  # OSTROŻNIE! Nadawca zobaczy

    - type: "save_to_database"        # Zapisz do bazy danych
      enabled: false
      database_path: "./data/messages.db"

    - type: "save_to_file"            # Zapisz do pliku
      enabled: true
      file_path: "./data/messages.txt"
      format: "json"                  # "json", "txt", "csv"

    - type: "execute_script"          # Wykonaj skrypt
      enabled: false
      script_path: "./scripts/on_message.py"
```

### 5.2 Akcje Okresowe
```yaml
periodic_actions:
  - name: "cleanup_logs"
    enabled: false
    interval: 86400                   # Co ile sekund (86400 = 24h)
    action: "cleanup"
    parameters:
      keep_days: 7                    # Zachowaj logi z ostatnich N dni

  - name: "export_data"
    enabled: false
    interval: 3600                    # Co godzinę
    action: "export"
    parameters:
      format: "json"
      destination: "./exports/"
```

---

## 6. EXPORT DANYCH

### 6.1 Ustawienia Eksportu
```yaml
export:
  enabled: true                       # Włącz eksport danych
  auto_export: false                  # Automatyczny eksport
  export_interval: 3600               # Co ile sekund eksportować (auto_export=true)

  formats:                            # Formaty eksportu
    - "json"                          # JSON (strukturalny)
    - "csv"                           # CSV (tabela)
    - "txt"                           # TXT (prosty tekst)
    - "html"                          # HTML (czytelny w przeglądarce)

  destination: "./exports/"           # Katalog docelowy

  file_naming:
    pattern: "{date}_{conversation}_{format}"  # Wzorzec nazwy pliku
    # Dostępne zmienne: {date}, {time}, {conversation}, {format}, {timestamp}

  compression:
    enabled: false                    # Kompresja plików eksportu
    format: "zip"                     # "zip", "gz", "tar"
```

### 6.2 Zawartość Eksportu
```yaml
export_content:
  include_metadata: true              # Metadane konwersacji
  include_messages: true              # Treść wiadomości
  include_media_links: true           # Linki do mediów
  include_timestamps: true            # Znaczniki czasu
  include_participants: true          # Lista uczestników
  include_statistics: true            # Statystyki (liczba wiadomości, itp.)

  anonymize:                          # Anonimizacja danych
    enabled: false
    anonymize_names: false
    anonymize_phone_numbers: false
```

---

## 7. ZAAWANSOWANE

### 7.1 Debug i Logi
```yaml
debugging:
  enabled: true                       # Włącz tryb debug
  save_screenshots: true              # Zapisuj zrzuty ekranu
  save_page_source: true              # Zapisuj źródło strony
  screenshot_on_error: true           # Zrzut ekranu przy błędzie
  verbose_logging: false              # Szczegółowe logowanie

  log_level: "INFO"                   # "DEBUG", "INFO", "WARNING", "ERROR"
  log_file: "./logs/bot.log"          # Ścieżka do pliku logów
  debug_dir: "./debug_res/"           # Katalog na pliki debug
```

### 7.2 Bezpieczeństwo
```yaml
security:
  respect_rate_limits: true           # Szanuj limity Facebooka
  random_delays: true                 # Losowe opóźnienia (bardziej ludzkie)
  min_delay: 1                        # Minimalne opóźnienie (sekundy)
  max_delay: 3                        # Maksymalne opóźnienie (sekundy)

  max_actions_per_hour: 100           # Maksymalna liczba akcji/godzinę
  max_messages_per_conversation: 50   # Maks. wiadomości/konwersacja/sesja
```

### 7.3 Zarządzanie Sesją
```yaml
session:
  save_cookies: false                 # Zapisuj cookies (szybsze logowanie)
  cookies_file: "./config/cookies.pkl"
  session_timeout: 3600               # Timeout sesji (sekundy)
  auto_reconnect: true                # Automatyczne ponowne połączenie
  max_reconnect_attempts: 3           # Maksymalna liczba prób
```

### 7.4 Wydajność
```yaml
performance:
  max_memory_usage: 512               # Maksymalne zużycie pamięci (MB)
  cache_enabled: true                 # Włącz cache
  cache_size: 100                     # Wielkość cache (liczba elementów)
  parallel_processing: false          # Równoległe przetwarzanie (eksperymentalne)
```

---

## 📝 PRZYKŁADOWE KONFIGURACJE

### Przykład 1: Proste Monitorowanie Rafała Szuwalskiego
```yaml
mode: "monitor"
scope: "specific"
specific_conversations:
  - name: "Rafał Szuwalski"
    priority: "high"
    enabled: true
    actions: ["monitor", "save_messages", "notify"]

data_to_collect:
  messages:
    enabled: true
  media:
    enabled: false

notifications:
  enabled: true
  methods: ["console", "log_file"]
  triggers:
    on_new_message: true
```

### Przykład 2: Ekstrakcja Historii Wszystkich Konwersacji
```yaml
mode: "extract"
scope: "all"

data_to_collect:
  messages:
    enabled: true
    include_reactions: true
    include_timestamps: true
  media:
    enabled: true
    download_files: true

time_range:
  mode: "historical"
  last_n_days: 90

export:
  enabled: true
  formats: ["json", "html"]
  destination: "./exports/"
```

### Przykład 3: Bot z Auto-odpowiedziami (Tryb Wakacyjny)
```yaml
mode: "auto"
scope: "all"

auto_reply:
  enabled: true
  delay: 30
  rules:
    - trigger: "all"
      response: "Jestem poza domem do 15.11. Odezwę się po powrocie!"
      enabled: true

on_new_message:
  actions:
    - type: "log"
      enabled: true
    - type: "save_to_file"
      enabled: true
      file_path: "./data/messages_while_away.json"
```

---

## ⚠️ WAŻNE UWAGI

1. **Bezpieczeństwo**: Użycie automatyzacji może naruszać Regulamin Facebooka i prowadzić do zablokowania konta.

2. **Prywatność**: Szanuj prywatność innych użytkowników. Nie przechowuj danych bez zgody.

3. **Rate Limiting**: Facebook wykrywa boty. Używaj losowych opóźnień i szanuj limity.

4. **Testy**: Zawsze testuj konfigurację na koncie testowym przed użyciem na prawdziwym koncie.

5. **Backupy**: Regularnie twórz kopie zapasowe swoich danych i konfiguracji.

6. **Aktualizacje**: Facebook często zmienia interfejs. Bot może wymagać aktualizacji selektorów.

---

## 📞 POMOC I WSPARCIE

W razie problemów:
1. Sprawdź logi w katalogu `./logs/`
2. Sprawdź debug screenshots w `./debug_res/`
3. Włącz `verbose_logging: true` dla szczegółów
4. Sprawdź dokumentację w `README.md`

---

**Wersja konfiguracji**: 1.0
**Ostatnia aktualizacja**: 2025-11-05
**Kompatybilność**: Facebook Messenger Bot v1.0+
