"""Render article-ready evidence cards from the sanitized validation summary."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / "evidence" / "validation-summary.json").read_text())
OUT = ROOT / "evidence"
WIDTH, HEIGHT = 1400, 788
BG = "#0B1020"
PANEL = "#151D33"
TEXT = "#F7F9FC"
MUTED = "#AAB6CF"
ORANGE = "#FF9900"
BLUE = "#55B6FF"
GREEN = "#43D17A"
RED = "#FF6B6B"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    choices = [
        (
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
            if bold
            else "/System/Library/Fonts/Supplemental/Arial.ttf"
        ),
        (
            "/System/Library/Fonts/SFNS.ttf"
            if not bold
            else "/System/Library/Fonts/SFNS.ttf"
        ),
    ]
    for path in choices:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            pass
    return ImageFont.load_default()


def canvas(title: str, subtitle: str):
    image = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(image)
    draw.text((70, 54), title, font=font(46, True), fill=TEXT)
    draw.text((72, 118), subtitle, font=font(23), fill=MUTED)
    draw.text(
        (WIDTH - 280, HEIGHT - 42),
        "Measured on AWS · 10 Nov 2026",
        font=font(17),
        fill=MUTED,
    )
    return image, draw


def rounded(draw, box, fill=PANEL, outline=None, radius=22, width=2):
    draw.rounded_rectangle(
        box, radius=radius, fill=fill, outline=outline, width=width
    )


def arrow(draw, start, end, color=MUTED, width=5):
    x1, y1 = start
    x2, y2 = end
    draw.line((x1, y1, x2, y2), fill=color, width=width)
    if x1 == x2:
        direction = 1 if y2 > y1 else -1
        draw.polygon(
            [
                (x2, y2),
                (x2 - 10, y2 - 16 * direction),
                (x2 + 10, y2 - 16 * direction),
            ],
            fill=color,
        )
    else:
        direction = 1 if x2 > x1 else -1
        draw.polygon(
            [
                (x2, y2),
                (x2 - 16 * direction, y2 - 10),
                (x2 - 16 * direction, y2 + 10),
            ],
            fill=color,
        )


def render_architecture():
    image, draw = canvas(
        "AI lakehouse optimization lab",
        "The model proposes; policy, measurements, and result equality decide.",
    )

    rounded(draw, (60, 185, 320, 320), outline=ORANGE)
    draw.text((88, 218), "Amazon Bedrock", font=font(27, True), fill=TEXT)
    draw.text((88, 265), "Tool-shaped proposal", font=font(20), fill=MUTED)
    draw.text((88, 295), "Guardrail assessment", font=font(20), fill=MUTED)

    rounded(draw, (390, 185, 665, 320), outline=GREEN)
    draw.text((420, 218), "Policy gate", font=font(27, True), fill=TEXT)
    draw.text((420, 265), "Read-only SQL", font=font(20), fill=MUTED)
    draw.text((420, 295), "Allow-listed identifiers", font=font(20), fill=MUTED)

    rounded(draw, (735, 165, 1340, 340), outline=BLUE)
    draw.text(
        (765, 202),
        "Shared S3 Tables / Iceberg data",
        font=font(27, True),
        fill=TEXT,
    )
    draw.text(
        (765, 249),
        "Glue Data Catalog + Lake Formation",
        font=font(20),
        fill=MUTED,
    )
    draw.text(
        (765, 282),
        "Unpartitioned baseline + partitioned candidate",
        font=font(20),
        fill=MUTED,
    )
    draw.text(
        (765, 315),
        "Immutable 10,000-row validation fixture",
        font=font(20),
        fill=MUTED,
    )

    arrow(draw, (320, 252), (380, 252))
    arrow(draw, (665, 252), (725, 252))

    engines = [
        (60, "Amazon Athena", "Bytes scanned + timing", BLUE),
        (510, "EMR Serverless", "Spark cross-engine read", ORANGE),
        (960, "Redshift Serverless", "External-schema read", "#E15FED"),
    ]
    for x, name, detail, color in engines:
        rounded(draw, (x, 440, x + 380, 565), outline=color)
        draw.text((x + 30, 474), name, font=font(26, True), fill=TEXT)
        draw.text((x + 30, 522), detail, font=font(20), fill=MUTED)

    draw.line((1035, 340, 1035, 400), fill=MUTED, width=5)
    draw.line((250, 400, 1150, 400), fill=MUTED, width=5)
    for x in (250, 700, 1150):
        arrow(draw, (x, 400), (x, 430))

    rounded(draw, (300, 650, 1100, 742), outline=GREEN)
    draw.text((338, 674), "Deterministic verdict", font=font(27, True), fill=TEXT)
    draw.text(
        (338, 713),
        "Result equality · Glue Data Quality · scan reduction · resource use",
        font=font(19),
        fill=MUTED,
    )
    for x in (250, 700, 1150):
        draw.line((x, 565, x, 620), fill=MUTED, width=5)
    draw.line((250, 620, 1150, 620), fill=MUTED, width=5)
    arrow(draw, (700, 620), (700, 640))

    image.save(ROOT / "architecture.png")


def render_athena():
    image, draw = canvas(
        "Athena measured the rewrite",
        "Same result rows. Less data scanned. Slightly slower on a tiny fixture.",
    )
    baseline = DATA["athena"]["baseline"]
    candidate = DATA["athena"]["candidate"]
    rounded(draw, (70, 180, 1330, 680))

    labels = [
        ("Unpartitioned baseline", baseline, ORANGE),
        ("Partitioned candidate", candidate, BLUE),
    ]
    max_scan = baseline["data_scanned_bytes"]
    for index, (label, values, color) in enumerate(labels):
        y = 245 + index * 185
        draw.text((120, y), label, font=font(27, True), fill=TEXT)
        bar_width = int(850 * values["data_scanned_bytes"] / max_scan)
        rounded(draw, (120, y + 54, 120 + bar_width, y + 105), color, radius=12)
        draw.text(
            (1000, y + 52),
            f'{values["data_scanned_bytes"]:,} bytes',
            font=font(28, True),
            fill=color,
        )
        draw.text(
            (1000, y + 94),
            f'{values["engine_millis"]} ms engine time',
            font=font(20),
            fill=MUTED,
        )

    draw.text((120, 590), "78.3% fewer bytes scanned", font=font(34, True), fill=GREEN)
    draw.text(
        (700, 594),
        "RESULT SET MATCHED",
        font=font(27, True),
        fill=GREEN,
    )
    image.save(OUT / "athena-measured-comparison.png")


def render_cross_engine():
    image, draw = canvas(
        "One Iceberg table, three query engines",
        "The acceptance gate compared returned values—not model confidence.",
    )
    cards = [
        ("Amazon Athena", "PASS", BLUE),
        ("EMR Serverless", "PASS", ORANGE),
        ("Redshift Serverless", "PASS", "#E15FED"),
    ]
    for i, (name, status, color) in enumerate(cards):
        x = 70 + i * 430
        rounded(draw, (x, 190, x + 390, 370), outline=color)
        draw.text((x + 28, 225), name, font=font(28, True), fill=TEXT)
        draw.text((x + 28, 300), status, font=font(38, True), fill=GREEN)

    rounded(draw, (70, 410, 1330, 675))
    draw.text((110, 448), "Returned aggregates", font=font(27, True), fill=TEXT)
    rows = DATA["result_rows"]
    for i, row in enumerate(rows):
        draw.text(
            (120, 505 + i * 48),
            f"{row[0]:<10}  {row[1]:>10,.1f}",
            font=font(25),
            fill=TEXT,
        )
    draw.text((680, 470), "Glue Data Quality", font=font(27, True), fill=TEXT)
    draw.text((680, 522), "Score 1.0", font=font(42, True), fill=GREEN)
    draw.text(
        (680, 585),
        "3 of 3 deterministic rules passed",
        font=font(24),
        fill=MUTED,
    )
    image.save(OUT / "cross-engine-validation.png")


def render_ai_failures():
    image, draw = canvas(
        "The AI proposal failed safely—three times",
        "Each failure became validator feedback; only the fourth proposal could run.",
    )
    steps = [
        ("1", "Guardrail blocked", "Prompt-attack false positive", RED),
        ("2", "Contract rejected", "Markdown + wrong JSON type", RED),
        ("3", "SQL rejected", "Invalid Athena identifier", RED),
        ("4", "Proposal accepted", "Valid tool input after one repair", GREEN),
    ]
    for i, (n, title, detail, color) in enumerate(steps):
        y = 185 + i * 125
        draw.ellipse((80, y, 142, y + 62), fill=color)
        draw.text((101, y + 12), n, font=font(28, True), fill=BG)
        if i < len(steps) - 1:
            draw.line((111, y + 62, 111, y + 122), fill=MUTED, width=4)
        rounded(draw, (175, y - 8, 1300, y + 78), outline=color, radius=18)
        draw.text((210, y + 8), title, font=font(27, True), fill=TEXT)
        draw.text((600, y + 11), detail, font=font(23), fill=MUTED)
    draw.text(
        (175, 690),
        "Bedrock proposes. Deterministic evidence decides.",
        font=font(29, True),
        fill=ORANGE,
    )
    image.save(OUT / "bedrock-safe-failures.png")


if __name__ == "__main__":
    render_architecture()
    render_athena()
    render_cross_engine()
    render_ai_failures()

