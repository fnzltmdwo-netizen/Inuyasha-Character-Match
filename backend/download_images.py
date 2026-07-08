import os
import requests
from PIL import Image
from io import BytesIO

API_URL = "https://inuyasha.fandom.com/api.php"
SAVE_DIR = "images"
HEADERS = {"User-Agent": "Mozilla/5.0"}

CHARACTERS = [
    ("이누야샤", "Inuyasha", "inuyasha"),
    ("셋쇼마루", "Sesshomaru", "sesshomaru"),
    ("가영", "Kagome Higurashi", "kagome"),
    ("키쿄우", "Kikyo", "kikyo"),
    ("산고", "Sango", "sango"),
    ("미로쿠", "Miroku", "miroku"),
    ("싯포", "Shippo", "shippo"),
    ("나라쿠", "Naraku", "naraku"),
    ("코우가", "Koga", "koga"),
    ("카구라", "Kagura", "kagura"),
    ("칸나", "Kanna", "kanna"),
    ("링", "Rin", "rin"),
    ("쟈켄", "Jaken", "jaken"),
    ("묘가", "Myoga", "myoga"),
    ("코하쿠", "Kohaku", "kohaku"),
    ("토토사이", "Totosai", "totosai"),
    ("하쿠도시", "Hakudoshi", "hakudoshi"),
    ("반코츠", "Bankotsu", "bankotsu"),
    ("쟈코츠", "Jakotsu", "jakotsu"),
    ("렌코츠", "Renkotsu", "renkotsu"),
    ("스이코츠", "Suikotsu", "suikotsu"),
    ("긴코츠", "Ginkotsu", "ginkotsu"),
    ("무코츠", "Mukotsu", "mukotsu"),
    ("아야메", "Ayame", "ayame"),
    ("호조", "Hojo", "hojo"),
    ("츠바키", "Tsubaki", "tsubaki"),
    ("무소", "Muso", "muso"),
    ("히토미코", "Hitomiko", "hitomiko"),
    ("사라공주", "Princess Sara", "princess_sara"),
    ("이자요이", "Izayoi", "izayoi"),
    ("이누노타이쇼", "Toga", "toga"),
    ("소타", "Sota Higurashi", "sota"),
    ("카에데", "Kaede", "kaede"),
    ("부요", "Buyo", "buyo"),
    ("키라라", "Kirara", "kirara"),
]

def get_fandom_image(title):
    params = {
        "action": "query",
        "titles": title,
        "prop": "pageimages",
        "format": "json",
        "pithumbsize": 800,
        "redirects": 1,
    }

    r = requests.get(API_URL, params=params, headers=HEADERS, timeout=20)
    r.raise_for_status()

    pages = r.json().get("query", {}).get("pages", {})
    for page in pages.values():
        thumb = page.get("thumbnail", {})
        if thumb.get("source"):
            return thumb["source"]

    return ""

def download_image(url, filename):
    os.makedirs(SAVE_DIR, exist_ok=True)

    path = os.path.join(SAVE_DIR, filename)

    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()

    img = Image.open(BytesIO(r.content)).convert("RGBA")
    img.save(path, format="PNG")

    return path

def main():
    success = []
    failed = []

    for idx, (kor, eng, slug) in enumerate(CHARACTERS, start=1):
        print(f"\n[{idx}/{len(CHARACTERS)}] {kor} / {eng}")

        try:
            image_url = get_fandom_image(eng)

            if not image_url:
                print("❌ 이미지 없음")
                failed.append((kor, eng))
                continue

            path = download_image(image_url, f"{slug}.png")
            print("✅ 저장:", path)
            success.append((kor, eng))

        except Exception as e:
            print("❌ 실패:", e)
            failed.append((kor, eng))

    print("\n완료!")
    print("성공:", len(success))
    print("실패:", len(failed))

    if failed:
        print("\n실패 목록:")
        for kor, eng in failed:
            print("-", kor, "/", eng)

if __name__ == "__main__":
    main()