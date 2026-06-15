#!/usr/bin/env python3
"""Generate a PPT-ready growth flywheel graphic for ZhengYuanfang."""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs" / "证元芳_PPT图示" / "证元芳_增长飞轮图_16x9_v3.png"
W, H = 2560, 1440


FONT_CANDIDATES = [
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/STHeiti Light.ttc",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/System/Library/Fonts/Supplemental/Songti.ttc",
]


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = FONT_CANDIDATES if bold else FONT_CANDIDATES[1:] + FONT_CANDIDATES[:1]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


F = {
    "title": font(62, True),
    "subtitle": font(29),
    "panel_header": font(27, True),
    "panel_num": font(34, True),
    "card_title": font(27, True),
    "body": font(21),
    "body_small": font(18),
    "metric": font(34, True),
    "metric_label": font(21, True),
    "wheel_title": font(34, True),
    "wheel_sub": font(21, True),
    "wheel_small": font(18),
    "section_header": font(28, True),
    "bottom_title": font(23, True),
    "bottom_body": font(19),
    "note": font(17),
}


COLORS = {
    "navy": "#061E4D",
    "blue": "#075BDC",
    "blue2": "#0A7DFF",
    "blue_light": "#EAF3FF",
    "green": "#079B49",
    "green2": "#18C166",
    "green_light": "#EBF9F1",
    "orange": "#FF6A00",
    "orange2": "#FF9A1F",
    "orange_light": "#FFF2E8",
    "purple": "#5B3AD8",
    "purple2": "#735CF0",
    "purple_light": "#F1EEFF",
    "gray": "#546179",
    "line": "#D5E1F2",
    "white": "#FFFFFF",
}


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def text_size(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.ImageFont) -> tuple[int, int]:
    if not text:
        return 0, 0
    box = draw.textbbox((0, 0), text, font=fnt)
    return box[2] - box[0], box[3] - box[1]


def draw_centered(
    draw: ImageDraw.ImageDraw,
    text: str,
    cx: int,
    y: int,
    fnt: ImageFont.ImageFont,
    fill: str,
) -> None:
    tw, _ = text_size(draw, text, fnt)
    draw.text((cx - tw / 2, y), text, font=fnt, fill=fill)


def rounded_rect(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int, int, int],
    radius: int,
    fill: str,
    outline: str | None = None,
    width: int = 1,
) -> None:
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def gradient_rounded_rect(
    base: Image.Image,
    xy: tuple[int, int, int, int],
    radius: int,
    left: str,
    right: str,
    outline: str | None = None,
    width: int = 1,
) -> None:
    x1, y1, x2, y2 = xy
    gw, gh = x2 - x1, y2 - y1
    c1 = hex_to_rgb(left)
    c2 = hex_to_rgb(right)
    grad = Image.new("RGBA", (gw, gh), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grad)
    for x in range(gw):
        t = x / max(1, gw - 1)
        c = tuple(round(c1[i] * (1 - t) + c2[i] * t) for i in range(3))
        gd.line((x, 0, x, gh), fill=c + (255,))
    mask = Image.new("L", (gw, gh), 0)
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle((0, 0, gw, gh), radius=radius, fill=255)
    base.paste(grad, (x1, y1), mask)
    if outline:
        ImageDraw.Draw(base).rounded_rectangle(xy, radius=radius, outline=outline, width=width)


def add_shadow(base: Image.Image, xy: tuple[int, int, int, int], radius: int, opacity: int = 46) -> None:
    x1, y1, x2, y2 = xy
    shadow = Image.new("RGBA", base.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle((x1 + 8, y1 + 10, x2 + 8, y2 + 10), radius=radius, fill=(10, 45, 95, opacity))
    shadow = shadow.filter(ImageFilter.GaussianBlur(16))
    base.alpha_composite(shadow)


def wrap_text(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.ImageFont, max_width: int) -> list[str]:
    lines: list[str] = []
    for raw in text.split("\n"):
        current = ""
        for char in raw:
            trial = current + char
            if text_size(draw, trial, fnt)[0] <= max_width or not current:
                current = trial
            else:
                lines.append(current)
                current = char
        lines.append(current)
    return lines


def draw_wrapped(
    draw: ImageDraw.ImageDraw,
    text: str,
    x: int,
    y: int,
    max_width: int,
    fnt: ImageFont.ImageFont,
    fill: str,
    line_gap: int = 8,
) -> int:
    for line in wrap_text(draw, text, fnt, max_width):
        draw.text((x, y), line, font=fnt, fill=fill)
        y += text_size(draw, line, fnt)[1] + line_gap
    return y


def draw_bullets(
    draw: ImageDraw.ImageDraw,
    items: list[str],
    x: int,
    y: int,
    max_width: int,
    fnt: ImageFont.ImageFont,
    fill: str = "#17233D",
    bullet_color: str = "#0B63E5",
    line_gap: int = 6,
    item_gap: int = 8,
) -> int:
    for item in items:
        draw.ellipse((x, y + 7, x + 8, y + 15), fill=bullet_color)
        y = draw_wrapped(draw, item, x + 22, y, max_width - 22, fnt, fill, line_gap)
        y += item_gap
    return y


def arrow(draw: ImageDraw.ImageDraw, start: tuple[int, int], end: tuple[int, int], color: str, width: int = 8) -> None:
    x1, y1 = start
    x2, y2 = end
    draw.line((x1, y1, x2, y2), fill=color, width=width)
    ang = math.atan2(y2 - y1, x2 - x1)
    head = 24
    spread = 0.48
    pts = [
        (x2, y2),
        (x2 - head * math.cos(ang - spread), y2 - head * math.sin(ang - spread)),
        (x2 - head * math.cos(ang + spread), y2 - head * math.sin(ang + spread)),
    ]
    draw.polygon(pts, fill=color)


def draw_funnel_icon(draw: ImageDraw.ImageDraw, x: int, y: int, color: str) -> None:
    draw.polygon([(x, y), (x + 82, y), (x + 53, y + 46), (x + 53, y + 82), (x + 30, y + 96), (x + 30, y + 46)], fill=color)
    for dx in (10, 36, 62):
        draw.ellipse((x + dx, y - 26, x + dx + 16, y - 10), fill=color)


def draw_database_icon(draw: ImageDraw.ImageDraw, x: int, y: int, color: str) -> None:
    draw.ellipse((x, y, x + 86, y + 28), outline=color, width=6)
    draw.rectangle((x, y + 14, x + 86, y + 76), outline=color, width=6)
    draw.ellipse((x, y + 62, x + 86, y + 90), outline=color, width=6)
    draw.line((x, y + 41, x + 86, y + 41), fill=color, width=4)


def draw_nodes_icon(draw: ImageDraw.ImageDraw, x: int, y: int, color: str) -> None:
    pts = [(x + 40, y + 10), (x + 10, y + 58), (x + 70, y + 58), (x + 40, y + 96)]
    for a, b in [(0, 1), (0, 2), (1, 3), (2, 3)]:
        draw.line((pts[a][0], pts[a][1], pts[b][0], pts[b][1]), fill=color, width=5)
    for px, py in pts:
        draw.ellipse((px - 12, py - 12, px + 12, py + 12), fill="white", outline=color, width=5)


def draw_shield_icon(draw: ImageDraw.ImageDraw, x: int, y: int, color: str) -> None:
    draw.polygon([(x + 42, y), (x + 82, y + 16), (x + 75, y + 70), (x + 42, y + 98), (x + 9, y + 70), (x + 2, y + 16)], outline=color, fill=None)
    draw.line((x + 23, y + 49, x + 38, y + 66, x + 63, y + 32), fill=color, width=8, joint="curve")


def draw_magnifier_icon(draw: ImageDraw.ImageDraw, x: int, y: int, color: str) -> None:
    draw.ellipse((x, y, x + 66, y + 66), outline=color, width=7)
    draw.line((x + 52, y + 52, x + 88, y + 88), fill=color, width=8)


def draw_panel(
    base: Image.Image,
    xy: tuple[int, int, int, int],
    number: str,
    title: str,
    primary: str,
    secondary: str,
    light: str,
) -> None:
    draw = ImageDraw.Draw(base)
    x1, y1, x2, y2 = xy
    add_shadow(base, xy, 20, 30)
    rounded_rect(draw, xy, 20, COLORS["white"], outline=primary, width=3)
    gradient_rounded_rect(base, (x1, y1, x2, y1 + 72), 20, primary, secondary)
    draw.rectangle((x1, y1 + 46, x2, y1 + 72), fill=secondary)
    draw.text((x1 + 32, y1 + 16), number, font=F["panel_num"], fill="white")
    draw.text((x1 + 86, y1 + 19), title, font=F["panel_header"], fill="white")


def draw_info_card(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int, int, int],
    title: str,
    bullets: list[str],
    color: str,
    icon: str,
) -> None:
    x1, y1, x2, y2 = xy
    rounded_rect(draw, xy, 16, "#FBFDFF", outline="#CAD8E9", width=2)
    icon_x, icon_y = x1 + 32, y1 + 58
    if icon == "funnel":
        draw_funnel_icon(draw, icon_x, icon_y, color)
    elif icon == "database":
        draw_database_icon(draw, icon_x, icon_y, color)
    elif icon == "nodes":
        draw_nodes_icon(draw, icon_x, icon_y, color)
    elif icon == "shield":
        draw_shield_icon(draw, icon_x, icon_y, color)
    else:
        draw_magnifier_icon(draw, icon_x, icon_y, color)
    draw.text((x1 + 150, y1 + 26), title, font=F["card_title"], fill=color)
    draw_bullets(draw, bullets, x1 + 150, y1 + 76, x2 - x1 - 180, F["body"], bullet_color=color)


def draw_compact_card(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int, int, int],
    title: str,
    bullets: list[str],
    color: str,
) -> None:
    x1, y1, x2, y2 = xy
    rounded_rect(draw, xy, 16, "#FBFDFF", outline="#CAD8E9", width=2)
    sx, sy = x1 + 34, y1 + 24
    draw.polygon(
        [(sx + 34, sy), (sx + 66, sy + 12), (sx + 60, sy + 52), (sx + 34, sy + 74), (sx + 8, sy + 52), (sx + 2, sy + 12)],
        outline=color,
        fill="#F7FCFA",
    )
    draw.line((sx + 20, sy + 40, sx + 32, sy + 54, sx + 52, sy + 26), fill=color, width=7, joint="curve")
    draw.text((x1 + 124, y1 + 18), title, font=F["card_title"], fill=color)
    draw_bullets(
        draw,
        bullets,
        x1 + 124,
        y1 + 58,
        x2 - x1 - 150,
        F["body_small"],
        bullet_color=color,
        line_gap=4,
        item_gap=4,
    )


def draw_metric_pair(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int, int, int],
    left_label: str,
    left_value: str,
    right_label: str,
    right_value: str,
) -> None:
    x1, y1, x2, y2 = xy
    rounded_rect(draw, xy, 16, "#F7FBFF", outline="#CAD8E9", width=2)
    mid = (x1 + x2) // 2
    draw.line((mid, y1 + 16, mid, y2 - 16), fill="#B8C9DF", width=2)
    for cx, label, val in [
        ((x1 + mid) // 2, left_label, left_value),
        ((mid + x2) // 2, right_label, right_value),
    ]:
        lw, _ = text_size(draw, label, F["metric_label"])
        vw, _ = text_size(draw, val, F["metric"])
        draw.text((cx - lw / 2, y1 + 14), label, font=F["metric_label"], fill=COLORS["navy"])
        draw.text((cx - vw / 2, y1 + 40), val, font=F["metric"], fill="#0E9F50")
        draw.polygon([(cx + vw / 2 + 10, y1 + 57), (cx + vw / 2 + 24, y1 + 57), (cx + vw / 2 + 17, y1 + 42)], fill="#0E9F50")


def pie_segment_label(
    draw: ImageDraw.ImageDraw,
    cx: int,
    cy: int,
    angle_deg: float,
    radius: int,
    title: str,
    subtitle: str,
    fill: str = "white",
) -> None:
    ang = math.radians(angle_deg)
    x = cx + math.cos(ang) * radius
    y = cy + math.sin(ang) * radius
    tw, th = text_size(draw, title, F["wheel_sub"])
    sw, _ = text_size(draw, subtitle, F["wheel_small"])
    draw.text((x - tw / 2, y - th), title, font=F["wheel_sub"], fill=fill)
    draw.text((x - sw / 2, y + 6), subtitle, font=F["wheel_small"], fill=fill)


def draw_flywheel(base: Image.Image) -> None:
    draw = ImageDraw.Draw(base)
    cx, cy = 1280, 510
    outer = 296
    inner = 142
    bbox = (cx - outer, cy - outer, cx + outer, cy + outer)
    segments = [
        (-92, 32, COLORS["green"], "2 技术能力闭环", "可验证 · 可追溯", -25),
        (32, 150, COLORS["orange"], "3 高频使用闭环", "诊疗 · 科研 · 患教", 92),
        (150, 270, COLORS["blue"], "1 专业信任闭环", "问即有据", 210),
    ]
    glow = Image.new("RGBA", base.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((cx - outer - 20, cy - outer - 20, cx + outer + 20, cy + outer + 20), fill=(28, 106, 214, 35))
    base.alpha_composite(glow.filter(ImageFilter.GaussianBlur(24)))
    for start, end, color, _, _, _ in segments:
        draw.pieslice(bbox, start=start, end=end, fill=color, outline="white", width=12)
    draw.ellipse((cx - inner, cy - inner, cx + inner, cy + inner), fill=COLORS["navy"], outline="white", width=12)
    draw.ellipse((cx - inner - 14, cy - inner - 14, cx + inner + 14, cy + inner + 14), outline="#C8DAFF", width=4)
    for _, _, _, title, subtitle, angle in segments:
        pie_segment_label(draw, cx, cy, angle, 218, title, subtitle)
    draw_centered(draw, "证元芳", cx, cy - 68, F["wheel_title"], "white")
    draw_centered(draw, "增长飞轮", cx, cy - 25, F["wheel_title"], "white")
    draw_centered(draw, "循证可信 · 高频工作流", cx, cy + 32, F["wheel_small"], "#CFE0FF")

    for ang, color in [(27, COLORS["green"]), (148, COLORS["blue"]), (269, COLORS["orange"])]:
        rad = math.radians(ang)
        tx = cx + math.cos(rad) * (outer - 8)
        ty = cy + math.sin(rad) * (outer - 8)
        tip = (tx + math.cos(rad + 0.7) * 2, ty + math.sin(rad + 0.7) * 2)
        left = (tx - 40 * math.cos(rad - 0.72), ty - 40 * math.sin(rad - 0.72))
        right = (tx - 40 * math.cos(rad + 0.18), ty - 40 * math.sin(rad + 0.18))
        draw.polygon([tip, left, right], fill=color, outline="white")

    arrow(draw, (800, 405), (966, 445), COLORS["blue2"], 10)
    arrow(draw, (1760, 405), (1594, 445), COLORS["green"], 10)
    arrow(draw, (1128, 790), (1005, 850), COLORS["orange"], 10)
    arrow(draw, (1432, 790), (1555, 850), COLORS["orange"], 10)


def draw_growth_panel(draw: ImageDraw.ImageDraw) -> None:
    x1, y1, x2, y2 = 400, 852, 2160, 1050
    draw.text(
        (1000, 812),
        "3 增长闭环：从专业信任到持续使用",
        font=F["section_header"],
        fill=COLORS["orange"],
        stroke_width=5,
        stroke_fill="#F8FBFF",
    )
    rounded_rect(draw, (x1, y1, x2, y2), 18, "#FFF8F1", outline=COLORS["orange"], width=3)
    cards = [
        ("价值触达", "医生快速理解：它能解决查证、科研、患教与备考痛点", None),
        ("注册 → 认证", "来源可追溯 + 权威测评背书，降低专业信任门槛", "+10%"),
        ("持续使用", "诊前/诊中/诊后与论文/方案/备考形成高频工作流", "+15%"),
    ]
    card_w = 490
    gap = 45
    start_x = x1 + 78
    for i, (title, body, metric) in enumerate(cards):
        cx = start_x + i * (card_w + gap)
        rounded_rect(draw, (cx, y1 + 50, cx + card_w, y2 - 32), 14, "#FFFFFF", outline="#FFD4AE", width=2)
        draw.text((cx + 30, y1 + 74), title, font=F["bottom_title"], fill=COLORS["orange"])
        body_width = card_w - 205 if metric else card_w - 60
        draw_wrapped(draw, body, cx + 30, y1 + 114, body_width, F["bottom_body"], "#1E2B44", 8)
        if metric:
            draw.text((cx + card_w - 142, y2 - 75), metric, font=F["metric"], fill="#0E9F50")
        if i < 2:
            arrow(draw, (cx + card_w + 10, y1 + 114), (cx + card_w + gap - 10, y1 + 114), COLORS["orange2"], 5)


def draw_knowledge_strip(draw: ImageDraw.ImageDraw) -> None:
    x1, y1, x2, y2 = 150, 1074, 2410, 1228
    rounded_rect(draw, (x1, y1, x2, y2), 18, "#FFFFFF", outline=COLORS["purple"], width=3)
    gradient_rounded_rect(canvas, (x1, y1, x1 + 780, y1 + 48), 18, COLORS["purple"], COLORS["purple2"])
    draw.rectangle((x1, y1 + 28, x1 + 780, y1 + 48), fill=COLORS["purple2"])
    draw.text((x1 + 28, y1 + 10), "4 知识中台：证据资产沉淀与能力迭代", font=F["bottom_title"], fill="white")
    steps = [
        ("多源医学数据", "PubMed / 中文在线 / 医学知识"),
        ("证据清洗治理", "标准化、去重、质量控制"),
        ("知识图谱与引用链", "5000万+ 实体级知识底座"),
        ("反馈与场景沉淀", "医生使用、评价、问答日志"),
        ("反哺模型/Skills", "Dr.GPT 与 2000+ Skills 迭代"),
    ]
    card_w = 370
    gap = 55
    sx = x1 + 70
    for i, (title, desc) in enumerate(steps):
        bx = sx + i * (card_w + gap)
        rounded_rect(draw, (bx, y1 + 64, bx + card_w, y2 - 16), 13, "#F8F7FF", outline="#D7D1FF", width=2)
        draw.text((bx + 24, y1 + 80), title, font=F["metric_label"], fill=COLORS["purple"])
        draw_wrapped(draw, desc, bx + 24, y1 + 112, card_w - 48, F["bottom_body"], "#22304A", 6)
        if i < len(steps) - 1:
            arrow(draw, (bx + card_w + 12, y1 + 113), (bx + card_w + gap - 16, y1 + 113), COLORS["purple2"], 5)


def draw_result_strip(draw: ImageDraw.ImageDraw) -> None:
    x1, y1, x2, y2 = 150, 1248, 2410, 1372
    rounded_rect(draw, (x1, y1, x2, y2), 18, "#F8FBFF", outline=COLORS["blue"], width=3)
    draw.text((x1 + 36, y1 + 38), "飞轮效应\n结果", font=F["bottom_title"], fill=COLORS["navy"], spacing=8)
    items = [
        ("专业价值更清楚", "注册意愿提升"),
        ("可信背书更强", "认证转化 +10%"),
        ("高频场景更完整", "留存率 +15%"),
        ("证据资产更厚", "能力持续迭代"),
        ("增长飞轮转动", "产品与商业共进"),
    ]
    sx = x1 + 310
    item_w = 360
    for i, (title, desc) in enumerate(items):
        bx = sx + i * item_w
        draw.ellipse((bx, y1 + 36, bx + 54, y1 + 90), fill="#EAF3FF", outline=COLORS["blue"], width=3)
        draw.text((bx + 19, y1 + 47), str(i + 1), font=F["metric_label"], fill=COLORS["blue"])
        draw.text((bx + 72, y1 + 34), title, font=F["metric_label"], fill=COLORS["navy"])
        draw.text((bx + 72, y1 + 70), desc, font=F["bottom_body"], fill=COLORS["gray"])
        if i < len(items) - 1:
            arrow(draw, (bx + 292, y1 + 64), (bx + 336, y1 + 64), "#9EB8DA", 4)


def draw_background(draw: ImageDraw.ImageDraw) -> None:
    draw.rectangle((0, 0, W, H), fill="#F8FBFF")
    bg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(bg)
    bd.ellipse((-540, -520, 900, 520), fill=(224, 240, 255, 160))
    bd.ellipse((1820, -500, 3100, 640), fill=(236, 249, 243, 140))
    bd.polygon([(0, 210), (0, 0), (480, 0), (275, 122)], fill=(233, 243, 255, 140))
    bd.polygon([(2560, 1440), (2050, 1440), (2360, 1180), (2560, 1110)], fill=(229, 241, 255, 160))
    bd.line((92, 1008, 92, 385, 150, 360), fill=(106, 90, 228, 120), width=3)
    bd.line((2468, 1008, 2468, 385, 2410, 360), fill=(106, 90, 228, 120), width=3)
    canvas.alpha_composite(bg)


canvas = Image.new("RGBA", (W, H), (255, 255, 255, 255))
draw = ImageDraw.Draw(canvas)
draw_background(draw)

draw_centered(draw, "证元芳循证医学智能体增长飞轮", W // 2, 54, F["title"], COLORS["navy"])
draw_centered(
    draw,
    "以可追溯医学证据与多智能体工作流，驱动医生端注册、认证与留存持续提升",
    W // 2,
    130,
    F["subtitle"],
    "#1E2B44",
)

draw_panel(canvas, (150, 200, 790, 790), "1", "产品闭环：专业价值清晰", COLORS["blue"], COLORS["blue2"], COLORS["blue_light"])
draw_info_card(
    draw,
    (180, 292, 760, 496),
    "证元芳是什么",
    [
        "面向医生/医学生的循证医学 AI 助手",
        "查循证、写论文、备考、做临床研究方案",
        "每个答案附医学文献或指南来源",
    ],
    COLORS["blue"],
    "funnel",
)
draw_info_card(
    draw,
    (180, 516, 760, 690),
    "医生核心痛点",
    [
        "文献/指南分散，查证成本高",
        "通用 AI 缺少可靠来源与追溯链",
        "临床、科研、患教工作流割裂",
    ],
    COLORS["blue"],
    "magnifier",
)
draw_metric_pair(draw, (180, 710, 760, 772), "注册-认证转化", "+10%", "留存率", "+15%")

draw_panel(canvas, (1770, 200, 2410, 790), "2", "技术闭环：可信能力组合", COLORS["green"], COLORS["green2"], COLORS["green_light"])
draw_info_card(
    draw,
    (1800, 292, 2380, 470),
    "Dr.GPT + 医学知识图谱",
    [
        "医疗-健康垂直大模型能力承载",
        "5000万+ 实体级医学知识底座",
        "权威文献、指南与医学知识融合",
    ],
    COLORS["green"],
    "database",
)
draw_info_card(
    draw,
    (1800, 492, 2380, 660),
    "MedClaw + Agent DeepResearch",
    [
        "多智能体协作完成深度研究",
        "检索、评估、引用验证链路贯通",
        "面向诊疗、科研、患教任务编排",
    ],
    COLORS["green"],
    "nodes",
)
draw_compact_card(
    draw,
    (1800, 674, 2380, 774),
    "能力背书",
    ["CAICT/泰尔实验室能力测评 13/13 通过", "MedClaw Skills Store 2000+ 标准化 Skills"],
    COLORS["green"],
)

draw_flywheel(canvas)
draw_growth_panel(draw)
draw_knowledge_strip(draw)
draw_result_strip(draw)

note = "注：+10% / +15% 为本次指定业务效果指标；产品定义、技术能力和背书数据来自产品真源库（Aicare-Product-Kb，a19fac3）。"
draw_centered(draw, note, W // 2, 1388, F["note"], "#5D6678")

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
canvas.convert("RGB").save(OUTPUT, quality=95)
print(OUTPUT)
