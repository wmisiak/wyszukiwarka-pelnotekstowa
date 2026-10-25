# Wyszukiwarka pełnotekstowa dokumentów

Projekt realizuje lokalną wyszukiwarkę dokumentów tekstowych z wykorzystaniem **Apache Beam**, **Python** i **PostgreSQL**. Indekser przetwarza pliki tekstowe do reprezentacji TF-IDF i zapisuje indeksy w bazie. Wyszukiwarka porównuje zapytanie z dokumentami za pomocą podobieństwa cosinusowego.

## 1. Wymagania

- Python 3.12 (lub zgodna wersja obsługiwana przez używaną wersję Apache Beam)
- Docker Desktop z Docker Compose
- `pip`
- Terminal uruchomiony w katalogu projektu

## 2. Struktura projektu

```text
wyszukiwarka-pelnotekstowa/
├── compose.yaml
├── init.sql
├── .env.example
├── .gitignore
├── requirements.txt
├── database.py
├── transforms.py
├── indexer.py
├── search.py
├── data/
│   └── *.txt
└── tests/
    ├── test_transform.py
    ├── test_search.py
    └── test_indexer.py
```

## 3. Przygotowanie środowiska Python

Aktywuj swoje środowisko wirtualne/Conda. Jeśli używasz Condy:

```bash
conda activate apache-beam
```

Zainstaluj zależności:

```bash
pip install -r requirements.txt
```

Jeśli w `requirements.txt` nie ma jeszcze tych pakietów, powinny się w nim znaleźć:

```text
apache-beam
psycopg[binary]
python-dotenv
```

## 4. Konfiguracja zmiennych środowiskowych

Utwórz lokalny plik `.env` na podstawie przykładowego pliku:

```bash
cp .env.example .env
```

Przykładowa zawartość `.env`:

```dotenv
DB_HOST=localhost
DB_PORT=5433
DB_NAME=indexer_db
DB_USER=a_user
DB_PASSWORD=pass123
```

Dostosuj wartości do swojej konfiguracji. Plik `.env` zawiera ustawienia lokalne i nie powinien być dodawany do repozytorium ani udostępnianego archiwum. Do projektu dołącz `.env.example` bez prawdziwych sekretów.

## 5. Uruchomienie bazy danych

Uruchom PostgreSQL w Dockerze:

```bash
docker compose up -d
```

Sprawdź status kontenera:

```bash
docker compose ps
```

Wyświetl logi PostgreSQL:

```bash
docker compose logs -f postgres
```

Po pierwszym uruchomieniu `init.sql` tworzy tabelę `files` i indeksy. Skrypt inicjalizacyjny jest automatycznie wykonywany przy tworzeniu nowego katalogu danych PostgreSQL; przy istniejącym wolumenie zmiany w `init.sql` nie są automatycznie uruchamiane ponownie.

Sprawdź tabelę:

```bash
docker compose exec postgres psql -U a_user -d indexer_db -c "\d files"
```

## 6. Dodawanie dokumentów

Umieść dokumenty tekstowe w katalogu `data/`. Indekser przetwarza pliki z rozszerzeniem `.txt` znajdujące się bezpośrednio w tym katalogu.

Przykład:

```text
data/
├── beam.txt
├── python.txt
├── search.txt
├── alice_in_wonderland.txt
├── dracula.txt
└── frankenstein.txt
```

Pliki powinny być zapisane w kodowaniu UTF-8.

## 7. Indeksowanie dokumentów

Uruchom indekser:

```bash
python indexer.py
```

Indekser:
1. wyszukuje pliki `.txt` w katalogu `data/`,
2. przypisuje dokumentom stabilne identyfikatory na podstawie ścieżek,
3. tokenizuje tekst i usuwa wybrane słowa (stop words),
4. oblicza częstości tokenów, DF, IDF i wagi TF-IDF,
5. zapisuje identyfikator, ścieżkę i słownik wag w PostgreSQL.

Ponowne uruchomienie indeksowania aktualizuje rekordy o tych samych identyfikatorach, zamiast tworzyć ich duplikaty.

### Sprawdzenie zapisanych dokumentów

Pokaż identyfikatory i ścieżki:

```bash
docker compose exec postgres psql -U a_user -d indexer_db -c "SELECT id, filename FROM files ORDER BY filename;"
```

Pokaż rozmiar indeksu i liczbę tokenów w każdym dokumencie:

```bash
docker compose exec postgres psql -U a_user -d indexer_db -c "SELECT filename, pg_size_pretty(pg_column_size(index_structure)::bigint) AS rozmiar_json, (SELECT COUNT(*) FROM jsonb_object_keys(index_structure)) AS liczba_tokenow FROM files ORDER BY pg_column_size(index_structure) DESC;"
```

Pokaż czytelny indeks jednego dokumentu:

```bash
docker compose exec postgres psql -U a_user -d indexer_db -c "SELECT filename, jsonb_pretty(index_structure) FROM files WHERE filename = 'data/dracula.txt';"
```

## 8. Wyszukiwanie

Wyszukiwarka przyjmuje zapytanie jako argument tekstowy:

```bash
python search.py "vampire blood horror"
```

Inne przykłady:

```bash
python search.py "monster creature experiment"
python search.py "alice rabbit wonderland"
python search.py "python programming"
python search.py "beam pipeline"
```

Wyniki zawierają pozycję w rankingu, ścieżkę dokumentu, ID i wynik podobieństwa cosinusowego. Wyniki są sortowane malejąco według podobieństwa. Wynik podobieństwa nie jest procentową oceną trafności.

Jeśli zapytanie zawiera wyłącznie pomijane słowa albo nie ma wspólnych tokenów z dokumentami, wyszukiwarka może nie zwrócić wyników.

## 9. Testy jednostkowe

Uruchom wszystkie testy:

```bash
python -m unittest discover -s tests -v
```

Testy obejmują logikę tokenizacji, usuwania stop words, obliczania częstości, TF-IDF i podobieństwa cosinusowego. Powinny działać niezależnie od kolejności uruchamiania.

## 10. Zatrzymanie bazy danych

Zatrzymaj kontener:

```bash
docker compose down
```

Ta komenda zachowuje wolumen bazy danych. **Nie używaj `docker compose down -v`, jeśli chcesz zachować zaindeksowane dokumenty**, ponieważ opcja `-v` usuwa także wolumen z danymi.

## 11. Jak działa TF-IDF?

- **TF (Term Frequency)** — częstość tokenu w dokumencie, w tym projekcie znormalizowana przez liczbę tokenów dokumentu po filtracji.
- **DF (Document Frequency)** — liczba dokumentów, w których występuje token.
- **IDF (Inverse Document Frequency)** — waga zależna od rzadkości tokenu w całym zbiorze.
- **TF-IDF** — iloczyn TF i IDF, używany jako waga tokenu w reprezentacji dokumentu.
- **Podobieństwo cosinusowe** — miara podobieństwa wektora zapytania i wektora dokumentu.

Projekt używa wygładzonego wzoru:

```text
IDF(t) = ln((N + 1) / (DF(t) + 1)) + 1
TF(t, d) = liczba_wystąpień_tokenu / liczba_wszystkich_tokenów_dokumentu
TF-IDF(t, d) = TF(t, d) * IDF(t)
```

## 12. Uwagi

- W obecnej wersji stop words są angielskie, a tokenizacja używa wzorca ASCII `a-z` i `0-9`. Jest to dostosowane do dołączonych anglojęzycznych tekstów; polskie znaki diakrytyczne wymagają zmiany tokenizacji.
- Indeks GIN na kolumnie JSONB może przyspieszać niektóre zapytania po kluczach JSONB, ale aktualna wyszukiwarka pobiera dokumenty z bazy i oblicza podobieństwo cosinusowe w Pythonie.
- Jeśli zmienisz sposób tokenizacji lub listę stop words, uruchom ponownie `python indexer.py`, aby przebudować indeksy.
