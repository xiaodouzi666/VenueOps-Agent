from __future__ import annotations

import shutil
import subprocess
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFont

try:
    import imageio_ffmpeg
except ImportError as exc:  # pragma: no cover - local artifact helper
    raise SystemExit("Install imageio-ffmpeg first: python3 -m pip install imageio-ffmpeg") from exc


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs" / "demo_assets"
SLIDES = ASSETS / "generated_slides"
VIDEO = ASSETS / "venueops_demo.mp4"
NARRATION_TXT = ASSETS / "venueops_demo_narration.txt"
NARRATION_AUDIO = ASSETS / "venueops_demo_narration.aiff"
CONCAT = ASSETS / "venueops_demo_concat.txt"
SIZE = (1280, 720)

NARRATION = """VenueOps Agent is an operations copilot for large retail and event venues.
During a peak event, operators are watching crowd density, queues, inventory, incidents, and staffing at the same time.
The goal is not another chat dashboard. The goal is an agent that can inspect live operational data, retrieve the right procedures, and create safe actions that a human can approve.

The demo starts in the command center for NorthBridge Stadium and Retail Plaza.
MongoDB holds the venue, event, telemetry, tenants, inventory, staff shifts, incidents, actions, audit events, SOP documents, and agent run memory.
The heatmap makes the first problem visible immediately: Gate B is under critical pressure, with an eighteen minute wait and a large staffing gap.

Next, the demo reset and crowd surge controls reproduce the scenario.
The API writes the surge into operational telemetry, and the dashboard updates the risk model.
This is deterministic for judging, but the same repository can switch to MongoDB Atlas, MongoDB MCP Server, and Vertex AI Gemini when the required secrets are configured.

When the mission runs, the agent follows an observe, analyze, retrieve, plan, confirm loop.
It inspects MongoDB collection schema, aggregates telemetry, finds inventory and staff data, counts incidents, retrieves SOP guidance, and creates five pending actions.
The tool trace is exposed in the product so the operator can see exactly which MongoDB-shaped calls and controlled business tools were used.

The action plan is operational, not just descriptive.
It proposes moving four trained stewards from Retail Wing East to Gate B, drafting a signage redirect to Gate D, restocking Water 500ml, assigning a facility team to Restroom 2F West, and drafting a tenant campaign to pull optional traffic toward Retail Wing East.
Every meaningful action is created as pending approval.

The operator approves the staff dispatch and water restock, and rejects the signage instruction.
The application writes execution effects and audit events back to MongoDB.
Gate B staffing improves, water stock recovers, the before and after KPI shows pressure and wait time dropping, and each action card shows the audit trail.

The architecture page summarizes the build.
Cloud Run deployment assets are included, Gemini integration is implemented behind configuration, MongoDB Atlas is the production data store, MongoDB Search and Vector Search-ready SOP retrieval is included, and MongoDB MCP access is represented in the trace with a real MCP stdio path plus deterministic local fallback.
VenueOps Agent is a controlled operations loop: observe with MongoDB, reason with Gemini, retrieve procedures, propose actions, require human approval, execute safely, and preserve audit memory."""

SLIDE_PLAN = [
    ("slide_01_problem.png", "01_command_center.png", None, 18, "Problem", "Peak venues need an agent that turns live operations data into safe actions."),
    ("slide_02_command_center.png", "01_command_center.png", None, 24, "Command Center", "Crowd, queue, inventory, incidents, staff, KPIs, and heatmap in one operational surface."),
    ("slide_03_crowd_surge.png", "02_crowd_surge.png", None, 24, "Reproducible Scenario", "Demo reset and crowd surge produce a critical Gate B risk from live telemetry."),
    ("slide_04_agent_plan.png", "03_agent_plan.png", (0, 760, 1280, 1480), 32, "Agent Plan", "The agent creates five pending actions with rationale, evidence, and expected impact."),
    ("slide_05_tool_trace.png", "06_tool_trace_full.png", (760, 2200, 1280, 2920), 28, "MongoDB Tool Trace", "Schema, aggregate, find, count, SOP retrieval, and controlled action writes stay visible."),
    ("slide_06_audit_kpis.png", "04_audit_kpis.png", (0, 760, 1280, 1480), 34, "Human Approval", "Approved and rejected actions update status, audit trail, stock, staffing, pressure, and wait KPIs."),
    ("slide_07_architecture.png", "05_architecture_docs.png", None, 20, "Architecture", "Cloud Run-ready app, Gemini hook, MongoDB Atlas data model, MCP trace, and SOP retrieval."),
]


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def cover_crop(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    src_ratio = image.width / image.height
    dst_ratio = size[0] / size[1]
    if src_ratio > dst_ratio:
        new_width = int(image.height * dst_ratio)
        left = (image.width - new_width) // 2
        image = image.crop((left, 0, left + new_width, image.height))
    else:
        new_height = int(image.width / dst_ratio)
        top = (image.height - new_height) // 2
        image = image.crop((0, top, image.width, top + new_height))
    return image.resize(size, Image.Resampling.LANCZOS)


def draw_caption(slide: Image.Image, label: str, text: str) -> None:
    draw = ImageDraw.Draw(slide, "RGBA")
    title_font = load_font(46, bold=True)
    body_font = load_font(26)
    label_font = load_font(18, bold=True)
    draw.rounded_rectangle((34, 34, 760, 182), radius=18, fill=(12, 28, 32, 214))
    draw.text((60, 55), label.upper(), fill=(157, 220, 210, 255), font=label_font)
    draw.text((58, 84), label, fill=(255, 252, 244, 255), font=title_font)
    wrapped = "\n".join(textwrap.wrap(text, 62))
    draw.rounded_rectangle((34, 542, 1246, 686), radius=18, fill=(12, 28, 32, 224))
    draw.text((60, 570), wrapped, fill=(255, 252, 244, 255), font=body_font, spacing=7)


def make_slide(output: Path, source: Path, crop: tuple[int, int, int, int] | None, label: str, text: str) -> None:
    image = Image.open(source).convert("RGB")
    if crop:
        image = image.crop(crop)
    base = cover_crop(image, SIZE)
    base = ImageEnhance.Brightness(base).enhance(0.78)
    overlay = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    base = Image.alpha_composite(base.convert("RGBA"), overlay)
    draw_caption(base, label, text)
    base.convert("RGB").save(output, quality=94)


def build_slides() -> list[tuple[Path, int]]:
    SLIDES.mkdir(parents=True, exist_ok=True)
    rendered: list[tuple[Path, int]] = []
    for output_name, source_name, crop, duration, label, text in SLIDE_PLAN:
        output = SLIDES / output_name
        make_slide(output, ASSETS / source_name, crop, label, text)
        rendered.append((output, duration))
    return rendered


def build_audio() -> None:
    NARRATION_TXT.write_text(NARRATION, encoding="utf-8")
    say = shutil.which("say")
    if not say:
        raise SystemExit("macOS say command is required to build narration audio.")
    subprocess.run(
        [say, "-v", "Alex", "-r", "148", "-o", str(NARRATION_AUDIO), "-f", str(NARRATION_TXT)],
        check=True,
    )


def build_video(slides: list[tuple[Path, int]]) -> None:
    with CONCAT.open("w", encoding="utf-8") as handle:
        for slide, duration in slides:
            handle.write(f"file '{slide.as_posix()}'\n")
            handle.write(f"duration {duration}\n")
        handle.write(f"file '{slides[-1][0].as_posix()}'\n")
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(CONCAT),
            "-i",
            str(NARRATION_AUDIO),
            "-vf",
            "fps=30,format=yuv420p",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "24",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-t",
            "180",
            "-movflags",
            "+faststart",
            str(VIDEO),
        ],
        check=True,
    )


def main() -> None:
    slides = build_slides()
    build_audio()
    build_video(slides)
    print(VIDEO)


if __name__ == "__main__":
    main()
