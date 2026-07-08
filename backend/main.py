from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
import pandas as pd
import os
import json
import re

from matcher import find_top20

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI(title="Inuyasha Character Match API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

if os.path.exists("images"):
    app.mount("/images", StaticFiles(directory="images"), name="images")

CSV_PATH = "inuyasha_ai.csv"


class MatchRequest(BaseModel):
    image_base64: str


def extract_json(text):
    try:
        return json.loads(text)
    except Exception:
        pass

    match = re.search(r"\{[\s\S]*\}", str(text))
    if not match:
        raise ValueError("JSON을 찾을 수 없습니다.")

    return json.loads(match.group(0))


def load_characters():
    if not os.path.exists(CSV_PATH):
        return []

    df = pd.read_csv(CSV_PATH).fillna("")
    return df.to_dict(orient="records")


def make_image_url(image_path):
    if not image_path:
        return ""

    image_path = str(image_path).replace("\\", "/")

    if image_path.startswith("http"):
        return image_path

    if image_path.startswith("images/"):
        return "http://127.0.0.1:8000/" + image_path

    return image_path


def analyze_face_gpt(image_base64):
    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is missing")

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """
너는 이누야샤 닮은꼴 테스트용 얼굴 분석가야.
사진 속 인물의 신원, 성별, 나이, 직업은 절대 추측하지 마.
오직 얼굴 생김새와 인상 특징만 분석해.
반드시 JSON만 출력해.
"""
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """
사진 속 사람을 이누야샤 캐릭터와 매칭하기 좋게 얼굴 중심으로 분석해줘.

반드시 아래 JSON 형식만 출력해.

{
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
}

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
- 자유 서술 금지
- 성별 판단 금지
- 나이 추정 금지
- 신원 추측 금지
"""
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": image_base64}
                    }
                ]
            }
        ],
        temperature=0.1,
    )

    return extract_json(response.choices[0].message.content)


def final_select_gpt(image_base64, face_analysis, candidates):
    candidate_text = json.dumps(candidates, ensure_ascii=False, indent=2)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """
너는 이누야샤 등장인물 닮은꼴 최종 심사위원이야.
사진과 후보 캐릭터 목록을 보고 가장 얼굴이 닮은 Top3를 골라.
실제 사람의 신원, 성별, 나이는 절대 추측하지 마.
캐릭터의 성격, 역할, 작품 설정은 무시해.
오직 얼굴형, 눈, 눈썹, 코, 입, 턱, 머리, 전체 인상 기준으로만 판단해.
반드시 JSON만 출력해.
"""
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"""
사용자 얼굴 분석 결과:
{json.dumps(face_analysis, ensure_ascii=False)}

후보 캐릭터 목록:
{candidate_text}

위 후보 중 최종 Top3를 골라줘.

판단 순서:
1. 얼굴형이 비슷한가
2. 눈 크기와 눈매가 비슷한가
3. 눈썹, 코, 입, 턱이 비슷한가
4. 머리 모양과 전체 인상이 비슷한가
5. 단순히 분위기만 비슷한 캐릭터는 낮게 평가

아래 JSON 형식만 출력해.

{{
  "results": [
    {{
      "rank": 1,
      "name": "캐릭터명",
      "english_name": "영문명",
      "percent": 88,
      "reason": "얼굴형, 눈매, 코, 입, 턱, 헤어 기준으로 왜 닮았는지 짧고 자연스럽게 설명",
      "keywords": "키워드1,키워드2,키워드3"
    }}
  ]
}}

조건:
- 반드시 후보 목록 안에서만 골라.
- 성별은 고려하지 마.
- 나이와 캐릭터 설정도 고려하지 마.
- 얼굴형과 눈매를 가장 중요하게 봐.
- 닮지 않은 캐릭터를 억지로 고르지 마.
- 1위 percent는 84~92 사이.
- 2위 percent는 76~83 사이.
- 3위 percent는 68~75 사이.
- reason은 결과 카드에 들어갈 정도로 짧게.
"""
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": image_base64}
                    }
                ]
            }
        ],
        temperature=0.2,
    )

    parsed = extract_json(response.choices[0].message.content)
    return parsed.get("results", [])


def enrich_results(results, characters):
    enriched = []

    for item in results:
        name = str(item.get("name", "")).strip()

        ch = {}
        for c in characters:
            if str(c.get("name", "")).strip() == name:
                ch = c
                break

        item["english_name"] = item.get("english_name") or ch.get("english_name", "")
        item["description"] = ch.get("description", "")
        item["image_url"] = make_image_url(ch.get("image_url", ""))
        item["face_tags"] = ch.get("face_tags", "")
        item["keywords"] = item.get("keywords") or ch.get("keywords", "")

        enriched.append(item)

    return enriched


@app.get("/")
def root():
    characters = load_characters()

    return {
        "message": "Inuyasha Character Match API is running!",
        "status": "ok",
        "csv_exists": os.path.exists(CSV_PATH),
        "character_count": len(characters),
        "openai_ready": bool(os.getenv("OPENAI_API_KEY")),
    }


@app.get("/characters")
def characters():
    data = load_characters()
    return {
        "count": len(data),
        "characters": data
    }


@app.post("/match")
def match_character(req: MatchRequest):
    if not req.image_base64:
        raise HTTPException(status_code=400, detail="image_base64 is required")

    characters = load_characters()

    if not characters:
        raise HTTPException(status_code=500, detail="No characters found")

    try:
        face_analysis = analyze_face_gpt(req.image_base64)

        top20_rows = find_top20(face_analysis)

        candidates = []
        for row in top20_rows:
            item = dict(row)
            item["image_url"] = make_image_url(item.get("image_url", ""))
            candidates.append(item)

        results = final_select_gpt(
            image_base64=req.image_base64,
            face_analysis=face_analysis,
            candidates=candidates
        )

        results = enrich_results(results, characters)

        return {
            "status": "success",
            "face_analysis": face_analysis,
            "candidate_count": len(candidates),
            "results": results
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))