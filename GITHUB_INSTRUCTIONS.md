# Instrukcje wrzucania na GitHub

## Krok 1: Przygotowanie repozytorium na GitHub

1. Wejdź na https://github.com
2. Zaloguj się na swoje konto
3. Kliknij przycisk "+" w prawym górnym rogu i wybierz "New repository"
4. Wypełnij formularz:
   - **Repository name**: `DXF2SVG`
   - **Description**: `Interaktywny konwerter plików DXF do SVG z GUI i konfigurowalnymi parametrami`
   - **Public**: Zaznacz (żeby było publiczne)
   - **Add a README file**: ODZNACZ (mamy już własny)
   - **Add .gitignore**: ODZNACZ (mamy już własny)
   - **Choose a license**: ODZNACZ (mamy już LICENSE)
5. Kliknij "Create repository"

## Krok 2: Inicjalizacja Git i push do GitHub

Otwórz terminal w katalogu projektu i wykonaj następujące polecenia:

```bash
# Inicjalizuj git (jeśli jeszcze nie jest)
git init

# Dodaj wszystkie pliki
git add .

# Zrób pierwszy commit
git commit -m "Initial commit: DXF2SVG Interactive Converter"

# Dodaj remote origin (ZMIEŃ NA SWOJĄ NAZWĘ UŻYTKOWNIKA!)
git remote add origin https://github.com/TWOJA_NAZWA_UZYTKOWNIKA/DXF2SVG.git

# Zmień główną gałąź na main (jeśli potrzeba)
git branch -M main

# Wypchnij na GitHub
git push -u origin main
```

## Krok 3: Ustawienia repozytorium na GitHub

Po wrzuceniu kodu:

1. Idź do swojego repozytorium na GitHub
2. Kliknij "Settings" (ustawienia)
3. W sekcji "General":
   - Ustaw "Default branch" na "main"
4. W sekcji "Pages" (jeśli chcesz GitHub Pages):
   - Możesz włączyć GitHub Pages dla dokumentacji

## Krok 4: Dodanie dodatkowych informacji

1. **Topics/Tags**: W głównej stronie repo kliknij koło zębate obok "About" i dodaj tagi:
   - `dxf-converter`
   - `svg-generator`  
   - `python-gui`
   - `tkinter`
   - `cad-tools`
   - `autocad`

2. **README**: GitHub automatycznie pokaże README_PL.md lub README.md

## Krok 5: Opcjonalne - Release

1. Idź do sekcji "Releases" w swoim repo
2. Kliknij "Create a new release"
3. Tag: `v1.0.0`
4. Title: `DXF2SVG v1.0.0 - Pierwsza stabilna wersja`
5. Opis w języku polskim opisujący funkcjonalności

## Gotowe pliki w projekcie:

✅ README_PL.md - Polska dokumentacja
✅ README.md - Angielska dokumentacja  
✅ LICENSE - Licencja MIT
✅ .gitignore - Ignorowanie niepotrzebnych plików
✅ requirements.txt - Zależności Python
✅ CHANGELOG.md - Historia zmian
✅ Uporządkowana struktura folderów src/

## Polecenia do skopiowania (zastąp TWOJA_NAZWA_UZYTKOWNIKA):

```bash
git init
git add .
git commit -m "Initial commit: DXF2SVG Interactive Converter"
git remote add origin https://github.com/TWOJA_NAZWA_UZYTKOWNIKA/DXF2SVG.git
git branch -M main
git push -u origin main
```

Po wykonaniu tych kroków Twój projekt będzie dostępny publicznie na GitHubie!
