from io import BytesIO
from xml.sax.saxutils import escape

from django.http import HttpResponse

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


GREEN = colors.HexColor("#185239")
DARK_GREEN = colors.HexColor("#102e21")
LIGHT_GREEN = colors.HexColor("#eaf4ed")
BORDER = colors.HexColor("#e3eae5")


def build_pdf_response(title, sections, filename):
    """
    Build a printable PDF response.

    sections format:
    [
        ("Section heading", [("Label", "Value"), ...]),
    ]
    """

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        title=title,
        author="ShambaSense",
    )

    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="ReportTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=19,
        leading=24,
        textColor=DARK_GREEN,
        alignment=TA_CENTER,
        spaceAfter=8,
    ))

    styles.add(ParagraphStyle(
        name="ReportSubtitle",
        parent=styles["Normal"],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#718078"),
        alignment=TA_CENTER,
        spaceAfter=18,
    ))

    styles.add(ParagraphStyle(
        name="ReportSection",
        parent=styles["Heading2"],
        fontSize=12,
        leading=16,
        textColor=GREEN,
        spaceBefore=13,
        spaceAfter=7,
    ))

    styles.add(ParagraphStyle(
        name="ReportCell",
        parent=styles["BodyText"],
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#24332a"),
    ))

    styles.add(ParagraphStyle(
        name="ReportLabel",
        parent=styles["BodyText"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=12,
        textColor=DARK_GREEN,
    ))

    story = [
        Paragraph(escape(str(title)), styles["ReportTitle"]),
        Paragraph(
            "ShambaSense | Agricultural Decision Support",
            styles["ReportSubtitle"],
        ),
    ]

    for section_title, rows in sections:
        story.append(
            Paragraph(escape(str(section_title)), styles["ReportSection"])
        )

        if not rows:
            story.append(Paragraph("No records available.", styles["ReportCell"]))
            story.append(Spacer(1, 5))
            continue

        table_data = []

        for label, value in rows:
            safe_label = Paragraph(
                escape(str(label)),
                styles["ReportLabel"],
            )
            safe_value = Paragraph(
                escape(str(value if value not in (None, "") else "Not recorded")),
                styles["ReportCell"],
            )
            table_data.append([safe_label, safe_value])

        table = Table(
            table_data,
            colWidths=[48 * mm, 119 * mm],
            repeatRows=0,
            hAlign="LEFT",
        )

        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), LIGHT_GREEN),
            ("TEXTCOLOR", (0, 0), (-1, -1), DARK_GREEN),
            ("GRID", (0, 0), (-1, -1), 0.4, BORDER),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))

        story.append(table)
        story.append(Spacer(1, 8))

    def add_page_number(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#718078"))
        canvas.drawString(18 * mm, 11 * mm, "ShambaSense")
        canvas.drawRightString(
            A4[0] - 18 * mm,
            11 * mm,
            f"Page {doc.page}",
        )
        canvas.restoreState()

    document.build(
        story,
        onFirstPage=add_page_number,
        onLaterPages=add_page_number,
    )

    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="{filename}"'
    )
    response["Content-Length"] = len(pdf)

    return response
