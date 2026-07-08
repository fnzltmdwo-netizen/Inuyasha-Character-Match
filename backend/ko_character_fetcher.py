import os
import re
import csv
import requests

API_URL = "https://inuyasha.fandom.com/ko/api.php"
CATEGORY = "분류:이누야샤의 등장인물"
LIMIT = 80

OUTPUT_CSV = "character_seed_80.csv"
IMAGE_DIR = "images"

os.makedirs(IMAGE_DIR, exist_ok=True)


def safe_filename(name):
    name = re.sub(r"\(.*?\)", "", name)
    name = re.sub(r"[^가-힣a-zA-Z0-9_-]+", "_", name)
    return name.strip("_").lower() + ".jpg"


def clean_name(name):
    return re.sub(r"\s*\(.*?\)", "", name).strip()


def get_category_members():
    titles = []
    cmcontinue = None

    while True:
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": CATEGORY,
            "cmlimit": 50,
            "format": "json",
        }

        if cmcontinue:
            params["cmcontinue"] = cmcontinue

        res = requests.get(API_URL, params=params, timeout=20)
        res.raise_for_status()
        data = res.json()

        for item in data.get("query", {}).get("categorymembers", []):
            title = item.get("title", "")

            if title.startswith(("분류:", "파일:", "틀:")):
                continue

            titles.append(title)

        cmcontinue = data.get("continue", {}).get("cmcontinue")
        if not cmcontinue:
            break

    return titles


def get_page_info(title):
    params = {
        "action": "query",
        "titles": title,
        "prop": "pageimages|extracts",
        "pithumbsize": 700,
        "exintro": 1,
        "explaintext": 1,
        "format": "json",
    }

    res = requests.get(API_URL, params=params, timeout=20)
    res.raise_for_status()
    data = res.json()

    page = next(iter(data["query"]["pages"].values()))
    image_url = page.get("thumbnail", {}).get("source", "")
    description = page.get("extract", "").replace("\n", " ").strip()

    return image_url, description


def download_image(url, filename):
    path = os.path.join(IMAGE_DIR, filename)

    res = requests.get(url, timeout=30)
    res.raise_for_status()

    with open(path, "wb") as f:
        f.write(res.content)

    return path.replace("\\", "/")


def main():
    titles = get_category_members()
    print(f"후보 {len(titles)}개 발견")

    rows = []

    for title in titles:
        if len(rows) >= LIMIT:
            break

        try:
            image_url, description = get_page_info(title)

            if not image_url:
                print(f"이미지 없음: {title}")
                continue

            name = clean_name(title)
            filename = safe_filename(name)
            image_path = download_image(image_url, filename)

            rows.append({
                "name": name,
                "english_name": title,
                "description": description[:180] if description else f"{name} 캐릭터",
                "image_url": image_path,
            })

            print(f"완료 {len(rows)}/{LIMIT}: {name}")

        except Exception as e:
            print(f"실패: {title} / {e}")

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["name", "english_name", "description", "image_url"]
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n완료! {OUTPUT_CSV} 생성 / 총 {len(rows)}명")


if __name__ == "__main__":
    main()