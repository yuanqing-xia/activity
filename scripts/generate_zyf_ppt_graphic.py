from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path("/Users/xyq-mac/Documents/活动申请")
OUT_DIR = ROOT / "outputs" / "证元芳_PPT图示"
OUT_DIR.mkdir(parents=True, exist_ok=True)

PNG_OUT = OUT_DIR / "证元芳_增长逻辑图_16x9_v2.png"
LEGACY_OUT = OUT_DIR / "证元芳_技术领域工作效果图_16x9.png"

FONT_REG = "/System/Library/Fonts/STHeiti Light.ttc"
FONT_BOLD = "/System/Library/Fonts/STHeiti Medium.ttc"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size)


def measure(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont) -> tuple[int, int]:
    box = draw.textbbox((0, 0), text, font=fnt)
    return box[2] - box[0], box[3] - box[1]


def wrap(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    lines: list[str] = []
    for paragraph in text.split("\n"):
        current = ""
        for ch in paragraph:
            trial = current + ch
            if measure(draw, trial, fnt)[0] <= max_width:
                current = trial
            else:
                if current:
                    lines.append(current)
                current = ch
        if current:
            lines.append(current)
    return lines


def draw_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    fnt: ImageFont.FreeTypeFont,
    color: str,
    max_width: int | None = None,
    line_gap: int = 8,
    anchor: str | None = None,
) -> int:
    x, y = xy
    if max_width is None:
        draw.text((x, y), text, font=fnt, fill=color, anchor=anchor)
        return measure(draw, text, fnt)[1]
    lines = wrap(draw, text, fnt, max_width)
    line_h = measure(draw, "国", fnt)[1] + line_gap
    for idx, line in enumerate(lines):
        draw.text((x, y + idx * line_h), line, font=fnt, fill=color, anchor=anchor)
    return len(lines) * line_h


def rounded(
    img: Image.Image,
    xy: tuple[int, int, int, int],
    radius: int,
    fill: str,
    outline: str | None = None,
    width: int = 2,
    shadow: bool = False,
) -> None:
    if shadow:
        layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        sd = ImageDraw.Draw(layer)
        sd.rounded_rectangle((xy[0] + 10, xy[1] + 14, xy[2] + 10, xy[3] + 14), radius, fill=(27, 39, 68, 34))
        layer = layer.filter(ImageFilter.GaussianBlur(16))
        img.alpha_composite(layer)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle(xy, radius, fill=fill, outline=outline, width=width)


def arrow(draw: ImageDraw.ImageDraw, start: tuple[int, int], end: tuple[int, int], color: str, width: int = 7) -> None:
    sx, sy = start
    ex, ey = end
    draw.line((sx, sy, ex, ey), fill=color, width=width)
    size = 24
    draw.polygon([(ex, ey), (ex - size, ey - 14), (ex - size, ey + 14)], fill=color)


def tag(draw: ImageDraw.ImageDraw, xy: tuple[int, int, int, int], text: str, fill: str, color: str) -> None:
    draw.rounded_rectangle(xy, radius=(xy[3] - xy[1]) // 2, fill=fill)
    draw.text(((xy[0] + xy[2]) // 2, (xy[1] + xy[3]) // 2 - 2), text, font=font(25, True), fill=color, anchor="mm")


def stage_card(
    img: Image.Image,
    x: int,
    y: int,
    w: int,
    h: int,
    num: str,
    title: str,
    body: str,
    accent: str,
) -> None:
    d = ImageDraw.Draw(img)
    rounded(img, (x, y, x + w, y + h), 28, "#FFFFFF", "#D7E2F0", shadow=True)
    d.ellipse((x + 28, y + 28, x + 92, y + 92), fill=accent)
    d.text((x + 60, y + 60), num, font=font(33, True), fill="#FFFFFF", anchor="mm")
    d.text((x + 115, y + 29), title, font=font(31, True), fill="#172B4D")
    draw_text(d, (x + 115, y + 78), body, font(23), "#516579", w - 140, line_gap=7)


def metric_badge(img: Image.Image, x: int, y: int, label: str, value: str, color: str) -> None:
    d = ImageDraw.Draw(img)
    rounded(img, (x, y, x + 310, y + 144), 26, "#FFFFFF", "#D8E2F0", shadow=True)
    d.text((x + 28, y + 24), label, font=font(26, True), fill="#243B59")
    d.text((x + 28, y + 72), value, font=font(58, True), fill=color)


def inline_metric(draw: ImageDraw.ImageDraw, xy: tuple[int, int, int, int], value: str, color: str) -> None:
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle(xy, radius=18, fill="#FFFFFF", outline="#D8E2F0", width=2)
    draw.text(((x1 + x2) // 2, y1 + 24), "提升", font=font(20, True), fill="#66788C", anchor="mm")
    draw.text(((x1 + x2) // 2, y1 + 70), value, font=font(44, True), fill=color, anchor="mm")


def main() -> None:
    W, H = 2400, 1350
    img = Image.new("RGBA", (W, H), "#F7F9FC")
    d = ImageDraw.Draw(img)

    # Background geometry: muted, PPT-friendly, no decorative clutter.
    d.rectangle((0, 0, W, 238), fill="#EAF3F8")
    d.rounded_rectangle((1760, -230, 2550, 360), 260, fill="#E4F4EE")
    d.rectangle((0, 1190, W, H), fill="#F0F4FA")

    # Header.
    d.text((95, 62), "证元芳如何带动医生端注册、认证与留存增长", font=font(58, True), fill="#122844")
    d.text(
        (98, 146),
        "逻辑：先让医生理解“这是什么、为什么可信、能解决什么工作”，再把信任转化为认证，把高频工作流转化为留存。",
        font=font(29),
        fill="#50667C",
    )
    tag(d, (1895, 70, 2260, 126), "产品真源库 a19fac3", "#DDF3EE", "#08736F")
    tag(d, (1895, 146, 2260, 202), "PPT 16:9 高清 PNG", "#E7EEFF", "#315C9A")

    # Claim band.
    rounded(img, (95, 270, 2305, 390), 32, "#172B4D", shadow=True)
    d.text((140, 312), "核心表述", font=font(34, True), fill="#9EF2E3")
    draw_text(
        d,
        (330, 302),
        "基于 Dr.GPT 医疗-健康垂直大模型、5000 万+ 医学知识图谱与 MedClaw 多智能体，在临床决策支持和医学科研领域开展可追溯 AI 工作流。",
        font(31, True),
        "#FFFFFF",
        1850,
        line_gap=6,
    )

    # Section 1: What it is.
    rounded(img, (95, 450, 680, 1032), 34, "#FFFFFF", "#D7E2F0", shadow=True)
    d.text((135, 495), "1  先说清：证元芳是什么", font=font(34, True), fill="#0B6D69")
    d.rounded_rectangle((135, 560, 640, 672), 24, fill="#ECF9F6", outline="#BFE7DF", width=2)
    d.text((165, 590), "面向医生 / 医学生的", font=font(27), fill="#3D596D")
    d.text((165, 628), "循证医学 AI 助手", font=font(39, True), fill="#08736F")

    what_points = [
        ("问即有据", "每个答案附医学文献或指南来源"),
        ("不是替代医生", "定位是查证、解释、科研与学习助手"),
        ("从 1.0 到 2.0", "从循证问答扩展到论文、方案、备考、图像与科普"),
    ]
    y = 720
    for title, body in what_points:
        d.ellipse((145, y + 6, 165, y + 26), fill="#12A594")
        d.text((182, y), title, font=font(26, True), fill="#172B4D")
        draw_text(d, (182, y + 36), body, font(22), "#647789", 420, line_gap=6)
        y += 98

    # Section 2: Technology.
    rounded(img, (770, 450, 1590, 1032), 34, "#FFFFFF", "#D7E2F0", shadow=True)
    d.text((810, 495), "2  技术能力：把“可用”变成“可信”", font=font(34, True), fill="#315C9A")
    tech_cards = [
        ("Dr.GPT", "医学语义理解、临床推理、内容生成"),
        ("5000 万+ 知识图谱", "PubMed + 中文在线 + 卫和三源融合"),
        ("MedClaw + DeepResearch", "任务拆解、深度检索、权威评估、引用验证"),
    ]
    y = 565
    for idx, (title, body) in enumerate(tech_cards):
        d.rounded_rectangle((825, y, 1535, y + 98), 20, fill="#F2F6FC", outline="#CFE0F2", width=2)
        d.text((855, y + 15), title, font=font(28, True), fill="#243B59")
        d.text((855, y + 57), body, font=font(23), fill="#5D7084")
        if idx < len(tech_cards) - 1:
            d.line((1180, y + 106, 1180, y + 132), fill="#9DB2CC", width=5)
            d.polygon([(1180, y + 142), (1166, y + 118), (1194, y + 118)], fill="#9DB2CC")
        y += 136
    d.rounded_rectangle((825, 928, 1535, 986), 18, fill="#EAF4FF", outline="#CFE0F2", width=2)
    d.text((855, 945), "能力背书：MedClaw 测评 13/13 通过", font=font(24, True), fill="#315C9A")
    d.text((1360, 945), "2000+ Skills", font=font(24, True), fill="#08736F")

    # Section 3: Growth funnel.
    rounded(img, (1680, 450, 2305, 1032), 34, "#FFFFFF", "#D7E2F0", shadow=True)
    d.text((1720, 495), "3  作用到产品增长漏斗", font=font(34, True), fill="#B4541A")
    funnel = [
        ("触达 / 注册", "价值一句话可理解：医生知道它能解决查证、科研、患教痛点", "#E8F6F3", "#08736F", None),
        ("注册 → 认证", "权威测评 + 文献来源 + 可追溯回答，降低专业信任门槛", "#FFF3E8", "#E36B2C", "+10%"),
        ("持续使用 / 留存", "诊前、诊中、诊后 + 论文/方案/备考，形成高频工作流", "#EDF2FF", "#315C9A", "+15%"),
    ]
    y = 568
    for i, (title, body, fill, color, metric) in enumerate(funnel):
        x = 1730
        w = 520
        h = 104
        d.rounded_rectangle((x, y, x + w, y + h), 20, fill=fill, outline="#D8E2F0", width=2)
        d.text((x + 26, y + 17), title, font=font(27, True), fill=color)
        body_width = 305 if metric else w - 52
        draw_text(d, (x + 26, y + 52), body, font(20), "#4F6478", body_width, line_gap=5)
        if metric:
            inline_metric(d, (x + 366, y + 18, x + 500, y + 88), metric, color)
        if i < len(funnel) - 1:
            d.polygon([(1990, y + 128), (1968, y + 104), (2012, y + 104)], fill="#B5C3D4")
        y += 145

    d.rounded_rectangle((1730, 964, 2250, 1005), 18, fill="#F7F9FC", outline="#D8E2F0", width=1)
    d.text((1756, 975), "结果口径：注册-认证转化 +10%；留存率 +15%", font=font(20, True), fill="#B4541A")

    # Arrows from definition -> tech -> funnel.
    arrow(d, (697, 742), (750, 742), "#9AAEC8", width=8)
    arrow(d, (1608, 742), (1662, 742), "#9AAEC8", width=8)

    # Bottom evidence strip.
    d.text((110, 1125), "可引用数据与边界", font=font(32, True), fill="#172B4D")
    evidence = [
        ("2000+ Skills", "临床、公卫、影像、检验、医院管理等"),
        ("13/13", "MedClaw 能力测评通过"),
        ("69,615 人", "赋能医路轻松医学专业人士"),
        ("百家重点医院", "护理记录 / 病历核对 / 患者宣教等场景"),
    ]
    x = 390
    for value, label in evidence:
        d.rounded_rectangle((x, 1090, x + 410, 1215), 24, fill="#FFFFFF", outline="#D7E2F0", width=2)
        d.text((x + 28, 1112), value, font=font(34, True), fill="#08736F")
        draw_text(d, (x + 28, 1160), label, font(20), "#5C6F83", 345, line_gap=5)
        x += 450

    d.text(
        (110, 1276),
        "注：+10% / +15% 为本次指定业务效果指标；产品定义、技术能力和背书数据来自产品真源库。CMB 满分与肿瘤 SOTA 归属 Dr.GPT 模型层，证元芳仅作为承载产品借用。",
        font=font(21),
        fill="#6B7C8F",
    )

    img.convert("RGB").save(PNG_OUT, quality=95)
    # Keep legacy path refreshed only if it does not exist; users may still compare the old file.
    if not LEGACY_OUT.exists():
        img.convert("RGB").save(LEGACY_OUT, quality=95)
    print(PNG_OUT)


if __name__ == "__main__":
    main()
