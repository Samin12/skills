#!/usr/bin/env python3
"""
YouTube Research Outlier Report Generator

Generates a professional PDF report from outlier research data.
Accepts a JSON file as input with tiers, video ideas, and patterns.

Usage:
    python3 generate_report.py --input data.json --output report.pdf
    python3 generate_report.py --input data.json  # defaults to ./Outlier_Report.pdf
"""

import argparse
import json
import sys
import os
from datetime import datetime

try:
    from fpdf import FPDF
except ImportError:
    print("fpdf2 not installed. Installing...")
    os.system(f"{sys.executable} -m pip install fpdf2 --quiet")
    from fpdf import FPDF


class OutlierReport(FPDF):
    def __init__(self, channel_name="YouTube Channel"):
        super().__init__()
        self.channel_name = channel_name
        self.set_auto_page_break(auto=True, margin=20)

    def header(self):
        if self.page_no() > 1:
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(140, 140, 140)
            date_str = datetime.now().strftime("%B %Y")
            self.cell(0, 8, f"TubeLab Outlier Research  |  {self.channel_name}  |  {date_str}", align="C")
            self.ln(12)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(140, 140, 140)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def section_title(self, title, color=(41, 98, 255)):
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(*color)
        self.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*color)
        self.set_line_width(0.8)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(6)

    def body_text(self, text):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(50, 50, 50)
        self.multi_cell(0, 5.5, text)
        self.ln(2)

    def stat_badge(self, label, value, color=(41, 98, 255)):
        x = self.get_x()
        y = self.get_y()
        w = 52
        h = 32
        self.set_fill_color(*color)
        self.rect(x, y, w, h, style="F")
        self.set_xy(x, y + 4)
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(255, 255, 255)
        self.cell(w, 8, str(value), align="C")
        self.set_xy(x, y + 15)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(220, 220, 255)
        self.cell(w, 6, label, align="C")
        self.set_xy(x + w + 6, y)

    def outlier_card(self, rank, title, channel, subs, views, ratio, zscore, your_angle, duration=""):
        y_start = self.get_y()
        if y_start > 230:
            self.add_page()
            y_start = self.get_y()

        card_w = self.w - self.l_margin - self.r_margin

        # Rank circle
        self.set_fill_color(41, 98, 255)
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(255, 255, 255)
        cx = self.l_margin + 8
        cy = y_start + 8
        self.ellipse(cx - 8, cy - 8, 16, 16, style="F")
        self.set_xy(cx - 8, cy - 5)
        self.cell(16, 10, str(rank), align="C")

        # Title
        self.set_xy(self.l_margin + 22, y_start + 1)
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(30, 30, 30)
        self.cell(card_w - 22, 6, title[:85], new_x="LMARGIN", new_y="NEXT")

        # Channel info
        self.set_x(self.l_margin + 22)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(100, 100, 100)
        self.cell(card_w - 22, 5, f"{channel} ({subs} subs)  |  {duration}", new_x="LMARGIN", new_y="NEXT")
        self.ln(3)

        # Stats row
        self.set_x(self.l_margin + 22)

        self.set_fill_color(230, 240, 255)
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(41, 98, 255)
        views_text = f"  {views} views  "
        vw = self.get_string_width(views_text) + 4
        self.cell(vw, 7, views_text, fill=True)
        self.cell(3, 7, "")

        self.set_fill_color(220, 255, 230)
        self.set_text_color(0, 140, 60)
        ratio_text = f"  {ratio}x avg  "
        rw = self.get_string_width(ratio_text) + 4
        self.cell(rw, 7, ratio_text, fill=True)
        self.cell(3, 7, "")

        self.set_fill_color(255, 235, 220)
        self.set_text_color(200, 80, 0)
        z_text = f"  z: {zscore}  "
        zw = self.get_string_width(z_text) + 4
        self.cell(zw, 7, z_text, fill=True)

        self.ln(10)

        # Your angle
        self.set_x(self.l_margin + 22)
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(41, 98, 255)
        self.cell(card_w - 22, 5, "YOUR ANGLE:", new_x="LMARGIN", new_y="NEXT")
        self.set_x(self.l_margin + 22)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(60, 60, 80)
        self.multi_cell(card_w - 26, 5, your_angle)

        self.ln(3)
        self.set_draw_color(220, 220, 220)
        self.set_line_width(0.3)
        self.line(self.l_margin + 22, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(5)

    def video_idea_row(self, rank, idea, why, reference):
        y_start = self.get_y()
        if y_start > 240:
            self.add_page()
            y_start = self.get_y()

        card_w = self.w - self.l_margin - self.r_margin

        self.set_fill_color(41, 98, 255)
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(255, 255, 255)
        cx = self.l_margin + 8
        cy = y_start + 8
        self.ellipse(cx - 8, cy - 8, 16, 16, style="F")
        self.set_xy(cx - 8, cy - 5)
        self.cell(16, 10, str(rank), align="C")

        self.set_xy(self.l_margin + 22, y_start + 1)
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(30, 30, 30)
        self.multi_cell(card_w - 26, 6, idea)

        self.set_x(self.l_margin + 22)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(80, 80, 80)
        self.multi_cell(card_w - 26, 5, f"Why: {why}")

        self.set_x(self.l_margin + 22)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(140, 140, 140)
        self.multi_cell(card_w - 26, 4.5, f"Based on: {reference}")

        self.ln(3)
        self.set_draw_color(220, 220, 220)
        self.set_line_width(0.3)
        self.line(self.l_margin + 22, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(5)

    def pattern_item(self, number, title, description):
        y_start = self.get_y()
        if y_start > 250:
            self.add_page()
            y_start = self.get_y()

        card_w = self.w - self.l_margin - self.r_margin

        self.set_font("Helvetica", "B", 20)
        self.set_text_color(41, 98, 255)
        self.cell(16, 10, str(number), new_x="END")

        x_after = self.get_x() + 4
        self.set_xy(x_after, y_start)
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(30, 30, 30)
        self.cell(card_w - 24, 6, title, new_x="LMARGIN", new_y="NEXT")

        self.set_x(self.l_margin + 20)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(80, 80, 80)
        self.multi_cell(card_w - 24, 5, description)
        self.ln(5)


def generate_report(data, output_path):
    channel_name = data.get("channel", {}).get("name", "YouTube Channel")
    channel_handle = data.get("channel", {}).get("handle", "@channel")
    report_date = data.get("date", datetime.now().strftime("%B %d, %Y"))

    pdf = OutlierReport(channel_name)
    pdf.alias_nb_pages()

    # === COVER PAGE ===
    pdf.add_page()
    pdf.ln(30)

    pdf.set_font("Helvetica", "B", 32)
    pdf.set_text_color(41, 98, 255)
    pdf.cell(0, 14, "TubeLab Outlier", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 14, "Research Report", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)

    pdf.set_font("Helvetica", "", 14)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, f"Video Ideas Backed by Data for {channel_handle}", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    pdf.set_font("Helvetica", "I", 11)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 8, report_date, align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(20)

    pdf.set_draw_color(41, 98, 255)
    pdf.set_line_width(1.5)
    center_x = pdf.w / 2
    pdf.line(center_x - 40, pdf.get_y(), center_x + 40, pdf.get_y())
    pdf.ln(20)

    # Stats badges
    queries = str(data.get("queries_run", "?"))
    outliers_count = str(data.get("outliers_found", "?"))
    ideas_count = str(len(data.get("video_ideas", [])))
    credits = str(data.get("credits_used", "?"))

    start_x = (pdf.w - (4 * 52 + 3 * 6)) / 2
    pdf.set_xy(start_x, pdf.get_y())
    pdf.stat_badge("Queries Run", queries, (41, 98, 255))
    pdf.stat_badge("Outliers Found", outliers_count, (0, 160, 80))
    pdf.stat_badge("Top Ideas", ideas_count, (200, 80, 0))
    pdf.stat_badge("Credits Used", credits, (120, 80, 200))
    pdf.ln(45)

    # Method note
    description = data.get("description", "")
    if description:
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(120, 120, 120)
        pdf.multi_cell(0, 5.5, description, align="C")
        pdf.ln(8)

    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(41, 98, 255)
    pdf.cell(0, 6, "averageViewsRatio = actual views / channel avg views.  5x+ = monster outlier.", align="C")

    # === TIERS ===
    for tier in data.get("tiers", []):
        pdf.add_page()
        color = tuple(tier.get("color", [41, 98, 255]))
        pdf.section_title(tier["name"], color)
        if tier.get("description"):
            pdf.body_text(tier["description"])
            pdf.ln(3)

        for outlier in tier.get("outliers", []):
            pdf.outlier_card(
                outlier["rank"],
                outlier["title"],
                outlier["channel"],
                outlier["subs"],
                outlier["views"],
                outlier["ratio"],
                outlier["zscore"],
                outlier["your_angle"],
                outlier.get("duration", "")
            )

    # === VIDEO IDEAS ===
    ideas = data.get("video_ideas", [])
    if ideas:
        pdf.add_page()
        pdf.section_title(f"TOP {len(ideas)} VIDEO IDEAS (Ranked by Opportunity)", (41, 98, 255))
        pdf.body_text("Distilled from all outlier data. Ordered by expected performance based on outlier ratios, topic demand, and unique credibility.")
        pdf.ln(4)

        for idea in ideas:
            pdf.video_idea_row(
                idea["rank"],
                idea["idea"],
                idea["why"],
                idea["reference"]
            )

    # === PATTERNS ===
    patterns = data.get("patterns", [])
    if patterns:
        pdf.add_page()
        pdf.section_title("KEY PATTERNS FROM THE DATA", (80, 60, 180))
        pdf.ln(2)

        for pattern in patterns:
            pdf.pattern_item(
                pattern["number"],
                pattern["title"],
                pattern["description"]
            )

    # === CLOSING ===
    closing = data.get("closing_note", "")
    if closing:
        pdf.ln(10)
        pdf.set_draw_color(41, 98, 255)
        pdf.set_line_width(0.5)
        pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
        pdf.ln(8)

        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(41, 98, 255)
        pdf.cell(0, 7, "YOUR UNFAIR ADVANTAGE", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(60, 60, 60)
        pdf.multi_cell(0, 5.5, closing)

    pdf.ln(8)
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 6, f"Generated by YouTube Research Skill  |  TubeLab API  |  {credits} credits used", align="C")

    pdf.output(output_path)
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Generate YouTube Outlier Research PDF Report")
    parser.add_argument("--input", "-i", required=True, help="Path to JSON data file")
    parser.add_argument("--output", "-o", default="Outlier_Report.pdf", help="Output PDF path")
    args = parser.parse_args()

    with open(args.input, "r") as f:
        data = json.load(f)

    output = generate_report(data, args.output)
    print(f"Report saved to: {output}")


if __name__ == "__main__":
    main()
