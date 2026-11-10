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
    render_athena()
    render_cross_engine()
    render_ai_failures()

