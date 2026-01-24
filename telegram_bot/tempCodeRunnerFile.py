

# ================= CONFIG =================
DATA_FILE = "users.json"
AFFILIATE_ID = "bh7162"

BITLY_TOKENS = ["ea039af98086dc4ee7998b9f4473aa9465d8046d"]

# ================= HELPERS =================
def load_users():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_users(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def extract_links(text: str) -> list:
    return re.findall(r'https?://[^\s]+', text)
