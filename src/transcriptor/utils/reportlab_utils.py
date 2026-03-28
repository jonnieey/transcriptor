from pathlib import Path
from typing import Any, Dict

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    PageTemplate,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from transcriptor.models import Invoice


class BackgroundDocTemplate(BaseDocTemplate):
    def __init__(self, filename, **kwargs):
        super().__init__(filename, **kwargs)
        frame = Frame(
            self.leftMargin,
            self.bottomMargin,
            self.width,
            self.height,
            id="normal",
        )
        template = PageTemplate(
            id="BackgroundPage", frames=[frame], onPage=self._draw_background
        )
        self.addPageTemplates([template])

    def _draw_background(self, canvas, doc):
        canvas.setFillColor(colors.HexColor("#FFFFFF"))
        canvas.rect(
            0, 0, self.pagesize[0], self.pagesize[1], fill=1, stroke=0
        )


def format_currency(amount: float) -> str:
    return f"${amount:,.2f}"


def invoice_to_reportlab_data(invoice: Invoice) -> Dict[str, Any]:
    """Convert Invoice model to ReportLab-compatible dictionary"""
    return {
        "invoice_number": invoice.invoice_number,
        "profile": {
            "name": invoice.profile.name,
            "area": invoice.profile.area,
            "country": invoice.profile.country,
        },
        "create_date": invoice.create_date.strftime("%Y-%m-%d"),
        "due_date": invoice.due_date.strftime("%Y-%m-%d")
        if invoice.due_date
        else "",
        "client_name": invoice.client_name,
        "jobs": [
            {
                "job_number": job.job_number,
                "job_type": job.job_type,
                "job_rate": job.job_rate,
                "quantity": job.quantity,
                "amount": job.amount,
            }
            for job in invoice.jobs
        ],
    }


def register_fonts():
    """Register Montserrat font family"""
    font_files = {
        "Montserrat-Bold": "Montserrat-Bold.ttf",
        "Montserrat": "Montserrat-Regular.ttf",
        "Montserrat-Italic": "Montserrat-Italic.ttf",
        "Montserrat-BoldItalic": "Montserrat-BoldItalic.ttf",
    }

    fonts_registered = False

    # Try to load fonts from package resources
    try:
        import importlib.resources

        for font_name, font_file in font_files.items():
            try:
                # Try to get font file from package
                font_data = (
                    importlib.resources.files("transcriptor.fonts")
                    .joinpath(font_file)
                    .read_bytes()
                )
                # Create a temporary file or register from bytes
                import tempfile

                with tempfile.NamedTemporaryFile(
                    suffix=".ttf", delete=False
                ) as tmp:
                    tmp.write(font_data)
                    tmp.flush()
                    pdfmetrics.registerFont(TTFont(font_name, tmp.name))
                fonts_registered = True
            except (FileNotFoundError, ImportError):
                continue

    except (ImportError, FileNotFoundError):
        # Fallback to local directory
        font_path = Path(__file__).parent.parent / "fonts"
        for font_name, font_file in font_files.items():
            font_file_path = font_path / font_file
            if font_file_path.exists():
                pdfmetrics.registerFont(
                    TTFont(font_name, str(font_file_path))
                )
                fonts_registered = True

    if not fonts_registered:
        # Use default fonts if custom fonts not found
        print("Warning: Montserrat fonts not found. Using default fonts.")
        return

    # Register font family
    pdfmetrics.registerFontFamily(
        "Montserrat",
        normal="Montserrat",
        bold="Montserrat-Bold",
        italic="Montserrat-Italic",
        boldItalic="Montserrat-BoldItalic",
    )


def create_invoice_pdf(invoice: Invoice, output_filename: Path) -> None:
    """
    Generates an invoice PDF from an Invoice model.

    Args:
        invoice: Invoice model instance
        output_filename: Path where PDF will be saved
    """
    # Register fonts first
    register_fonts()

    # Convert invoice model to reportlab data format
    data = invoice_to_reportlab_data(invoice)

    # Create the document with margins
    doc = BackgroundDocTemplate(
        str(output_filename),
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
    )
    story = []  # container for flowables

    # ----- Define custom styles -------------------------------------------------
    styles = getSampleStyleSheet()
    # Base style for body text
    normal_style = styles["Normal"]
    normal_style.fontName = "Montserrat"
    normal_style.fontSize = 10

    # Style for labels in the client info table (blue, bold)
    label_style = ParagraphStyle(
        "LabelStyle",
        parent=normal_style,
        fontName="Montserrat-Bold",
        textColor=colors.HexColor("#1e88e5"),
        fontSize=10,
        alignment=TA_LEFT,
    )
    # Style for the values in client info table
    value_style = ParagraphStyle(
        "ValueStyle",
        parent=normal_style,
        fontName="Montserrat",
        fontSize=10,
        alignment=TA_LEFT,
    )
    # Header title style (white, large)
    header_style = ParagraphStyle(
        "HeaderStyle",
        parent=normal_style,
        fontName="Montserrat-Bold",
        fontSize=24,
        textColor=colors.white,
        alignment=TA_LEFT,
        leading=28,
    )
    # Table header style (gray background, bold)
    th_style = ParagraphStyle(
        "TableHeaderStyle",
        parent=normal_style,
        fontName="Montserrat-Bold",
        fontSize=10,
        textColor=colors.HexColor("#555555"),
        alignment=TA_LEFT,
    )
    # Table cell style (normal)
    td_style = normal_style

    # ----- Header (blue background with invoice number) -----------------------
    header_data = [
        [
            Paragraph(f"Invoice #{data['invoice_number']}", header_style),
            Paragraph("", normal_style),  # Placeholder for logo
        ]
    ]
    header_table = Table(
        header_data, colWidths=[doc.width * 0.7, doc.width * 0.3]
    )
    header_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#1e88e5")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 20),
                ("RIGHTPADDING", (0, 0), (-1, -1), 20),
                ("TOPPADDING", (0, 0), (-1, -1), 20),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 20),
                ("BOX", (0, 0), (-1, -1), 0, colors.white),  # no border
            ]
        )
    )
    story.append(header_table)
    story.append(Spacer(1, 20))

    # ----- Client information (two‑column table) ------------------------------
    client_data = [
        [
            Paragraph("Name:", label_style),
            Paragraph(data["profile"]["name"], value_style),
            Paragraph("Invoice Date:", label_style),
            Paragraph(data["create_date"], value_style),
        ],
        [
            Paragraph("Area:", label_style),
            Paragraph(data["profile"]["area"], value_style),
            Paragraph("Due Date:", label_style),
            Paragraph(data["due_date"], value_style),
        ],
        [
            Paragraph("Country:", label_style),
            Paragraph(data["profile"]["country"], value_style),
            Paragraph("Client Name:", label_style),
            Paragraph(data["client_name"], value_style),
        ],
    ]
    client_table = Table(
        client_data,
        colWidths=[
            doc.width * 0.2,
            doc.width * 0.3,
            doc.width * 0.2,
            doc.width * 0.3,
        ],
    )
    client_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), "Montserrat"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.lightgrey,
                ),  # optional light border
            ]
        )
    )
    story.append(client_table)
    story.append(Spacer(1, 20))

    # ----- Line items table ---------------------------------------------------
    # Table headers
    headers = ["#", "Job Number", "Job Type", "Rate", "Quantity", "Amount"]
    # Build data rows from jobs
    rows = []
    for idx, job in enumerate(data["jobs"], start=1):
        rows.append(
            [
                Paragraph(str(idx), td_style),
                Paragraph(job["job_number"], td_style),
                Paragraph(job["job_type"].title(), td_style),
                Paragraph(format_currency(job["job_rate"]), td_style),
                Paragraph(f"{job['quantity']:.1f}", td_style),
                Paragraph(format_currency(job["amount"]), td_style),
            ]
        )

    # Total row
    total = sum(job["amount"] for job in data["jobs"])
    rows.append(
        [
            Paragraph("", td_style),
            Paragraph("", td_style),
            Paragraph("", td_style),
            Paragraph("", td_style),
            Paragraph("<b>TOTAL</b>", td_style),
            Paragraph(f"<b>{format_currency(total)}</b>", td_style),
        ]
    )

    # Create the full table (headers + rows)
    table_data = [headers] + rows
    # Column widths: we'll let them auto-size, but we can set a proportion
    col_widths = [
        0.5 * inch,
        1.5 * inch,
        1.5 * inch,
        1.0 * inch,
        1.0 * inch,
        1.5 * inch,
    ]
    line_items_table = Table(table_data, colWidths=col_widths, repeatRows=1)

    # Style the table
    tbl_style = TableStyle(
        [
            # Header row
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f5f5f5")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#555555")),
            ("ALIGN", (0, 0), (-1, 0), "LEFT"),
            ("FONTNAME", (0, 0), (-1, 0), "Montserrat-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
            ("TOPPADDING", (0, 0), (-1, 0), 12),
            # Body rows: even rows light blue
            ("BACKGROUND", (0, 1), (-1, -2), colors.HexColor("#e3f2fd")),
            # Total row (last row) light green
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#e8f5e9")),
            ("FONTNAME", (0, -1), (-1, -1), "Montserrat-Bold"),
            (
                "ALIGN",
                (4, -1),
                (5, -1),
                "RIGHT",
            ),  # align TOTAL and amount to right
            # General alignment
            ("ALIGN", (0, 1), (0, -1), "CENTER"),  # center # column
            ("ALIGN", (3, 1), (3, -1), "RIGHT"),  # rate right aligned
            ("ALIGN", (4, 1), (4, -1), "RIGHT"),  # quantity right aligned
            ("ALIGN", (5, 1), (5, -1), "RIGHT"),  # amount right aligned
            # Borders
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]
    )
    line_items_table.setStyle(tbl_style)
    story.append(line_items_table)

    # Optional footer (plain gray background)
    story.append(Spacer(1, 30))

    # Build the PDF
    doc.build(story)


def generate_invoice_pdf(invoice: Invoice, output_path: Path) -> None:
    """
    Main function to generate invoice PDF using ReportLab.

    Args:
        invoice: Invoice model instance
        output_path: Path where PDF will be saved
    """
    create_invoice_pdf(invoice, output_path)


def summary_invoice_to_reportlab_data(summary_invoice) -> Dict[str, Any]:
    """Convert SummaryInvoice model to ReportLab-compatible dictionary"""
    return {
        "create_date": summary_invoice.create_date,
        "profile": {
            "name": summary_invoice.profile.name,
            "area": summary_invoice.profile.area,
            "country": summary_invoice.profile.country,
        },
        "client_name": summary_invoice.client_name,
        "summary_lines": [
            {
                "month": line.month,
                "job_count": line.job_count,
                "total": line.total,
            }
            for line in summary_invoice.summary_lines
        ],
    }


def create_summary_invoice_pdf(
    summary_invoice, output_filename: Path
) -> None:
    """
    Generates a summary invoice PDF from a SummaryInvoice model.

    Args:
        summary_invoice: SummaryInvoice model instance
        output_filename: Path where PDF will be saved
    """
    # Register fonts first
    register_fonts()

    # Convert summary invoice model to reportlab data format
    data = summary_invoice_to_reportlab_data(summary_invoice)

    # Create the document with margins
    from reportlab.platypus import SimpleDocTemplate

    doc = SimpleDocTemplate(
        str(output_filename),
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
    )
    story = []

    # ----- Define custom styles -------------------------------------------------
    styles = getSampleStyleSheet()

    # Check if Montserrat font is available, otherwise use Helvetica
    registered_fonts = pdfmetrics.getRegisteredFontNames()
    if "Montserrat" in registered_fonts:
        base_font = "Montserrat"
        bold_font = "Montserrat-Bold"
    else:
        base_font = "Helvetica"
        bold_font = "Helvetica-Bold"

    normal_style = styles["Normal"]
    normal_style.fontName = base_font
    normal_style.fontSize = 10

    # Title style (used in header)
    title_style = ParagraphStyle(
        "TitleStyle",
        parent=normal_style,
        fontName=bold_font,
        fontSize=18,
        textColor=colors.black,
        alignment=TA_RIGHT,
    )

    # Label style (for detail section labels)
    label_style = ParagraphStyle(
        "LabelStyle",
        parent=normal_style,
        fontName=bold_font,
        fontSize=10,
        textColor=colors.black,
        alignment=TA_LEFT,
    )

    # Value style (for detail section values)
    value_style = ParagraphStyle(
        "ValueStyle",
        parent=normal_style,
        fontName=base_font,
        fontSize=10,
        textColor=colors.black,
        alignment=TA_LEFT,
    )

    # Table header style (gray background)
    th_style = ParagraphStyle(
        "TableHeaderStyle",
        parent=normal_style,
        fontName=bold_font,
        fontSize=10,
        textColor=colors.HexColor("#777777"),
        alignment=TA_LEFT,
    )

    # Table cell style (normal)
    td_style = normal_style

    # Total row style (bold)
    total_style = ParagraphStyle(
        "TotalStyle",
        parent=normal_style,
        fontName=bold_font,
        fontSize=10,
        textColor=colors.black,
        alignment=TA_RIGHT,
    )

    # ----- Header (gray background with title) ---------------------------------
    # Get the year from create_date (supports string or datetime)
    if isinstance(data["create_date"], str):
        year = (
            data["create_date"].split("-")[0]
            if "-" in data["create_date"]
            else data["create_date"]
        )
    else:
        year = data["create_date"].year
    header_title = Paragraph(f"Summary Invoice {year}", title_style)

    # Header uses a table with two cells (left for optional logo, right for title)
    header_data = [
        [Paragraph("", normal_style), header_title]  # left empty for logo
    ]
    header_table = Table(
        header_data, colWidths=[doc.width * 0.3, doc.width * 0.7]
    )
    header_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#eeeeee")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (0, -1), "LEFT"),
                ("ALIGN", (-1, 0), (-1, -1), "RIGHT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 20),
                ("RIGHTPADDING", (0, 0), (-1, -1), 20),
                ("TOPPADDING", (0, 0), (-1, -1), 15),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 15),
            ]
        )
    )
    story.append(header_table)
    story.append(Spacer(1, 20))

    # ----- Details section (light gray background, border) --------------------
    # Build rows for profile details
    profile_rows = [
        [
            Paragraph("Name:", label_style),
            Paragraph(data["profile"]["name"], value_style),
        ],
        [
            Paragraph("Area:", label_style),
            Paragraph(data["profile"]["area"], value_style),
        ],
        [
            Paragraph("Country:", label_style),
            Paragraph(data["profile"]["country"], value_style),
        ],
        [
            Paragraph("Client Name:", label_style),
            Paragraph(data["client_name"], value_style),
        ],
    ]

    # Create a table for these details with two columns
    details_table = Table(
        profile_rows, colWidths=[doc.width * 0.25, doc.width * 0.75]
    )
    details_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f9f9f9")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (0, 0), (0, -1), "LEFT"),
                ("ALIGN", (1, 0), (1, -1), "LEFT"),
            ]
        )
    )
    story.append(details_table)
    story.append(Spacer(1, 20))

    # ----- Summary items table -------------------------------------------------
    # Table headers
    headers = ["", "Month", "Job Count", "Total"]
    col_widths = [0.5 * inch, 3.0 * inch, 1.2 * inch, 1.5 * inch]

    # Build data rows from summary_lines
    rows = []
    for idx, line in enumerate(data["summary_lines"], start=1):
        rows.append(
            [
                Paragraph(str(idx), td_style),
                Paragraph(line["month"], td_style),
                Paragraph(str(line["job_count"]), td_style),
                Paragraph(format_currency(line["total"]), td_style),
            ]
        )

    # Total row
    total = sum(line["total"] for line in data["summary_lines"])
    rows.append(
        [
            Paragraph("", td_style),
            Paragraph("", td_style),
            Paragraph("<b>TOTAL</b>", td_style),
            Paragraph(f"<b>{format_currency(total)}</b>", td_style),
        ]
    )

    # Create the full table (headers + rows)
    table_data = [headers] + rows
    summary_table = Table(table_data, colWidths=col_widths, repeatRows=1)

    # Style the table
    tbl_style = TableStyle(
        [
            # Header row
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eeeeee")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#777777")),
            ("ALIGN", (0, 0), (-1, 0), "LEFT"),
            ("FONTNAME", (0, 0), (-1, 0), bold_font),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("TOPPADDING", (0, 0), (-1, 0), 8),
            # Total row (last row) light gray
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#eeeeee")),
            ("FONTNAME", (0, -1), (-1, -1), bold_font),
            (
                "ALIGN",
                (2, -1),
                (2, -1),
                "RIGHT",
            ),  # align TOTAL label to right
            (
                "ALIGN",
                (3, -1),
                (3, -1),
                "RIGHT",
            ),  # align total amount to right
            # Column alignment
            ("ALIGN", (0, 1), (0, -1), "CENTER"),  # index column centered
            ("ALIGN", (2, 1), (2, -1), "RIGHT"),  # Job Count right aligned
            ("ALIGN", (3, 1), (3, -1), "RIGHT"),  # Total right aligned
            # Borders and spacing
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]
    )
    summary_table.setStyle(tbl_style)
    story.append(summary_table)

    # Build the PDF
    doc.build(story)


def generate_summary_invoice_pdf(summary_invoice, output_path: Path) -> None:
    """
    Main function to generate summary invoice PDF using ReportLab.

    Args:
        summary_invoice: SummaryInvoice model instance
        output_path: Path where PDF will be saved
    """
    create_summary_invoice_pdf(summary_invoice, output_path)
