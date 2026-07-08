import pandas as pd

df = pd.read_csv("inuyasha_ai.csv").fillna("")

WEIGHTS = {
    "face_shape": 10,
    "eyes": 10,
    "eyebrows": 5,
    "nose": 5,
    "mouth": 4,
    "jaw": 5,
    "hair": 4,
    "impression": 3,
}


def normalize(text):
    if pd.isna(text):
        return set()

    return {
        t.strip().lower()
        for t in str(text).replace("，", ",").split(",")
        if t.strip()
    }


def compare(user, character, weight):

    u = normalize(user)
    c = normalize(character)

    if not u or not c:
        return 0

    common = u & c

    if not common:
        return 0

    ratio = len(common) / max(len(u), len(c))

    return ratio * weight


def similarity(user, character):

    score = 0

    for feature, weight in WEIGHTS.items():

        score += compare(
            user.get(feature, ""),
            character.get(feature, ""),
            weight,
        )

    score += compare(
        user.get("face_tags", ""),
        character.get("face_tags", ""),
        8,
    )

    score += compare(
        user.get("keywords", ""),
        character.get("keywords", ""),
        5,
    )

    return score


def find_top20(user_profile):

    scores = []

    for _, row in df.iterrows():

        score = similarity(user_profile, row)

        scores.append((score, row))

    scores.sort(
        key=lambda x: x[0],
        reverse=True,
    )

    return [row for _, row in scores[:30]]