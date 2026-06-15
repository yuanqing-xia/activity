#!/usr/bin/env python3
"""Generate a PPT-ready product introduction graphic for ZhengYuanfang."""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs" / "证元芳_PPT图示" / "证元芳_产品介绍图_16x9_v4.png"
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
    "title": font(61, True),
    "subtitle": font(28),
    "panel_header": font(28, True),
    "panel_num": font(34, True),
    "card_title": font(25, True),
    "body": font(21),
    "small": font(18),
    "tiny": font(16),
    "center_title": font(56, True),
    "center_sub": font(26, True),
    "center_body": font(22),
    "metric": font(35, True),
    "metric_label": font(20, True),
    "section": font(28, True),
    "strip_title": font(23, True),
    "note": font(17),
}

COLORS = {
    "navy": "#061E4D",
    "text": "#192945",
    "muted": "#546179",
    "line": "#CAD8E9",
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
    "purple_light": "#F2EFFF",
}


def rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def text_size(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.ImageFont) -> tuple[int, int]:
    if not text:
        return 0, 0
    box = draw.textbbox((0, 0), text, font=fnt)
    return box[2] - box[0], box[3] - box[1]


def centered(draw: ImageDraw.ImageDraw, text: str, cx: int, y: int, fnt: ImageFont.ImageFont, fill: str) -> None:
    tw, _ = text_size(draw, text, fnt)
    draw.text((cx - tw / 2, y), text, font=fnt, fill=fill)


def rr(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int, int, int],
    radius: int,
    fill: str,
    outline: str | None = None,
    width: int = 1,
) -> None:
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def gradient_rect(
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
    c1, c2 = rgb(left), rgb(right)
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


def shadow(base: Image.Image, xy: tuple[int, int, int, int], radius: int, opacity: int = 34) -> None:
    x1, y1, x2, y2 = xy
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(layer)
    sd.rounded_rectangle((x1 + 8, y1 + 10, x2 + 8, y2 + 10), radius=radius, fill=(10, 45, 95, opacity))
    base.alpha_composite(layer.filter(ImageFilter.GaussianBlur(16)))


def wrap(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.ImageFont, width: int) -> list[str]:
    lines: list[str] = []
    for para in text.split("\n"):
        current = ""
        for ch in para:
            trial = current + ch
            if text_size(draw, trial, fnt)[0] <= width or not current:
                current = trial
            else:
                lines.append(current)
                current = ch
        lines.append(current)
    return lines


def wrapped(
    draw: ImageDraw.ImageDraw,
    text: str,
    x: int,
    y: int,
    width: int,
    fnt: ImageFont.ImageFont,
    fill: str,
    line_gap: int = 6,
) -> int:
    for line in wrap(draw, text, fnt, width):
        draw.text((x, y), line, font=fnt, fill=fill)
        y += text_size(draw, line, fnt)[1] + line_gap
    return y


def bullets(
    draw: ImageDraw.ImageDraw,
    items: list[str],
    x: int,
    y: int,
    width: int,
    fnt: ImageFont.ImageFont,
    color: str,
    fill: str = COLORS["text"],
    gap: int = 7,
) -> int:
    for item in items:
        draw.ellipse((x, y + 8, x + 8, y + 16), fill=color)
        y = wrapped(draw, item, x + 22, y, width - 22, fnt, fill, 5)
        y += gap
    return y


def arrow(draw: ImageDraw.ImageDraw, start: tuple[int, int], end: tuple[int, int], color: str, width: int = 5) -> None:
    x1, y1 = start
    x2, y2 = end
    draw.line((x1, y1, x2, y2), fill=color, width=width)
    angle = math.atan2(y2 - y1, x2 - x1)
    head = 20
    spread = 0.5
    pts = [
        (x2, y2),
        (x2 - head * math.cos(angle - spread), y2 - head * math.sin(angle - spread)),
        (x2 - head * math.cos(angle + spread), y2 - head * math.sin(angle + spread)),
    ]
    draw.polygon(pts, fill=color)


def panel(
    base: Image.Image,
    xy: tuple[int, int, int, int],
    number: str,
    title: str,
    c1: str,
    c2: str,
) -> None:
    draw = ImageDraw.Draw(base)
    x1, y1, x2, y2 = xy
    shadow(base, xy, 20)
    rr(draw, xy, 20, "white", c1, 3)
    gradient_rect(base, (x1, y1, x2, y1 + 70), 20, c1, c2)
    draw.rectangle((x1, y1 + 46, x2, y1 + 70), fill=c2)
    draw.text((x1 + 30, y1 + 15), number, font=F["panel_num"], fill="white")
    draw.text((x1 + 84, y1 + 19), title, font=F["panel_header"], fill="white")


def icon_people(draw: ImageDraw.ImageDraw, x: int, y: int, color: str) -> None:
    for dx, dy, r in [(35, 0, 18), (8, 18, 15), (62, 18, 15)]:
        draw.ellipse((x + dx - r, y + dy, x + dx + r, y + dy + 2 * r), fill=color)
    draw.rounded_rectangle((x + 10, y + 56, x + 95, y + 98), 20, fill=color)


def icon_doc(draw: ImageDraw.ImageDraw, x: int, y: int, color: str) -> None:
    rr(draw, (x, y, x + 82, y + 100), 10, "#FFFFFF", color, 6)
    draw.line((x + 20, y + 32, x + 62, y + 32), fill=color, width=5)
    draw.line((x + 20, y + 55, x + 62, y + 55), fill=color, width=5)
    draw.line((x + 20, y + 78, x + 48, y + 78), fill=color, width=5)


def icon_database(draw: ImageDraw.ImageDraw, x: int, y: int, color: str) -> None:
    draw.ellipse((x, y, x + 86, y + 28), outline=color, width=6)
    draw.rectangle((x, y + 14, x + 86, y + 78), outline=color, width=6)
    draw.ellipse((x, y + 64, x + 86, y + 94), outline=color, width=6)
    draw.line((x, y + 43, x + 86, y + 43), fill=color, width=4)


def icon_nodes(draw: ImageDraw.ImageDraw, x: int, y: int, color: str) -> None:
    pts = [(x + 42, y + 8), (x + 12, y + 52), (x + 72, y + 52), (x + 42, y + 95)]
    for a, b in [(0, 1), (0, 2), (1, 3), (2, 3)]:
        draw.line((pts[a][0], pts[a][1], pts[b][0], pts[b][1]), fill=color, width=5)
    for px, py in pts:
        draw.ellipse((px - 12, py - 12, px + 12, py + 12), fill="white", outline=color, width=5)


def icon_check(draw: ImageDraw.ImageDraw, x: int, y: int, color: str) -> None:
    draw.polygon([(x + 30, y), (x + 60, y + 12), (x + 55, y + 50), (x + 30, y + 70), (x + 6, y + 50), (x, y + 12)], outline=color, fill="#F7FCFA")
    draw.line((x + 16, y + 36, x + 28, y + 48, x + 48, y + 23), fill=color, width=6)


def info_card(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int, int, int],
    title: str,
    items: list[str],
    color: str,
    icon: str,
) -> None:
    x1, y1, x2, y2 = xy
    rr(draw, xy, 15, "#FBFDFF", COLORS["line"], 2)
    ix, iy = x1 + 30, y1 + 47
    if icon == "people":
        icon_people(draw, ix, iy, color)
    elif icon == "doc":
        icon_doc(draw, ix, iy, color)
    elif icon == "database":
        icon_database(draw, ix, iy, color)
    elif icon == "nodes":
        icon_nodes(draw, ix, iy, color)
    elif icon == "check":
        icon_check(draw, ix + 8, y1 + 12, color)
    else:
        icon_check(draw, ix, iy, color)
    draw.text((x1 + 145, y1 + 24), title, font=F["card_title"], fill=color)
    bullets(draw, items, x1 + 145, y1 + 69, x2 - x1 - 170, F["body"], color)


def capability_tile(draw: ImageDraw.ImageDraw, xy: tuple[int, int, int, int], title: str, body: str, color: str) -> None:
    x1, y1, x2, y2 = xy
    rr(draw, xy, 15, "white", "#CFE0F2", 2)
    draw.ellipse((x1 + 22, y1 + 28, x1 + 62, y1 + 68), fill=color)
    draw.text((x1 + 82, y1 + 21), title, font=F["card_title"], fill=color)
    wrapped(draw, body, x1 + 82, y1 + 59, x2 - x1 - 105, F["small"], COLORS["text"], 5)


def mini_capability(draw: ImageDraw.ImageDraw, xy: tuple[int, int, int, int], title: str, body: str, color: str) -> None:
    x1, y1, x2, y2 = xy
    rr(draw, xy, 14, "#FFFFFF", "#CFE0F2", 2)
    draw.ellipse((x1 + 18, y1 + 18, x1 + 52, y1 + 52), fill=color)
    draw.text((x1 + 64, y1 + 17), title, font=F["metric_label"], fill=color)
    wrapped(draw, body, x1 + 18, y1 + 62, x2 - x1 - 36, F["tiny"], COLORS["text"], 5)


def draw_center_product(base: Image.Image) -> None:
    draw = ImageDraw.Draw(base)
    xy = (840, 218, 1720, 788)
    shadow(base, xy, 26, 38)
    rr(draw, xy, 26, "#FFFFFF", "#BFD1EA", 2)
    gradient_rect(base, (840, 218, 1720, 320), 26, "#0A2F6F", "#0D8A82")
    draw.rectangle((840, 286, 1720, 320), fill="#0D8A82")
    centered(draw, "证元芳产品介绍", 1280, 248, F["section"], "white")
    centered(draw, "问即有据 · 可验证 · 可追溯", 1280, 286, F["small"], "#DDF7F2")

    draw.ellipse((1035, 348, 1525, 585), fill=COLORS["navy"], outline="#CFE0FF", width=8)
    centered(draw, "证元芳", 1280, 388, F["center_title"], "white")
    centered(draw, "循证医学 AI 助手", 1280, 460, F["center_sub"], "#9EF2E3")
    centered(draw, "把分散医学证据转化为可引用、可解释的工作流输出", 1280, 526, F["center_body"], "#D9E7FF")

    mini_capability(draw, (880, 626, 1070, 742), "循证问答", "回答附文献或指南来源", COLORS["blue"])
    mini_capability(draw, (1095, 626, 1285, 742), "科研写作", "论文优化与研究方案设计", COLORS["green"])
    mini_capability(draw, (1310, 626, 1500, 742), "学习备考", "真题备考与知识解释", COLORS["orange"])
    mini_capability(draw, (1525, 626, 1715, 742), "患教科普", "宣教、科普内容生成", COLORS["purple"])

    arrow(draw, (790, 480), (842, 480), COLORS["blue2"], 7)
    arrow(draw, (1770, 480), (1720, 480), COLORS["green"], 7)
    arrow(draw, (1280, 788), (1280, 838), COLORS["orange"], 7)


def workflow_panel(draw: ImageDraw.ImageDraw) -> None:
    x1, y1, x2, y2 = 150, 830, 2410, 1058
    rr(draw, (x1, y1, x2, y2), 18, "#FFF8F1", COLORS["orange"], 3)
    draw.text((x1 + 28, y1 + 18), "3 典型工作流：从医学问题到可追溯产出", font=F["section"], fill=COLORS["orange"])
    steps = [
        ("需求输入", "临床问题 / 科研任务 / 学习备考"),
        ("证据检索", "文献、指南、知识图谱同步检索"),
        ("多智能体协作", "拆解任务、评估证据、组织答案"),
        ("引用验证", "保留来源链路，便于医生复核"),
        ("结构化输出", "问答、论文、方案、患教与科普"),
    ]
    card_w, gap = 380, 55
    sx = x1 + 78
    for i, (title, body) in enumerate(steps):
        bx = sx + i * (card_w + gap)
        rr(draw, (bx, y1 + 82, bx + card_w, y2 - 28), 14, "#FFFFFF", "#FFD4AE", 2)
        draw.text((bx + 26, y1 + 106), title, font=F["card_title"], fill=COLORS["orange"])
        wrapped(draw, body, bx + 26, y1 + 146, card_w - 52, F["small"], COLORS["text"], 6)
        if i < len(steps) - 1:
            arrow(draw, (bx + card_w + 10, y1 + 145), (bx + card_w + gap - 14, y1 + 145), COLORS["orange2"], 5)


def knowledge_strip(draw: ImageDraw.ImageDraw) -> None:
    x1, y1, x2, y2 = 150, 1090, 2410, 1226
    rr(draw, (x1, y1, x2, y2), 18, "#FFFFFF", COLORS["purple"], 3)
    gradient_rect(canvas, (x1, y1, x1 + 760, y1 + 48), 18, COLORS["purple"], COLORS["purple2"])
    draw.rectangle((x1, y1 + 28, x1 + 760, y1 + 48), fill=COLORS["purple2"])
    draw.text((x1 + 26, y1 + 10), "4 数据与能力资产：支撑“问即有据”的底座", font=F["strip_title"], fill="white")
    items = [
        ("多源医学数据", "PubMed / 中文在线 / 医学知识"),
        ("5000万+实体", "医学知识融合底座"),
        ("MedClaw Skills", "2000+ 标准化 Skills"),
        ("可信测评", "CAICT/泰尔实验室 13/13"),
        ("反馈沉淀", "问答、评价、场景持续迭代"),
    ]
    card_w, gap, sx = 365, 56, x1 + 70
    for i, (title, body) in enumerate(items):
        bx = sx + i * (card_w + gap)
        rr(draw, (bx, y1 + 66, bx + card_w, y2 - 16), 13, "#F8F7FF", "#D7D1FF", 2)
        draw.text((bx + 22, y1 + 82), title, font=F["metric_label"], fill=COLORS["purple"])
        draw.text((bx + 22, y1 + 116), body, font=F["small"], fill=COLORS["text"])
        if i < len(items) - 1:
            arrow(draw, (bx + card_w + 11, y1 + 110), (bx + card_w + gap - 16, y1 + 110), COLORS["purple2"], 5)


def result_strip(draw: ImageDraw.ImageDraw) -> None:
    x1, y1, x2, y2 = 150, 1246, 2410, 1370
    rr(draw, (x1, y1, x2, y2), 18, "#F8FBFF", COLORS["blue"], 3)
    draw.text((x1 + 34, y1 + 37), "应用效果\n与背书", font=F["strip_title"], fill=COLORS["navy"], spacing=8)
    items = [
        ("69,615", "医学专业人士用户"),
        ("52.7%", "副主任以上医师占比"),
        ("百家重点医院", "护理/病历/宣教等场景"),
        ("+10%", "注册-认证转化"),
        ("+15%", "留存率"),
    ]
    sx, item_w = x1 + 285, 380
    for i, (value, label) in enumerate(items):
        bx = sx + i * item_w
        rr(draw, (bx, y1 + 28, bx + 320, y2 - 26), 14, "white", "#CFE0F2", 2)
        tw, _ = text_size(draw, value, F["metric"])
        draw.text((bx + 160 - tw / 2, y1 + 42), value, font=F["metric"], fill="#0E9F50" if value.startswith("+") else COLORS["blue"])
        lw, _ = text_size(draw, label, F["small"])
        draw.text((bx + 160 - lw / 2, y1 + 87), label, font=F["small"], fill=COLORS["muted"])


def background(base: Image.Image) -> None:
    bg = Image.new("RGBA", base.size, (248, 251, 255, 255))
    d = ImageDraw.Draw(bg)
    d.ellipse((-560, -520, 900, 535), fill=(224, 240, 255, 165))
    d.ellipse((1800, -500, 3140, 645), fill=(235, 249, 242, 145))
    d.polygon([(0, 220), (0, 0), (520, 0), (290, 130)], fill=(233, 243, 255, 140))
    d.polygon([(2560, 1440), (2050, 1440), (2360, 1180), (2560, 1110)], fill=(229, 241, 255, 160))
    d.line((92, 1010, 92, 380, 150, 360), fill=(106, 90, 228, 105), width=3)
    d.line((2468, 1010, 2468, 380, 2410, 360), fill=(106, 90, 228, 105), width=3)
    base.alpha_composite(bg)


canvas = Image.new("RGBA", (W, H), (255, 255, 255, 255))
draw = ImageDraw.Draw(canvas)
background(canvas)

centered(draw, "证元芳：问即有据的循证医学 AI 助手", W // 2, 54, F["title"], COLORS["navy"])
centered(
    draw,
    "面向医生与医学生，基于医学知识图谱、多智能体和可追溯证据链，提供临床、科研、学习与患教工作流",
    W // 2,
    130,
    F["subtitle"],
    COLORS["text"],
)

panel(canvas, (150, 205, 790, 780), "1", "产品定位：服务医生工作", COLORS["blue"], COLORS["blue2"])
info_card(
    draw,
    (180, 296, 760, 482),
    "它是什么",
    [
        "i-Magellanic 麦哲伦医药研究平台下的医学 AI 助手",
        "面向医生、医学生和医学专业场景",
        "核心表达：问即有据",
    ],
    COLORS["blue"],
    "people",
)
info_card(
    draw,
    (180, 504, 760, 744),
    "解决什么问题",
    [
        "文献、指南和医学知识分散，查证成本高",
        "通用 AI 回答缺少可靠来源和证据追溯",
        "临床、科研、患教、备考任务分散在不同工具中",
        "需要更适合医学场景的结构化输出",
    ],
    COLORS["blue"],
    "doc",
)

panel(canvas, (1770, 205, 2410, 780), "2", "技术底座：可信回答来源", COLORS["green"], COLORS["green2"])
info_card(
    draw,
    (1800, 296, 2380, 476),
    "Dr.GPT + 知识图谱",
    [
        "医疗-健康垂直大模型能力承载",
        "5000万+ 实体级医学知识底座",
        "融合权威文献、指南与医学知识",
    ],
    COLORS["green"],
    "database",
)
info_card(
    draw,
    (1800, 496, 2380, 660),
    "MedClaw + Agent DeepResearch",
    [
        "多智能体协作完成复杂医学任务",
        "检索、评估、引用验证链路贯通",
        "形成诊疗、科研、患教等标准化工作流",
    ],
    COLORS["green"],
    "nodes",
)
info_card(
    draw,
    (1800, 680, 2380, 744),
    "可信背书",
    [
        "CAICT/泰尔实验室能力测评 13/13 通过",
    ],
    COLORS["green"],
    "check",
)

draw_center_product(canvas)
workflow_panel(draw)
knowledge_strip(draw)
result_strip(draw)

note = "注：+10% / +15% 为本次指定业务效果指标；产品定义、技术能力与背书数据来自产品真源库（Aicare-Product-Kb，a19fac3）。"
centered(draw, note, W // 2, 1390, F["note"], "#5D6678")

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
canvas.convert("RGB").save(OUTPUT, quality=95)
print(OUTPUT)
