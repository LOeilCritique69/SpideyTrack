from playwright.sync_api import sync_playwright
import os
import json
import time
import datetime

URL = "https://marveldle.com/character/audiovisual/guess"

# ════════════════════════════════════════════════════════════════
# CONFIG — chaque perso a son propre dossier, day file, results
# ════════════════════════════════════════════════════════════════
CHARACTERS = [
    {
        "key":         "tom",
        "label":       "Tom Holland",
        "prefix":      "Spider-Ma",
        "option":      "Spider-Man",
        "images_dir":  "marveldle/images",
        "results_file":"marveldle/results.json",
        "day_file":    "day.txt",
    },
    {
        "key":         "andrew",
        "label":       "Andrew Garfield",
        "prefix":      "Spider-Man (R",
        "option":      "Spider-Man (Rageful Vigilante Spider-Man Universe)",
        "images_dir":  "marveldle/images_andrew",
        "results_file":"marveldle/results_andrew.json",
        "day_file":    "day-andrew.txt",
    },
    {
        "key":         "tobey",
        "label":       "Tobey Maguire",
        "prefix":      "Spider-Man (O",
        "option":      "Spider-Man (Organic Webbing Spider-Man Universe)",
        "images_dir":  "marveldle/images_tobey",
        "results_file":"marveldle/results_tobey.json",
        "day_file":    "day_tobey.txt",
    },
]

TODAY_FILE = "last_run.txt"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)

today     = datetime.date.today()
today_iso = today.isoformat()

# ════════════════════════════════════════════════════════════════
# 1. VÉRIFIER si déjà lancé aujourd'hui
# ════════════════════════════════════════════════════════════════
if os.path.exists(TODAY_FILE):
    with open(TODAY_FILE, "r") as f:
        if f.read().strip() == today_iso:
            print("✅ Script déjà lancé aujourd'hui. Rien à faire.")
            exit()

# ════════════════════════════════════════════════════════════════
# 2. JOUER chaque personnage
# ════════════════════════════════════════════════════════════════
is_ci = os.environ.get('CI') == 'true'

for char in CHARACTERS:
    print(f"\n{'═'*55}")
    print(f"  {char['label']}")
    print(f"{'═'*55}")

    # Lire le jour actuel pour ce perso
    if os.path.exists(char["day_file"]):
        with open(char["day_file"], "r") as f:
            today_day = int(f.read().strip())
    else:
        today_day = 1 if char["key"] != "tom" else 56

    print(f"  🎯 Jour : {today_day}")

    # Charger son results.json
    results = {}
    if os.path.exists(char["results_file"]):
        with open(char["results_file"], "r", encoding="utf-8") as f:
            raw = f.read().strip()
            if raw:
                results = json.loads(raw)

    # Vérifier doublon
    if str(today_day) in results:
        print(f"  ⚠️  Jour {today_day} déjà dans {char['results_file']} — skip.")
        continue

    # Créer le dossier images si besoin
    os.makedirs(char["images_dir"], exist_ok=True)
    shot_path = f"{char['images_dir']}/day_{today_day:03}.png"

    if os.path.exists(shot_path):
        os.remove(shot_path)

    # Lancer Playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=is_ci,
            args=['--no-sandbox', '--disable-setuid-sandbox',
                  '--disable-blink-features=AutomationControlled']
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

        page.wait_for_selector(
            "input[placeholder=\"Guess today's character\"]", timeout=15000
        )
        time.sleep(1)

        page.click("input[placeholder=\"Guess today's character\"]")
        page.type(
            "input[placeholder=\"Guess today's character\"]",
            char["prefix"], delay=80
        )
        time.sleep(1.5)

        option_selector = f"span.option-name:has-text('{char['option']}')"
        page.wait_for_selector(option_selector, timeout=10000)
        page.click(option_selector)
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
                print("  ⏱ Timeout")
                break
            time.sleep(0.2)

        print("  ⏳ Attente animation (10s)...")
        time.sleep(10)

        square_info = []
        for sq in squares:
            cls   = sq.get_attribute("class")
            title = sq.get_attribute("title")
            square_info.append((title, cls))
            print(f"    · {title} → {cls}")

        is_match = all("exact" in cls for _, cls in square_info)
        verdict = "✅ C'est lui !" if is_match else "❌ Pas lui."
        print(f"  {verdict}")

        page.screenshot(path=shot_path)
        print(f"  📸 {shot_path}")

        context.close()
        browser.close()

    # Sauvegarder dans le results.json de ce perso
    results[str(today_day)] = {
        "date":       today_iso,
        "result":     is_match,
        "screenshot": shot_path,
    }
    with open(char["results_file"], "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"  ✅ {char['results_file']} mis à jour.")

    # Incrémenter le jour de ce perso
    with open(char["day_file"], "w") as f:
        f.write(str(today_day + 1))
    print(f"  📅 Prochain jour {char['label']} : {today_day + 1}")

# ════════════════════════════════════════════════════════════════
# 3. MARQUER last_run.txt
# ════════════════════════════════════════════════════════════════
with open(TODAY_FILE, "w") as f:
    f.write(today_iso)

print("\n🏁 Terminé.")