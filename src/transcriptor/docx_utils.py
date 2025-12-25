from typing import List

import docx  # type: ignore


def extract_table_data_from_docx(docx_path: str) -> List[List[str]]:
    try:
        docx_file = docx.Document(docx_path)
    except ImportError:
        print("docx library not installed")
        return []
    except docx.opc.exceptions.PackageNotFoundError:
        print("Docx file not found")
        return []

    table_data: List[List[str]] = []
    for table in docx_file.tables:
        table_data.extend(
            [cell.text for cell in row.cells] for row in table.rows
        )
    return table_data
