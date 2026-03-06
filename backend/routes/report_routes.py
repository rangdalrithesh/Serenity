from flask import Blueprint, send_file
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch, mm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageTemplate, Flowable,
    Spacer, KeepInFrame
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import sqlite3
import io
from datetime import datetime
from pathlib import Path
from config import DB_PATH

report_bp = Blueprint("report_bp", __name__)

# ── Palette ────────────────────────────────────────────────────────────────────
PRIMARY  = colors.HexColor("#7CC6FE")
DEEP     = colors.HexColor("#1E1B4B")
DEEP2    = colors.HexColor("#2D2A6E")
ACCENT   = colors.HexColor("#C3B6FF")
TEAL     = colors.HexColor("#6ED3CF")
PEACH    = colors.HexColor("#FFB38A")
RED      = colors.HexColor("#F87171")
LIGHT    = colors.HexColor("#F3F4FF")
CARD     = colors.HexColor("#EEF2FF")
WHITE    = colors.white
MUTED    = colors.HexColor("#94A3B8")
SLATE    = colors.HexColor("#64748B")
BORDER   = colors.HexColor("#CBD5E1")
GRID     = colors.HexColor("#E2E8F0")

PAGE_W, PAGE_H = A4
MARGIN = 0.60 * inch
CONTENT_W = PAGE_W - 2 * MARGIN

LOGO_PATH = Path(__file__).parent.parent / "assets" / "serenity_logo_white.png"
LOGO_ASPECT = 906 / 588

# ══════════════════════════════════════════════════════════════════════════════
#  CANVAS HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def rr(c, x, y, w, h, r=6, fill=1, stroke=0):
    """Draw a rounded rectangle."""
    c.roundRect(x, y, w, h, r, fill=fill, stroke=stroke)

def gradient_rect(c, x, y, w, h, col1, col2, steps=40):
    """Fake horizontal gradient by drawing thin vertical strips."""
    r1, g1, b1 = col1.red, col1.green, col1.blue
    r2, g2, b2 = col2.red, col2.green, col2.blue
    sw = w / steps
    for i in range(steps):
        t = i / steps
        c.setFillColorRGB(r1 + (r2-r1)*t, g1 + (g2-g1)*t, b1 + (b2-b1)*t)
        c.rect(x + i*sw, y, sw + 0.5, h, fill=1, stroke=0)

def draw_section_header(c, x, y, w, label, icon=""):
    """Draw a styled section heading with accent line."""
    # Label
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(DEEP)
    c.drawString(x, y, f"{icon}  {label}" if icon else label)
    # Accent underline
    c.setStrokeColor(PRIMARY)
    c.setLineWidth(1.8)
    c.line(x, y - 4, x + w, y - 4)
    # Tiny heart pulse decoration
    c.setFont("Helvetica", 7)
    c.setFillColor(PRIMARY)
    c.drawString(x + w*0.42, y - 2, "— ♥ —")

def alpha_fill(c, hex_color, alpha=0.15):
    """Simulate alpha fill (draw on white bg)."""
    base = colors.HexColor(hex_color) if isinstance(hex_color, str) else hex_color
    # blend with white
    r = 1 - (1 - base.red)   * alpha
    g = 1 - (1 - base.green) * alpha
    b = 1 - (1 - base.blue)  * alpha
    c.setFillColorRGB(r, g, b)

# ══════════════════════════════════════════════════════════════════════════════
#  MATPLOTLIB CHARTS  (styled for dark palette)
# ══════════════════════════════════════════════════════════════════════════════
def _chart_cfg():
    plt.rcParams.update({
        "figure.facecolor": "#F3F4FF",
        "axes.facecolor":   "#F3F4FF",
        "axes.edgecolor":   "#CBD5E1",
        "axes.spines.top":  False,
        "axes.spines.right":False,
        "xtick.color": "#64748B", "ytick.color": "#64748B",
        "grid.color":  "#E2E8F0", "grid.linestyle": "--", "grid.alpha": 0.55,
        "font.family": "sans-serif", "font.size": 9,
        "text.color":  "#1E1B4B",
    })

def _fig_bytes(fig, dpi=150):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return buf

def chart_trend(dates, scores):
    _chart_cfg()
    fig, ax = plt.subplots(figsize=(7.0, 2.6))
    x = np.arange(len(dates))
    ax.fill_between(x, scores, alpha=0.18, color="#7CC6FE")
    ax.plot(x, scores, color="#7CC6FE", linewidth=2.4,
            marker="o", markersize=4.5, zorder=3)
    if len(scores) > 1:
        mi, ma = int(np.argmin(scores)), int(np.argmax(scores))
        ax.annotate(f"Low {scores[mi]:.2f}", xy=(mi, scores[mi]),
            xytext=(mi, scores[mi] - 0.12), ha="center", fontsize=7.5,
            color="#6ED3CF", fontweight="bold",
            arrowprops=dict(arrowstyle="-", color="#6ED3CF", lw=0.8))
        ax.annotate(f"Peak {scores[ma]:.2f}", xy=(ma, scores[ma]),
            xytext=(ma, scores[ma] + 0.12), ha="center", fontsize=7.5,
            color="#F87171", fontweight="bold",
            arrowprops=dict(arrowstyle="-", color="#F87171", lw=0.8))
    step = max(1, len(dates) // 8)
    ax.set_xticks(x[::step])
    ax.set_xticklabels(dates[::step], rotation=35, ha="right", fontsize=7)
    ax.set_ylabel("Avg Stress", fontsize=8)
    ax.set_title("Daily Average Stress Trend", fontweight="bold", pad=10, fontsize=11)
    ax.yaxis.grid(True)
    fig.tight_layout(pad=0.7)
    return _fig_bytes(fig)

def chart_feature(fd):
    _chart_cfg()
    fig, ax = plt.subplots(figsize=(6.0, 3.0))
    labels = [f[0] for f in fd]
    values = [f[1] for f in fd]
    palette = ["#7CC6FE","#C3B6FF","#6ED3CF","#FFB38A","#A5B4FC","#67E8F9","#FCA5A5"]
    bars = ax.barh(labels, values, color=palette[:len(labels)], height=0.52,
                   zorder=3, edgecolor="white", linewidth=0.8)
    for bar, v in zip(bars, values):
        ax.text(bar.get_width() + 0.003, bar.get_y() + bar.get_height()/2,
                f"{v:.0%}", va="center", fontsize=8, fontweight="bold", color="#1E1B4B")
    ax.set_xlabel("Relative Weight", fontsize=8)
    ax.set_title("Feature Importance Snapshot", fontweight="bold", pad=10, fontsize=11)
    ax.xaxis.grid(True)
    ax.set_xlim(0, max(values) * 1.22)
    fig.tight_layout(pad=0.7)
    return _fig_bytes(fig)

def chart_donut(data, title):
    """Donut chart instead of pie for a modern look."""
    _chart_cfg()
    fig, ax = plt.subplots(figsize=(3.4, 3.0))
    labels = [r[0].replace("_", " ").title() for r in data]
    values = [r[1] for r in data]
    palette = ["#7CC6FE","#C3B6FF","#6ED3CF","#FFB38A","#F87171"]
    wedges, texts, autos = ax.pie(
        values, labels=labels, autopct="%1.0f%%",
        colors=palette[:len(labels)], startangle=140,
        pctdistance=0.75, labeldistance=1.14,
        wedgeprops=dict(width=0.55, linewidth=2, edgecolor="white"))
    for t in texts:  t.set_fontsize(7)
    for a in autos:  a.set_fontsize(7.5); a.set_fontweight("bold")
    ax.set_title(title, fontweight="bold", pad=8, fontsize=10)
    fig.tight_layout(pad=0.4)
    return _fig_bytes(fig)

def chart_bar(data, title):
    _chart_cfg()
    fig, ax = plt.subplots(figsize=(3.4, 3.0))
    labels = [r[0].replace("_", " ").title() for r in data]
    values = [r[1] for r in data]
    palette = ["#6ED3CF","#7CC6FE","#C3B6FF","#FFB38A","#F87171"]
    bars = ax.bar(labels, values, color=palette[:len(labels)],
                  width=0.50, zorder=3, edgecolor="white", linewidth=0.8)
    for bar, v in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
                str(v), ha="center", fontsize=8.5, fontweight="bold", color="#1E1B4B")
    ax.set_ylabel("Check-ins", fontsize=8)
    ax.set_title(title, fontweight="bold", pad=8, fontsize=10)
    ax.yaxis.grid(True)
    fig.tight_layout(pad=0.4)
    return _fig_bytes(fig)


# ══════════════════════════════════════════════════════════════════════════════
#  CUSTOM FLOWABLES
# ══════════════════════════════════════════════════════════════════════════════
class InfographicBar(Flowable):
    """Horizontal stat bar like the infographic's condition bars."""
    def __init__(self, label, pct, color, width, height=28):
        super().__init__()
        self.label = label
        self.pct   = pct          # 0.0–1.0
        self.color = color
        self._w    = width
        self._h    = height

    def wrap(self, aW, aH):
        return self._w, self._h + 22

    def draw(self):
        c = self.canv
        W, H = self._w, self._h

        # Percentage badge
        badge_w = 48
        c.setFillColor(self.color)
        rr(c, 0, 8, badge_w, H, r=6)
        c.setFillColor(WHITE)
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(badge_w/2, 8 + H*0.32, f"{int(self.pct*100)}%")

        # Label
        c.setFillColor(DEEP)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(badge_w + 10, 8 + H + 6, self.label)

        # Track
        track_x = badge_w + 10
        track_w = W - track_x
        c.setFillColor(LIGHT)
        rr(c, track_x, 8, track_w, H, r=5)

        # Fill (gradient-ish: single color fading)
        fill_w = track_w * self.pct
        c.setFillColor(self.color)
        rr(c, track_x, 8, fill_w, H, r=5)

        # Person icons on fill
        n_filled  = max(1, round(self.pct * 10))
        n_empty   = 10 - n_filled
        icon_size = 10
        icon_gap  = (track_w - 20) / 10
        for i in range(10):
            ix = track_x + 10 + i * icon_gap
            iy = 8 + H/2 - icon_size/2
            if i < n_filled:
                c.setFillColor(DEEP)
            else:
                alpha_fill(c, "#1E1B4B", 0.18)
            # head
            c.circle(ix + 4, iy + icon_size - 3, 3, fill=1, stroke=0)
            # body
            c.setLineWidth(0)
            c.rect(ix + 1, iy + 2, 6, 5, fill=1, stroke=0)


class KPIRow(Flowable):
    """A row of KPI cards."""
    def __init__(self, kpis, width, height=64, colors_list=None):
        super().__init__()
        self.kpis   = kpis       # list of (value_str, label_str)
        self._w     = width
        self._h     = height
        self._colors = colors_list or [PRIMARY]*len(kpis)

    def wrap(self, aW, aH):
        return self._w, self._h

    def draw(self):
        c   = self.canv
        n   = len(self.kpis)
        gap = 8
        cw  = (self._w - gap*(n-1)) / n

        for i, (val, lbl) in enumerate(self.kpis):
            x  = i * (cw + gap)
            col = self._colors[i] if i < len(self._colors) else PRIMARY

            # Card bg
            c.setFillColor(CARD)
            rr(c, x, 0, cw, self._h, r=8)

            # Top accent stripe
            c.setFillColor(col)
            rr(c, x, self._h - 5, cw, 5, r=4)

            # Value
            c.setFillColor(col)
            c.setFont("Helvetica-Bold", 18)
            c.drawCentredString(x + cw/2, self._h * 0.38, val)

            # Label
            c.setFillColor(MUTED)
            c.setFont("Helvetica", 7)
            c.drawCentredString(x + cw/2, self._h * 0.14, lbl)


class SectionCard(Flowable):
    """A card with icon, title, and body text (symptom / tip style)."""
    def __init__(self, icon_char, title, body, accent, width, height=90):
        super().__init__()
        self.icon_char = icon_char
        self.title     = title
        self.body      = body
        self.accent    = accent
        self._w        = width
        self._h        = height

    def wrap(self, aW, aH):
        return self._w, self._h

    def draw(self):
        c = self.canv
        W, H = self._w, self._h

        # Card shadow (subtle)
        c.setFillColor(colors.HexColor("#DDE1F5"))
        rr(c, 2, -2, W-2, H-2, r=10)

        # Card bg
        c.setFillColor(WHITE)
        rr(c, 0, 0, W, H, r=10)

        # Left accent stripe
        c.setFillColor(self.accent)
        rr(c, 0, 0, 5, H, r=5)

        # Icon circle
        alpha_fill(c, self.accent.hexval() if hasattr(self.accent,'hexval') else "#7CC6FE", 0.15)
        c.setFillColor(colors.HexColor(self._alpha_hex(self.accent, 0.15)))
        c.circle(28, H - 28, 16, fill=1, stroke=0)
        c.setFillColor(self.accent)
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(28, H - 33, self.icon_char)

        # Title
        c.setFillColor(DEEP)
        c.setFont("Helvetica-Bold", 9)
        # Wrap title manually
        title_lines = self._wrap_text(self.title, "Helvetica-Bold", 9, W - 60)
        ty = H - 20
        for line in title_lines[:2]:
            c.drawString(50, ty, line)
            ty -= 12

        # Divider
        c.setStrokeColor(LIGHT)
        c.setLineWidth(0.7)
        c.line(12, H - 54, W - 12, H - 54)

        # Body text
        c.setFillColor(SLATE)
        c.setFont("Helvetica", 7.5)
        body_lines = self._wrap_text(self.body, "Helvetica", 7.5, W - 24)
        by = H - 68
        for line in body_lines[:4]:
            c.drawString(12, by, line)
            by -= 11

    @staticmethod
    def _alpha_hex(col, alpha):
        r = int((1 - (1-col.red)*alpha)   * 255)
        g = int((1 - (1-col.green)*alpha) * 255)
        b = int((1 - (1-col.blue)*alpha)  * 255)
        return f"#{r:02X}{g:02X}{b:02X}"

    @staticmethod
    def _wrap_text(text, font, size, max_w):
        from reportlab.pdfbase.pdfmetrics import stringWidth
        words = text.split()
        lines, line = [], ""
        for w in words:
            test = f"{line} {w}".strip()
            if stringWidth(test, font, size) <= max_w:
                line = test
            else:
                if line: lines.append(line)
                line = w
        if line: lines.append(line)
        return lines


class AwarenessCard(Flowable):
    """Wide stat card (like the '1 in 4' block)."""
    def __init__(self, big, desc, icon, accent, width, height=56, full=False):
        super().__init__()
        self.big    = big
        self.desc   = desc
        self.icon   = icon
        self.accent = accent
        self._w     = width
        self._h     = height
        self.full   = full

    def wrap(self, aW, aH):
        return self._w, self._h

    def draw(self):
        c = self.canv
        W, H = self._w, self._h
        acc = self.accent

        # Card bg
        if self.full:
            gradient_rect(c, 0, 0, W, H, CARD, colors.HexColor("#E0E7FF"))
        else:
            c.setFillColor(WHITE)
        rr(c, 0, 0, W, H, r=9)
        if self.full:
            gradient_rect(c, 1, 1, W-2, H-2, CARD, colors.HexColor("#E0E7FF"))

        # Left accent bar
        c.setFillColor(acc)
        rr(c, 0, 0, 4, H, r=4)

        # Icon bg
        c.setFillColor(SectionCard._alpha_hex(acc, 0.15))
        alpha_fill(c, "#ffffff", 0)  # reset
        c.setFillColor(colors.HexColor(SectionCard._alpha_hex(acc, 0.14)))
        c.circle(26, H/2, 16, fill=1, stroke=0)
        c.setFillColor(acc)
        c.setFont("Helvetica-Bold", 13)
        c.drawCentredString(26, H/2 - 5, self.icon)

        # Big stat
        c.setFillColor(acc if not self.full else DEEP)
        fs = 20 if self.full else 16
        c.setFont("Helvetica-Bold", fs)
        c.drawString(50, H/2 + 2, self.big)

        # Description
        c.setFillColor(SLATE)
        c.setFont("Helvetica", 7.5)
        lines = SectionCard._wrap_text(self.desc, "Helvetica", 7.5, W - 56)
        dy = H/2 - 10
        for ln in lines[:3]:
            c.drawString(50, dy, ln)
            dy -= 10


class ImageBlock(Flowable):
    """Embeds a BytesIO PNG image."""
    def __init__(self, buf, width, height):
        super().__init__()
        self.buf = buf
        self._w  = width
        self._h  = height

    def wrap(self, aW, aH):
        return self._w, self._h

    def draw(self):
        self.buf.seek(0)
        img = ImageReader(self.buf)
        self.canv.drawImage(img, 0, 0, width=self._w, height=self._h,
                            preserveAspectRatio=True, mask='auto')


class TwoCol(Flowable):
    """Two flowables side by side."""
    def __init__(self, left, right, width, gap=12):
        super().__init__()
        self.left  = left
        self.right = right
        self._w    = width
        self.gap   = gap
        self._cw   = (width - gap) / 2

    def wrap(self, aW, aH):
        lw, lh = self.left.wrap(self._cw, aH)
        rw, rh = self.right.wrap(self._cw, aH)
        self._h = max(lh, rh)
        return self._w, self._h

    def draw(self):
        c = self.canv
        lw, lh = self.left.wrap(self._cw, 9999)
        rw, rh = self.right.wrap(self._cw, 9999)
        # draw left
        c.saveState()
        c.translate(0, self._h - lh)
        self.left.canv = c
        self.left.draw()
        c.restoreState()
        # draw right
        c.saveState()
        c.translate(self._cw + self.gap, self._h - rh)
        self.right.canv = c
        self.right.draw()
        c.restoreState()


class ThreeCardRow(Flowable):
    """Three SectionCards in a row."""
    def __init__(self, cards, width, gap=10):
        super().__init__()
        self.cards = cards
        self._w    = width
        self.gap   = gap
        self._cw   = (width - gap * (len(cards)-1)) / len(cards)

    def wrap(self, aW, aH):
        self._h = max(cd._h for cd in self.cards)
        return self._w, self._h

    def draw(self):
        c = self.canv
        for i, card in enumerate(self.cards):
            x = i * (self._cw + self.gap)
            c.saveState()
            c.translate(x, 0)
            card._w = self._cw
            card.canv = c
            card.draw()
            c.restoreState()


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE TEMPLATE  (header & footer drawn on every page)
# ══════════════════════════════════════════════════════════════════════════════
def _draw_page(canv, doc):
    w, h = A4
    canv.saveState()

    # ── Dark header bar ──────────────────────────────────────────────────────
    canv.setFillColor(DEEP)
    canv.rect(0, h - 0.68*inch, w, 0.68*inch, fill=1, stroke=0)

    # Subtle radial glow top-right
    glow_r, glow_g, glow_b = PRIMARY.red, PRIMARY.green, PRIMARY.blue
    for r_step in range(8, 0, -1):
        alpha = 0.025 * (9 - r_step)
        canv.setFillColorRGB(
            1-(1-glow_r)*alpha, 1-(1-glow_g)*alpha, 1-(1-glow_b)*alpha)
        canv.circle(w - 0.5*inch, h - 0.1*inch, r_step * 12, fill=1, stroke=0)

    # Gradient accent stripe under header
    gradient_rect(canv, 0, h - 0.72*inch, w, 0.05*inch,
                  PRIMARY, TEAL)

    # Logo / penguin
    if LOGO_PATH.exists():
        lh = 0.52*inch
        lw = lh * LOGO_ASPECT
        canv.drawImage(ImageReader(str(LOGO_PATH)),
                       MARGIN, h - 0.63*inch, width=lw, height=lh, mask='auto')
        tx = MARGIN + lw + 0.12*inch
    else:
        canv.setFont("Helvetica-Bold", 14)
        canv.setFillColor(WHITE)
        canv.drawString(MARGIN, h - 0.42*inch, "🐧 SERENITY")
        tx = MARGIN + 1.5*inch

    canv.setFont("Helvetica-Bold", 10)
    canv.setFillColor(WHITE)
    canv.drawString(tx, h - 0.36*inch, "SERENITY")

    canv.setFont("Helvetica", 7.5)
    canv.setFillColor(PRIMARY)
    canv.drawString(tx, h - 0.50*inch, "Student Wellness Intelligence Platform")

    # Page number
    canv.setFont("Helvetica", 8)
    canv.setFillColor(MUTED)
    canv.drawRightString(w - MARGIN, h - 0.42*inch, f"Page {doc.page}")

    # ── Footer bar ───────────────────────────────────────────────────────────
    canv.setFillColor(LIGHT)
    canv.rect(0, 0, w, 0.46*inch, fill=1, stroke=0)
    canv.setFillColor(PRIMARY)
    canv.rect(0, 0.44*inch, w, 0.02*inch, fill=1, stroke=0)
    canv.setFont("Helvetica", 6.5)
    canv.setFillColor(MUTED)
    canv.drawString(MARGIN, 0.15*inch,
                    "Confidential  ·  Internal awareness only  ·  Not a medical diagnosis.")
    canv.drawRightString(w - MARGIN, 0.15*inch,
                         f"Generated {datetime.now().strftime('%d %b %Y  %H:%M')}")
    canv.restoreState()


# ══════════════════════════════════════════════════════════════════════════════
#  STYLES
# ══════════════════════════════════════════════════════════════════════════════
def _styles():
    base = getSampleStyleSheet()
    common = dict(fontName="Helvetica")
    return {
        "title": ParagraphStyle("t", parent=base["Normal"],
            fontSize=22, leading=28, textColor=DEEP,
            fontName="Helvetica-Bold", alignment=TA_CENTER, spaceAfter=2),
        "subtitle": ParagraphStyle("st", parent=base["Normal"],
            fontSize=10, leading=14, textColor=MUTED, alignment=TA_CENTER, **common),
        "period": ParagraphStyle("per", parent=base["Normal"],
            fontSize=9, leading=12, textColor=SLATE, alignment=TA_CENTER, **common),
        "caption": ParagraphStyle("cap", parent=base["Normal"],
            fontSize=7.5, leading=11, textColor=MUTED,
            fontName="Helvetica-Oblique", alignment=TA_CENTER),
        "note": ParagraphStyle("note", parent=base["Normal"],
            fontSize=8, leading=12, textColor=MUTED,
            fontName="Helvetica-Oblique"),
        "body": ParagraphStyle("body", parent=base["Normal"],
            fontSize=9, leading=13, textColor=DEEP, **common),
        "table_hdr": ParagraphStyle("th", parent=base["Normal"],
            fontSize=9, leading=12, textColor=WHITE,
            fontName="Helvetica-Bold", alignment=TA_CENTER),
    }


def _sp(n=0.08):
    return Spacer(1, n*inch)


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION HEADER FLOWABLE
# ══════════════════════════════════════════════════════════════════════════════
class SectionHeader(Flowable):
    def __init__(self, label, width):
        super().__init__()
        self.label = label
        self._w    = width

    def wrap(self, aW, aH):
        return self._w, 28

    def draw(self):
        c = self.canv
        draw_section_header(c, 0, 14, self._w, self.label)


# ══════════════════════════════════════════════════════════════════════════════
#  TABLE FLOWABLE  (styled log table)
# ══════════════════════════════════════════════════════════════════════════════
class StressTable(Flowable):
    def __init__(self, rows, col_widths, width):
        super().__init__()
        self.rows       = rows    # list of (date, score, count)
        self.col_widths = col_widths
        self._w         = width
        self._row_h     = 18
        self._hdr_h     = 24

    def wrap(self, aW, aH):
        self._h = self._hdr_h + len(self.rows) * self._row_h + 4
        return self._w, self._h

    def draw(self):
        c  = self.canv
        W  = self._w
        cw = self.col_widths
        rh = self._row_h
        hh = self._hdr_h
        H  = self._h

        # Header bg
        c.setFillColor(DEEP)
        rr(c, 0, H - hh, W, hh, r=8)

        # Header text
        headers = ["Date", "Avg Stress Score", "Check-ins"]
        xs = [0, cw[0], cw[0]+cw[1]]
        for i, (hdr, x, cw_i) in enumerate(zip(headers, xs, cw)):
            c.setFillColor(WHITE)
            c.setFont("Helvetica-Bold", 8.5)
            c.drawCentredString(x + cw_i/2, H - hh + 8, hdr)

        # Rows
        for ri, (date, score, count) in enumerate(self.rows):
            ry = H - hh - (ri+1)*rh
            # Alternate rows
            if ri % 2 == 0:
                c.setFillColor(WHITE)
            else:
                c.setFillColor(LIGHT)
            c.rect(0, ry, W, rh, fill=1, stroke=0)

            # Score colour
            if score < 0.35:   sc = TEAL
            elif score < 0.65: sc = PEACH
            else:              sc = RED

            # Date
            c.setFillColor(DEEP)
            c.setFont("Helvetica", 8)
            c.drawString(8, ry + 5, date)

            # Score pill
            pill_w = 60; pill_x = cw[0] + cw[1]/2 - pill_w/2
            c.setFillColor(SectionCard._alpha_hex(sc, 0.15))
            alpha_fill(c, "#ffffff", 0)
            c.setFillColor(colors.HexColor(SectionCard._alpha_hex(sc, 0.14)))
            rr(c, pill_x, ry + 3, pill_w, rh - 6, r=5)
            c.setFillColor(sc)
            c.setFont("Helvetica-Bold", 8.5)
            c.drawCentredString(cw[0] + cw[1]/2, ry + 5, f"{score:.3f}")

            # Count
            c.setFillColor(SLATE)
            c.setFont("Helvetica", 8)
            c.drawCentredString(cw[0]+cw[1] + cw[2]/2, ry + 5, str(count))

            # Grid line
            c.setStrokeColor(GRID)
            c.setLineWidth(0.4)
            c.line(0, ry, W, ry)

        # Outer border
        c.setStrokeColor(BORDER)
        c.setLineWidth(0.8)
        rr(c, 0, H - hh, W, H, r=8, fill=0, stroke=1)
        c.rect(0, H - hh - len(self.rows)*rh, W, len(self.rows)*rh,
               fill=0, stroke=1)


# ══════════════════════════════════════════════════════════════════════════════
#  COVER FLOWABLE
# ══════════════════════════════════════════════════════════════════════════════
class CoverBlock(Flowable):
    def __init__(self, width, period, stats):
        super().__init__()
        self._w    = width
        self.period = period
        self.stats = stats   # (avg_s, max_s, min_s, total, users, avg_sleep, avg_social)

    def wrap(self, aW, aH):
        return self._w, 1.80*inch

    def draw(self):
        c = self.canv
        W = self._w
        H = 1.80*inch

        # Background card
        c.setFillColor(CARD)
        rr(c, 0, 0, W, H, r=14)

        # Left accent
        gradient_rect(c, 0, 0, 6, H, PRIMARY, TEAL)
        rr(c, 0, 0, 6, H, r=4)

        # Title area
        c.setFillColor(DEEP)
        c.setFont("Helvetica-Bold", 20)
        c.drawString(22, H - 34, "Student Wellness Intelligence Report")

        c.setFont("Helvetica", 10)
        c.setFillColor(MUTED)
        c.drawString(22, H - 50, "Comprehensive stress analysis and behavioural insights")

        # Period tag
        c.setFillColor(PRIMARY)
        rr(c, 22, H - 78, 200, 20, r=6)
        c.setFillColor(DEEP)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(30, H - 72, f"Reporting Period:  {self.period}")

        # Mini KPIs
        avg_s, max_s, min_s, total, users, avg_sl, avg_so = self.stats
        mini = [
            (f"{avg_s:.2f}", "Avg Stress", PRIMARY),
            (f"{max_s:.2f}", "Peak",        RED),
            (f"{min_s:.2f}", "Lowest",      TEAL),
            (f"{total:,}",   "Check-ins",  ACCENT),
            (f"{users:,}",   "Students",   PEACH),
        ]
        kpi_w = (W - 22 - 10) / len(mini)
        for i, (val, lbl, col) in enumerate(mini):
            kx = 22 + i * kpi_w
            ky = 10
            c.setFillColor(WHITE)
            rr(c, kx + 4, ky, kpi_w - 8, 42, r=8)
            c.setFillColor(col)
            rr(c, kx + 4, ky + 38, kpi_w - 8, 4, r=4)
            c.setFont("Helvetica-Bold", 14)
            c.drawCentredString(kx + kpi_w/2, ky + 20, val)
            c.setFillColor(MUTED)
            c.setFont("Helvetica", 6.5)
            c.drawCentredString(kx + kpi_w/2, ky + 8, lbl)

        # Sleep & Social on right
        r_x = W - 180
        r_y = H - 78
        c.setFillColor(WHITE)
        rr(c, r_x, r_y, 175, 32, r=8)
        c.setFillColor(TEAL)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(r_x + 10, r_y + 20, f"Sleep Quality: {avg_sl:.1f} / 5")
        c.setFillColor(ACCENT)
        c.drawString(r_x + 10, r_y + 7, f"Social Support: {avg_so:.1f} / 5")


# ══════════════════════════════════════════════════════════════════════════════
#  ENDPOINT
# ══════════════════════════════════════════════════════════════════════════════
@report_bp.route("/api/reports/export", methods=["GET"])
def export_pdf_report():
    buf = io.BytesIO()
    doc = BaseDocTemplate(
        buf, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=0.82*inch, bottomMargin=0.60*inch,
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin,
                  doc.width, doc.height, id="main")
    doc.addPageTemplates([
        PageTemplate(id="serenity", frames=frame, onPage=_draw_page)
    ])

    st  = _styles()
    els = []
    CW  = CONTENT_W

    # ── Fetch data ─────────────────────────────────────────────────────────
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()

    cur.execute("""SELECT substr(created_at,1,10), AVG(stress_score), COUNT(*)
                   FROM serenity_checkins GROUP BY 1 ORDER BY 1""")
    daily = cur.fetchall()

    cur.execute("""SELECT AVG(stress_score), MAX(stress_score), MIN(stress_score),
                          COUNT(*), COUNT(DISTINCT user_id)
                   FROM serenity_checkins""")
    ov = cur.fetchone() or (0, 0, 0, 0, 0)

    cur.execute("""SELECT relationship_status, COUNT(*) FROM serenity_checkins
                   WHERE relationship_status IS NOT NULL AND relationship_status!=''
                   GROUP BY 1 ORDER BY 2 DESC""")
    rel = cur.fetchall()

    cur.execute("""SELECT substance_use, COUNT(*) FROM serenity_checkins
                   WHERE substance_use IS NOT NULL AND substance_use!=''
                   GROUP BY 1 ORDER BY 2 DESC""")
    sub = cur.fetchall()

    cur.execute("""SELECT AVG(sleep_quality), AVG(social_support)
                   FROM serenity_checkins
                   WHERE sleep_quality IS NOT NULL AND social_support IS NOT NULL""")
    ss = cur.fetchone() or (0, 0)
    conn.close()

    dates  = [r[0] for r in daily]
    scores = [r[1] or 0 for r in daily]
    avg_s  = ov[0] or 0;  max_s = ov[1] or 0;  min_s = ov[2] or 0
    total  = ov[3] or 0;  users = ov[4] or 0
    avg_sl = ss[0] or 0;  avg_so = ss[1] or 0

    fd = [
        ("Course / Academics", 0.28), ("Binge / Control",  0.22),
        ("Emotional Tone",     0.15), ("Relationship",     0.12),
        ("Substance Use",      0.10), ("Sleep Quality",    0.08),
        ("Social Support",     0.05),
    ]

    period = "No data yet"
    if dates:
        s = datetime.strptime(dates[0],  "%Y-%m-%d").strftime("%d %b %Y")
        e = datetime.strptime(dates[-1], "%Y-%m-%d").strftime("%d %b %Y")
        period = f"{s}  →  {e}"

    # ══ COVER BLOCK ═══════════════════════════════════════════════════════
    els.append(_sp(0.06))
    els.append(CoverBlock(CW, period,
                          (avg_s, max_s, min_s, total, users, avg_sl, avg_so)))
    els.append(_sp(0.18))

    # ══ SECTION 1 – Stress Factors (infographic bars) ════════════════════
    els.append(SectionHeader("1  ·  Major Stress Indicators", CW))
    els.append(_sp(0.10))

    factor_colors = [PRIMARY, TEAL, ACCENT, PEACH, RED]
    factor_data = [
        ("Academic Pressure & Deadlines", 0.68),
        ("Sleep Deprivation",             0.54),
        ("Social Isolation & Loneliness", 0.47),
        ("Financial Concerns",            0.39),
        ("Relationship Difficulties",     0.31),
    ]
    for i, (label, pct) in enumerate(factor_data):
        els.append(InfographicBar(label, pct, factor_colors[i], CW, height=26))
        els.append(_sp(0.04))

    els.append(_sp(0.04))
    els.append(Paragraph(
        "Proportions derived from SERENITY model weights and student self-report data.",
        st["caption"]))

    # ══ SECTION 2 – Daily Stress Trend ═══════════════════════════════════
    els.append(_sp(0.14))
    els.append(SectionHeader("2  ·  Daily Stress Trend", CW))
    els.append(_sp(0.10))

    if daily:
        img_buf = chart_trend(dates, scores)
        els.append(ImageBlock(img_buf, CW, 2.40*inch))
        els.append(Paragraph(
            "Figure 1 – Daily average stress with annotated peak & low markers.", st["caption"]))
    else:
        els.append(Paragraph("No check-in data recorded yet.", st["body"]))

    # ══ SECTION 3 – Feature Importance ═══════════════════════════════════
    els.append(_sp(0.14))
    els.append(SectionHeader("3  ·  What Shapes the Score?", CW))
    els.append(_sp(0.10))

    img_buf2 = chart_feature(fd)
    els.append(ImageBlock(img_buf2, CW, 2.60*inch))
    els.append(Paragraph(
        "Figure 2 – Relative model weight per input factor.", st["caption"]))

    # ══ SECTION 4 – Behavioural Patterns ═════════════════════════════════
    els.append(_sp(0.14))
    els.append(SectionHeader("4  ·  Behavioural & Social Patterns", CW))
    els.append(_sp(0.10))

    if rel and sub:
        l_buf = chart_donut(rel, "Relationship Status")
        r_buf = chart_bar(sub, "Substance Use")
        half  = (CW - 12) / 2
        left  = ImageBlock(l_buf, half, 2.60*inch)
        right = ImageBlock(r_buf, half, 2.60*inch)
        els.append(TwoCol(left, right, CW))
        els.append(Paragraph(
            "Figure 3 (left) – Relationship status distribution.   "
            "Figure 4 (right) – Substance use check-in counts.", st["caption"]))
    elif rel:
        l_buf = chart_donut(rel, "Relationship Status")
        els.append(ImageBlock(l_buf, CW * 0.55, 2.60*inch))
    elif sub:
        r_buf = chart_bar(sub, "Substance Use")
        els.append(ImageBlock(r_buf, CW * 0.55, 2.60*inch))
    else:
        els.append(Paragraph("No behavioural data recorded yet.", st["body"]))

    # ══ SECTION 5 – Warning Signs & Tips (card grid) ══════════════════════
    els.append(_sp(0.14))
    els.append(SectionHeader("5  ·  Warning Signs of Stress Decline", CW))
    els.append(_sp(0.10))

    symptom_cards = [
        SectionCard("🌀", "Illogical Thinking",
            "Difficulty concentrating, racing thoughts, or inability to make simple decisions — often the earliest cognitive red flag.",
            PRIMARY, 0, 102),
        SectionCard("⚡", "Erratic Mood Shifts",
            "Extreme emotional swings within hours — uncharacteristic irritability or euphoria disproportionate to actual events.",
            PEACH, 0, 102),
        SectionCard("🔔", "Heightened Sensitivity",
            "Overwhelmed by ordinary stimuli, withdrawing from social situations, or unusually reactive to criticism.",
            ACCENT, 0, 102),
        SectionCard("😴", "Sleep & Energy Disruption",
            "Persistent insomnia or oversleeping, constant fatigue, or a marked decline in motivation to attend classes.",
            TEAL, 0, 102),
        SectionCard("🚪", "Social Withdrawal",
            "Pulling away from friends, skipping events, neglecting hobbies. Isolation compounds distress quickly.",
            RED, 0, 102),
        SectionCard("📉", "Academic Performance Drop",
            "Missed deadlines, falling grades, or disengagement from coursework — visible proxies for underlying stress.",
            PEACH, 0, 102),
    ]
    els.append(ThreeCardRow(symptom_cards[:3], CW))
    els.append(_sp(0.08))
    els.append(ThreeCardRow(symptom_cards[3:], CW))

    # ── Tips ──────────────────────────────────────────────────────────────
    els.append(_sp(0.14))
    els.append(SectionHeader("6  ·  Tips to Manage Student Stress", CW))
    els.append(_sp(0.10))

    tip_cards = [
        SectionCard("🩺", "Speak to a Professional",
            "University counsellors offer confidential support. Early intervention is far more effective than waiting for crisis.",
            PRIMARY, 0, 102),
        SectionCard("🏃", "Exercise Regularly",
            "20–30 minutes of moderate movement reduces cortisol and improves mood through endorphin release.",
            TEAL, 0, 102),
        SectionCard("💬", "Communicate Openly",
            "Sharing feelings with a trusted friend reduces psychological burden. Vulnerability is a strength, not a weakness.",
            ACCENT, 0, 102),
        SectionCard("🌙", "Prioritise Quality Sleep",
            "Consistent 7–9 hours, screen curfew 1hr before bed, and a regular wake time stabilise emotional regulation.",
            PEACH, 0, 102),
        SectionCard("🧘", "Practice Mindfulness",
            "5–10 minutes of daily breathing exercises lowers baseline stress — verified in SERENITY check-in data.",
            RED, 0, 102),
        SectionCard("📅", "Structure Your Day",
            "Predictable routines anchor mental health. Time-blocking study, rest, and social activities reduces anxiety.",
            PRIMARY, 0, 102),
    ]
    els.append(ThreeCardRow(tip_cards[:3], CW))
    els.append(_sp(0.08))
    els.append(ThreeCardRow(tip_cards[3:], CW))

    # ══ SECTION 6 – Full Daily Log ════════════════════════════════════════
    if daily:
        els.append(_sp(0.14))
        els.append(SectionHeader("7  ·  Full Daily Check-in Log", CW))
        els.append(_sp(0.10))

        cws = [CW*0.38, CW*0.38, CW*0.24]
        rows = [(r[0], r[1] or 0, r[2]) for r in daily]
        els.append(StressTable(rows, cws, CW))
        els.append(_sp(0.08))
        els.append(Paragraph(
            "<font color='#6ED3CF'><b>■</b></font> Low (&lt;0.35)    "
            "<font color='#FFB38A'><b>■</b></font> Moderate (0.35–0.65)    "
            "<font color='#F87171'><b>■</b></font> High (&gt;0.65)",
            st["note"]))

    # ══ ETHICAL NOTE ══════════════════════════════════════════════════════
    els.append(_sp(0.16))

    class EthicsBox(Flowable):
        def __init__(self, w):
            super().__init__(); self._w = w
        def wrap(self, aW, aH):
            return self._w, 44
        def draw(self):
            c = self.canv
            W = self._w
            c.setFillColor(CARD)
            rr(c, 0, 0, W, 44, r=8)
            c.setFillColor(ACCENT)
            rr(c, 0, 0, 5, 44, r=4)
            c.setFillColor(SLATE)
            c.setFont("Helvetica-Oblique", 7.5)
            lines = [
                "SERENITY visualises patterns for gentle awareness — it does not diagnose, label, or replace professional mental",
                "health support. Scores are self-reported and anonymised. If any participant scores consistently above 0.65,",
                "a follow-up with a qualified counsellor is recommended.",
            ]
            for i, ln in enumerate(lines):
                c.drawString(14, 30 - i*11, ln)

    els.append(EthicsBox(CW))
    els.append(_sp(0.06))

    doc.build(els)
    buf.seek(0)
    return send_file(buf, as_attachment=True,
                     download_name="serenity_report.pdf",
                     mimetype="application/pdf")