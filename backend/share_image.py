from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from fastapi.responses import Response


def get_font(size):
    try:
        return ImageFont.truetype("malgun.ttf", size)
    except Exception:
        try:
            return ImageFont.truetype("arial.ttf", size)
        except Exception:
            return ImageFont.load_default()


def make_share_image(name="나", r1="", r2="", r3=""):
    W, H = 1200, 630

    img = Image.new("RGB", (W, H), "#fff7ea")
    draw = ImageDraw.Draw(img)

    title_font = get_font(56)
    rank_font = get_font(42)
    sub_font = get_font(28)

    draw.rectangle((0, 0, W, H), fill="#fff7ea")
    draw.rectangle((0, 520, W, H), fill="#b83243")

    draw.text((70, 55), f"🎉 {name}님의 이누야샤 닮은꼴 결과!", fill="#3b140f", font=title_font)

    cards = [
        ("🥇 1위", r1, "#d9b35b"),
        ("🥈 2위", r2, "#b7bec8"),
        ("🥉 3위", r3, "#c1773f"),
    ]

    x_positions = [70, 430, 790]

    for i, (rank, char_name, color) in enumerate(cards):
        x = x_positions[i]

        draw.rounded_rectangle(
            (x, 165, x + 310, 480),
            radius=28,
            fill="#ffffff",
            outline=color,
            width=5,
        )

        draw.rounded_rectangle(
            (x, 165, x + 310, 235),
            radius=28,
            fill=color,
        )

        draw.text((x + 95, 182), rank, fill="white", font=sub_font)
        draw.text((x + 75, 300), char_name or "-", fill="#3b140f", font=rank_font)

    draw.text((70, 545), "이누야샤 닮은꼴 테스트", fill="white", font=sub_font)
    draw.text((760, 545), "나도 테스트하기 👇", fill="white", font=sub_font)

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    return Response(content=buffer.getvalue(), media_type="image/png")