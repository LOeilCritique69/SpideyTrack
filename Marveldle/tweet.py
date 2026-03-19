from playwright.sync_api import sync_playwright
import os
import json
import time
import datetime

URL          = "https://marveldle.com/character/audiovisual/guess"
GUESS_PREFIX = "Spider-Ma"
IMAGES_DIR   = "images"
RESULTS_FILE = "results.json"
TODAY_FILE   = "last_run.txt"
DAY_FILE     = "day.txt"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)

today     = datetime.date.today()
today_iso = today.isoformat()

# ════════════════════════════════════════════════════════════════
# 1. VÉRIFIER via last_run.txt — déjà lancé aujourd'hui ?
# ════════════════════════════════════════════════════════════════
if os.path.exists(TODAY_FILE):
    with open(TODAY_FILE, "r") as f:
        if f.read().strip() == today_iso:
            print("✅ Script déjà lancé aujourd'hui. Rien à faire.")
            exit()

# ════════════════════════════════════════════════════════════════
# 2. LIRE le jour actuel depuis day.txt
# ════════════════════════════════════════════════════════════════
if os.path.exists(DAY_FILE):
    with open(DAY_FILE, "r") as f:
        today_day = int(f.read().strip())
else:
    today_day = 37  # valeur par défaut au premier lancement

print(f"🎯 Jour d'aujourd'hui : {today_day}")

# ════════════════════════════════════════════════════════════════
# 3. CHARGER results.json
# ════════════════════════════════════════════════════════════════
results = {}
if os.path.exists(RESULTS_FILE):
    with open(RESULTS_FILE, "r", encoding="utf-8") as f:
        raw = f.read().strip()
        if raw:
            results = json.loads(raw)

# ════════════════════════════════════════════════════════════════
# 4. VÉRIFIER que ce jour n'est pas déjà dans results.json
# ════════════════════════════════════════════════════════════════
if str(today_day) in results:
    print(f"⚠️  Jour {today_day} déjà présent dans results.json — doublon évité.")
    # Supprimer le screenshot si il a été créé par erreur
    shot_path = f"images/day_{today_day:03}.png"
    # On ne touche pas au screenshot existant, juste on ne rejoue pas
    exit()

# ════════════════════════════════════════════════════════════════
# 5. JOUER avec Playwright
# ════════════════════════════════════════════════════════════════
os.makedirs(IMAGES_DIR, exist_ok=True)
screenshot_path = f"images/day_{today_day:03}.png"

# Vérifier si le screenshot existe déjà (doublon fichier)
if os.path.exists(screenshot_path):
    print(f"⚠️  Screenshot {screenshot_path} existe déjà — suppression avant nouveau screenshot.")
    os.remove(screenshot_path)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page    = browser.new_page()
    page.goto(URL)

    page.fill("input[placeholder=\"Guess today's character\"]", GUESS_PREFIX)
    page.click("span.option-name:has-text('Spider-Man')")
    page.click("button.btn.btn-primary.search-button")

    page.wait_for_selector("div.guess-row.new")
    squares    = []
    start_time = time.time()
    while True:
        squares = page.query_selector_all("div.guess-row.new > div.similarity")
        if len(squares) == 7:
            break
        if time.time() - start_time > 10:
            print("⏱ Timeout — moins de 7 indices reçus")
            break
        time.sleep(0.2)

    print("⏳ Attente de 10 secondes (animation)...")
    time.sleep(10)

    square_info = []
    for sq in squares:
        cls   = sq.get_attribute("class")
        title = sq.get_attribute("title")
        square_info.append((title, cls))
        print(f"  · {title} → {cls}")

    is_spiderman = all("exact" in cls for _, cls in square_info)
    verdict = "✅ Spider-Man EST le perso du jour !" if is_spiderman else "❌ Spider-Man n'est PAS le perso du jour."
    print(verdict)

    page.screenshot(path=screenshot_path)
    print(f"📸 Screenshot : {screenshot_path}")
    browser.close()

# ════════════════════════════════════════════════════════════════
# 6. ÉCRIRE dans results.json (sans doublon)
# ════════════════════════════════════════════════════════════════
results[str(today_day)] = {
    "date":       today_iso,
    "result":     is_spiderman,
    "screenshot": screenshot_path
}

with open(RESULTS_FILE, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print(f"✅ results.json mis à jour (jour {today_day}).")

# ════════════════════════════════════════════════════════════════
# 7. INCRÉMENTER day.txt + marquer last_run.txt
# ════════════════════════════════════════════════════════════════
with open(DAY_FILE, "w") as f:
    f.write(str(today_day + 1))

with open(TODAY_FILE, "w") as f:
    f.write(today_iso)

print(f"📅 Prochain jour enregistré : {today_day + 1}")
print("🏁 Terminé.")
