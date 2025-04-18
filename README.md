# Gra jak Familiada  - Gra Quizowa

## Opis Projektu

Familiada Online to wierna adaptacja popularnego teleturnieju, pozwalająca na rozgrywkę w trybie online z podziałem na role:
- **Administrator** - zarządza całą rozgrywką
- **Prowadzący** - moderuje grę
- **Gracze** - uczestniczą w rozgrywce

## Funkcjonalności

✅ **Tryb wieloosobowy** z podziałem na role  
✅ **3 etapy rozgrywki**  
✅ **System punktowy** z pulą rundy  
✅ **Panel administracyjny** z pełną kontrolą  
✅ **Baza pytań** w SQLite  

## Wymagania Techniczne

- Python 3.8+
- Flask 2.0+
- SQLite3

## Instalacja

1. Sklonuj repozytorium:
```bash
git clone https://github.com/Matasnet/Gra-Jak-Familiada.git  
```

2. Inicjalizacja bazy danyc:
python init_db.py

3. Uruchomienie serwera
python app.py

## Struktura projketu  
familiada/  
├── app.py            # Główna aplikacja Flask  
├── database.py       # Inicjalizacja bazy danych  
├── requirements.txt  # Zależności  
├── config.ini        # Konfiguracja (opcjonalnie)  
├── static/  
│   ├── style.css     # Style CSS  
│   └── script.js     # Wspólne funkcje JS  
└── templates/  
    ├── admin.html    # Panel administratora  
    ├── host.html     # Widok prowadzącego  
    ├── player.html   # Widok gracza  
    └── index.html    # Wybór roli  

## Jak grać ?  
Jeden gracz wciela się w administratora/admina on przydziela punkty, odsłania odpowiedzi, uruchamia gre, zmienia rundę, przyznaje ostrzeżenia za błędną odpowiedź etc.  
Drugi gracz (opcjonalnie) jest prowadzącym on widzi tylko ilość odpowiedzi oraz punkty za odpowiedź ale jej nie zna.  
W celu zabezpieczenia zabawy dostęp do panelu administratora i prowadzącego jest zabezpieczony hasłem (można je zmienić w pliku app.py)  
2 zespoły bądź 2 graczy widzi zakryte odpowiedzi, zgaduje hasła i śledzi swoje wyniki.
