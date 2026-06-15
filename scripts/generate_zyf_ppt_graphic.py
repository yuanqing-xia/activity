from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path("/Users/xyq-mac/Documents/活动申请")
OUT_DIR = ROOT / "outputs" / "证元芳_PPT图示"
OUT_DIR.mkdir(parents=True, exist_ok=True)

PNG_OUT = OUT_DIR / "证元芳_技术领域工作效果图_16x9.png"

FONT_REG = "/System/Library/Fonts/STHeiti Light.ttc"
FONT_BOLD = "/System/Library/Fonts/STHeiti Medium.ttc"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size)


def text_size(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont) -> tuple[int, int]:
    box = draw.textbbox((0, 0), text, font=fnt)
    return box[2] - box[0], box[3] - box[1]


def wrap_text(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    lines: list[str] = []
    for raw in text.split("\n"):
        line = ""
        for ch in raw:
            trial = line + ch
            if text_size(draw, trial, fnt)[0] <= max_width:
                line = trial
            else:
                if line:
                    lines.append(line)
                line = ch
        if line:
            lines.append(line)
    return lines


def draw_wrapped(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    fnt: ImageFont.FreeTypeFont,
    fill: str,
    max_width: int,
    line_gap: int = 8,
    anchor: str | None = None,
) -> int:
    x, y = xy
    lines = wrap_text(draw, text, fnt, max_width)
    line_h = text_size(draw, "国", fnt)[1] + line_gap
    for idx, line in enumerate(lines):
        if anchor == "mm":
            draw.text((x, y + idx * line_h), line, font=fnt, fill=fill, anchor="mm")
        else:
            draw.text((x, y + idx * line_h), line, font=fnt, fill=fill)
    return len(lines) * line_h


def rounded_rect(
    base: Image.Image,
    xy: tuple[int, int, int, int],
    radius: int,
    fill: str,
    outline: str | None = None,
    width: int = 2,
    shadow: bool = False,
) -> None:
    if shadow:
        layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
        sd = ImageDraw.Draw(layer)
        sd.rounded_rectangle((xy[0] + 8, xy[1] + 10, xy[2] + 8, xy[3] + 10), radius, fill=(23, 39, 75, 28))
        layer = layer.filter(ImageFilter.GaussianBlur(10))
        base.alpha_composite(layer)
    d = ImageDraw.Draw(base)
    d.rounded_rectangle(xy, radius, fill=fill, outline=outline, width=width)


def arrow(draw: ImageDraw.ImageDraw, start: tuple[int, int], end: tuple[int, int], fill: str) -> None:
    draw.line((start, end), fill=fill, width=7)
    sx, sy = start
    ex, ey = end
    ang = math.atan2(ey - sy, ex - sx)
    size = 22
    pts = [
        (ex, ey),
        (ex - size * math.cos(ang - 0.45), ey - size * math.sin(ang - 0.45)),
        (ex - size * math.cos(ang + 0.45), ey - size * math.sin(ang + 0.45)),
    ]
    draw.polygon(pts, fill=fill)


def pill(draw: ImageDraw.ImageDraw, xy: tuple[int, int, int, int], text: str, fill: str, color: str) -> None:
    draw.rounded_rectangle(xy, radius=(xy[3] - xy[1]) // 2, fill=fill)
    draw.text(((xy[0] + xy[2]) // 2, (xy[1] + xy[3]) // 2 - 2), text, font=font(30, True), fill=color, anchor="mm")


def draw_metric(
    img: Image.Image,
    xy: tuple[int, int, int, int],
    label: str,
    value: str,
    note: str,
    accent: str,
) -> None:
    d = ImageDraw.Draw(img)
    rounded_rect(img, xy, 28, "#FFFFFF", outline="#C9D7E8", shadow=True)
    x1, y1, x2, y2 = xy
    d.rounded_rectangle((x1 + 26, y1 + 26, x1 + 92, y1 + 92), 22, fill=accent)
    d.text((x1 + 59, y1 + 60), "↑", font=font(46, True), fill="#FFFFFF", anchor="mm")
    d.text((x1 + 120, y1 + 30), label, font=font(31, True), fill="#21354D")
    d.text((x1 + 120, y1 + 82), value, font=font(68, True), fill=accent)
    draw_wrapped(d, (x1 + 120, y1 + 160), note, font(25), "#597089", x2 - x1 - 150, line_gap=8)


def main() -> None:
    W, H = 2400, 1350
    img = Image.new("RGBA", (W, H), "#F6F8FB")
    d = ImageDraw.Draw(img)

    # Subtle background bands.
    d.rectangle((0, 0, W, 260), fill="#EEF6FA")
    d.rounded_rectangle((1620, -150, 2550, 410), 220, fill="#E5F5F1")
    d.rounded_rectangle((-240, 820, 620, 1510), 260, fill="#EDF2FF")

    d.text((120, 86), "证元芳：基于 Dr.GPT 的循证医学智能体", font=font(60, True), fill="#172B4D")
    d.text(
        (122, 172),
        "基于专业大模型 + 医学知识图谱，在临床决策支持与医学科研领域开展可追溯 AI 工作流",
        font=font(33),
        fill="#4C5F75",
    )
    pill(d, (1880, 82, 2260, 138), "产品真源库口径", "#DFF4EF", "#0B7A75")
    pill(d, (1880, 154, 2260, 210), "PPT 16:9 高清图", "#EAF0FF", "#4267B2")

    col_y, col_h = 320, 650
    cols = [
        (110, col_y, 690, col_y + col_h, "技术底座", "#0B7A75"),
        (910, col_y, 1490, col_y + col_h, "开展工作", "#315C9A"),
        (1710, col_y, 2290, col_y + col_h, "效果呈现", "#B35C1E"),
    ]
    for x1, y1, x2, y2, title, accent in cols:
        rounded_rect(img, (x1, y1, x2, y2), 36, "#FFFFFF", outline="#D8E2EF", shadow=True)
        d.rounded_rectangle((x1, y1, x2, y1 + 92), 36, fill=accent)
        d.rectangle((x1, y1 + 46, x2, y1 + 92), fill=accent)
        d.text(((x1 + x2) // 2, y1 + 48), title, font=font(38, True), fill="#FFFFFF", anchor="mm")

    # Left cards.
    left_items = [
        ("Dr.GPT", "医疗-健康垂直大模型，提供医学语义理解、推理与生成能力"),
        ("5000 万+ 知识底座", "PubMed + 中文在线 + 卫和三源融合的医学知识图谱"),
        ("MedClaw + DeepResearch", "多智能体协作，完成深度检索、权威评估、引用验证"),
        ("2000+ Skills", "覆盖临床、公共卫生、医学教育等标准化能力"),
    ]
    y = 445
    for title, body in left_items:
        d.rounded_rectangle((150, y, 650, y + 105), 22, fill="#F2FAF8", outline="#CBE7E2", width=2)
        d.text((178, y + 20), title, font=font(30, True), fill="#0B6D69")
        draw_wrapped(d, (178, y + 60), body, font(23), "#456173", 430, line_gap=6)
        y += 124

    # Middle work flow.
    work_items = [
        ("诊前 / 诊中 / 诊后", "循证依据调取、临床决策参考、患者解释"),
        ("医学科研", "论文写作优化、文献解读、临床研究方案设计"),
        ("医学教育与患教", "考试备考、科普内容、医学图像与教学仿真"),
        ("机构级落地", "医院 / 药企定制化，医保合规 Skill 集与护理场景扩展"),
    ]
    y = 442
    for idx, (title, body) in enumerate(work_items, 1):
        cy = y + 50
        d.ellipse((960, cy - 31, 1022, cy + 31), fill="#315C9A")
        d.text((991, cy - 1), str(idx), font=font(30, True), fill="#FFFFFF", anchor="mm")
        d.text((1050, y + 10), title, font=font(30, True), fill="#243B59")
        draw_wrapped(d, (1050, y + 55), body, font(24), "#5B6C7D", 370, line_gap=7)
        if idx < len(work_items):
            d.line((991, cy + 39, 991, cy + 82), fill="#AFC1D8", width=5)
        y += 125

    # Right effects.
    draw_metric(
        img,
        (1750, 445, 2250, 635),
        "注册-认证转化",
        "+10%",
        "用于呈现本次业务效果指标",
        "#E36B2C",
    )
    draw_metric(
        img,
        (1750, 680, 2250, 870),
        "留存率",
        "+15%",
        "用于呈现使用后的持续活跃提升",
        "#16A085",
    )

    # Arrows between columns.
    arrow(d, (705, 650), (895, 650), "#8EA4BF")
    arrow(d, (1505, 650), (1695, 650), "#8EA4BF")

    # Bottom proof row.
    rounded_rect(img, (110, 1035, 2290, 1218), 34, "#172B4D", shadow=True)
    d.text((160, 1082), "产品真源库可支撑的背书", font=font(34, True), fill="#FFFFFF")
    proof_items = [
        ("13/13", "CAICT / 泰尔实验室能力测评通过"),
        ("69,615 人", "证元芳赋能医路轻松平台医学专业人士"),
        ("52.7%", "副主任以上医师占比"),
        ("百家重点医院", "护理记录、病历核对、护理方案、患者宣教场景"),
    ]
    px = 620
    for value, label in proof_items:
        d.text((px, 1072), value, font=font(40, True), fill="#9DF3E5", anchor="mm")
        draw_wrapped(d, (px - 140, 1120), label, font(22), "#DDE8F5", 280, line_gap=5)
        px += 430

    # Footnote.
    d.text(
        (120, 1262),
        "注：+10% / +15% 为本次指定呈现的业务效果指标；产品定义、技术底座、测评与平台数据来自产品真源库 qschouteam/Aicare-Product-Kb（a19fac3）。",
        font=font(21),
        fill="#6B7C8F",
    )

    img.convert("RGB").save(PNG_OUT, quality=95)
    print(PNG_OUT)


if __name__ == "__main__":
    main()
