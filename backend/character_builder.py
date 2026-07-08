import os
import json
import re
import time
import base64
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

IMAGE_DIR = "images"
OUTPUT_PATH = "inuyasha_ai.csv"

def image_to_base64(path):
    with open(path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    return f"data:image/png;base64,{encoded}"

def extract_json(text):
    try:
        return json.loads(text)
    except Exception:
        match = re.search(r"\{[\s\S]*\}", str(text))
        if match:
            return json.loads(match.group(0))
    return {}

def analyze_character(kor, eng, image_path):
    image_base64 = image_to_base64(image_path)

    prompt = f"""
너는 이누야샤 등장인물 닮은꼴 테스트용 캐릭터 얼굴 DB를 만드는 AI야.

캐릭터:
한국명: {kor}
영문명: {eng}

첨부된 캐릭터 이미지를 보고 얼굴 생김새만 분석해.
성별, 나이, 성격, 작품 설정은 분석하지 마.
오직 얼굴형, 눈, 눈썹, 코, 입, 턱, 머리, 전체 인상만 봐.

반드시 아래 JSON 형식만 출력해.

{{
  "description": "외형 한 줄 설명",
  "face_shape": "아래 face_shape 목록에서 1~2개만 선택",
  "eyes": "아래 eyes 목록에서 1~3개만 선택",
  "eyebrows": "아래 eyebrows 목록에서 1~2개만 선택",
  "nose": "아래 nose 목록에서 1~2개만 선택",
  "mouth": "아래 mouth 목록에서 1~2개만 선택",
  "jaw": "아래 jaw 목록에서 1~2개만 선택",
  "hair": "아래 hair 목록에서 1~3개만 선택",
  "impression": "아래 impression 목록에서 1~2개만 선택",
  "face_tags": "선택한 얼굴 특징을 쉼표로 구분",
  "keywords": "대표 얼굴 키워드 3~5개를 쉼표로 구분"
}}

반드시 아래 단어만 사용해.

face_shape:
긴얼굴, 둥근얼굴, 계란형, 각진얼굴, 역삼각형, 짧은얼굴, 갸름한얼굴

eyes:
큰눈, 작은눈, 날카로운눈, 처진눈, 동그란눈, 가는눈, 무쌍, 쌍꺼풀, 눈꼬리올라감, 눈꼬리처짐

eyebrows:
굵은눈썹, 가는눈썹, 일자눈썹, 아치형눈썹, 진한눈썹, 옅은눈썹

nose:
큰코, 작은코, 높은코, 낮은코, 오똑한코, 둥근코

mouth:
큰입, 작은입, 얇은입술, 두꺼운입술, 미소형입, 무표정입

jaw:
각진턱, 갸름한턱, 둥근턱, 짧은턱, 긴턱

hair:
장발, 단발, 숏컷, 앞머리, 가르마, 곱슬, 직모, 묶음머리, 풍성한머리

impression:
강한인상, 부드러운인상, 차가운인상, 귀여운인상, 성숙한인상, 신비로운인상, 날카로운인상

규칙:
- 각 값은 반드시 목록에 있는 단어만 사용
- 여러 개 선택할 때는 쉼표로 구분
- 설명(description)만 자연어 허용
- 나머지 항목은 자유 서술 금지
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "너는 애니 캐릭터 얼굴 특징 DB 제작자야. 반드시 JSON만 출력해."
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_base64}},
                ],
            },
        ],
        temperature=0.1,
    )

    return extract_json(response.choices[0].message.content)

def main():
    if not os.getenv("OPENAI_API_KEY"):
        print("OPENAI_API_KEY 없음! .env 확인")
        return

    rows = []

    image_files = sorted([
        f for f in os.listdir(IMAGE_DIR)
        if f.lower().endswith((".png", ".jpg", ".jpeg"))
    ])

    print(f"총 이미지 수: {len(image_files)}")

    for idx, filename in enumerate(image_files, start=1):

        image_path = os.path.join(IMAGE_DIR, filename)

        name = os.path.splitext(filename)[0]

        print(f"[{idx}/{len(image_files)}] {name} 분석 중...")

        profile = analyze_character(
            kor=name,
            eng=name,
            image_path=image_path,
        )

        rows.append({
            "name": name,
            "english_name": name,
            "description": profile.get("description", ""),
            "face_shape": profile.get("face_shape", ""),
            "eyes": profile.get("eyes", ""),
            "eyebrows": profile.get("eyebrows", ""),
            "nose": profile.get("nose", ""),
            "mouth": profile.get("mouth", ""),
            "jaw": profile.get("jaw", ""),
            "hair": profile.get("hair", ""),
            "impression": profile.get("impression", ""),
            "face_tags": profile.get("face_tags", ""),
            "keywords": profile.get("keywords", ""),
            "image_url": image_path.replace("\\", "/"),
        })

        pd.DataFrame(rows).to_csv(
            OUTPUT_PATH,
            index=False,
            encoding="utf-8-sig",
        )

        print("저장:", name)

        time.sleep(0.2)

    print("\n완료!")
    print("생성 파일:", OUTPUT_PATH)
    print("총 캐릭터 수:", len(rows))

if __name__ == "__main__":
    main()