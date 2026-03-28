from pathlib import Path
from typing import Optional

from transcriptor.models import Invoice, SummaryInvoice

from .reportlab_utils import (
    generate_invoice_pdf,
    generate_summary_invoice_pdf,
)


def htmlstr_to_pdf(htmlstr: str, output_path: Path) -> Optional[bytes]:
    """Deprecated: HTML to PDF conversion no longer supported."""
    import warnings

    warnings.warn(
        "htmlstr_to_pdf is deprecated. Use generate_invoice_pdf instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return None  # Return None for backward compatibility


def render_invoice(
    invoice: Invoice,
    custom_templates_dir: Optional[Path] = None,
    template_name: Optional[str] = None,
) -> str:
    """Deprecated: Template rendering no longer supported."""
    import warnings

    warnings.warn(
        "render_invoice is deprecated. Invoice generation now uses ReportLab directly.",
        DeprecationWarning,
        stacklevel=2,
    )
    return ""  # Return empty string for backward compatibility


def render_summary_invoice(
    summary_invoice: SummaryInvoice,
    custom_templates_dir: Optional[Path] = None,
    template_name: Optional[str] = None,
) -> str:
    """Deprecated: Template rendering no longer supported."""
    import warnings

    warnings.warn(
        "render_summary_invoice is deprecated. Summary invoice generation now uses ReportLab directly.",
        DeprecationWarning,
        stacklevel=2,
    )
    return ""  # Return empty string for backward compatibility


def write_pdf(
    invoice: Invoice,
    output_path: Path,
    custom_templates_dir: Optional[Path] = None,
    template_name: Optional[str] = None,
) -> None:
    """
    Generate invoice PDF using ReportLab.

    Args:
        invoice: Invoice model instance
        output_path: Path where PDF will be saved
        custom_templates_dir: Ignored (for backward compatibility)
        template_name: Ignored (for backward compatibility)
    """
    generate_invoice_pdf(invoice, output_path)


def write_summary_pdf(
    summary_invoice: SummaryInvoice,
    output_path: Path,
    custom_templates_dir: Optional[Path] = None,
    template_name: Optional[str] = None,
) -> None:
    """
    Generate summary invoice PDF using ReportLab.

    Args:
        summary_invoice: SummaryInvoice model instance
        output_path: Path where PDF will be saved
        custom_templates_dir: Ignored (for backward compatibility)
        template_name: Ignored (for backward compatibility)
    """
    generate_summary_invoice_pdf(summary_invoice, output_path)


def html_to_md(html: str) -> str:
    """Deprecated: HTML to Markdown conversion no longer supported."""
    import warnings

    warnings.warn(
        "html_to_md is deprecated. HTML templates are no longer used.",
        DeprecationWarning,
        stacklevel=2,
    )
    return ""  # Return empty string for backward compatibility


def invoice_template_themes():
    """Deprecated: Invoice templates are no longer used."""
    import warnings

    warnings.warn(
        "invoice_template_themes is deprecated. Invoice templates are no longer used.",
        DeprecationWarning,
        stacklevel=2,
    )
    return []  # Return empty list for backward compatibility
