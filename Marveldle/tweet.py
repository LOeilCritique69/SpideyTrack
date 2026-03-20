from playwright.sync_api import sync_playwright
import os
import json
import time
import datetime

URL          = "https://marveldle.com/character/audiovisual/guess"
GUESS_PREFIX = "Spider-Ma"
IMAGES_DIR   = "marveldle/images"
RESULTS_FILE = "marveldle/results.json"
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
    today_day = 56

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
    exit()

# ════════════════════════════════════════════════════════════════
# 5. JOUER avec Playwright
# ════════════════════════════════════════════════════════════════
os.makedirs(IMAGES_DIR, exist_ok=True)

# Chemin physique pour sauvegarder le screenshot
screenshot_path = f"marveldle/images/day_{today_day:03}.png"
# Chemin stocké dans results.json — relatif à marveldle.html
shot_for_html   = f"marveldle/images/day_{today_day:03}.png"

if os.path.exists(screenshot_path):
    print(f"⚠️  Screenshot {screenshot_path} existe déjà — suppression avant nouveau screenshot.")
    os.remove(screenshot_path)

with sync_playwright() as p:
    is_ci   = os.environ.get('CI') == 'true'
    browser = p.chromium.launch(
        headless=is_ci,
        args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-blink-features=AutomationControlled']
    )
    context = browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        viewport={"width": 1280, "height": 800},
    )
    page = context.new_page()
    page.goto(URL, wait_until="networkidle")

    # Attendre l'input
    page.wait_for_selector("input[placeholder=\"Guess today's character\"]", timeout=15000)
    time.sleep(1)

    # Taper lettre par lettre (simulation humaine)
    page.click("input[placeholder=\"Guess today's character\"]")
    page.type("input[placeholder=\"Guess today's character\"]", GUESS_PREFIX, delay=80)
    time.sleep(1.5)

    # Attendre le dropdown Spider-Man
    page.wait_for_selector("span.option-name:has-text('Spider-Man')", timeout=10000)
    page.click("span.option-name:has-text('Spider-Man')")
    time.sleep(0.5)
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
    context.close()
    browser.close()

# ════════════════════════════════════════════════════════════════
# 6. ÉCRIRE dans results.json
# ════════════════════════════════════════════════════════════════
results[str(today_day)] = {
    "date":       today_iso,
    "result":     is_spiderman,
    "screenshot": shot_for_html
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