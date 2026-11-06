from docling_core.types.doc import DoclingDocument


def export_markdown(document: DoclingDocument) -> str:
    """Render merged cells once, leaving covered Markdown positions empty."""
    export_document = document.model_copy()
    tables = []
    for table in document.tables:
        cells = []
        for cell in table.data.table_cells:
            # Markdown cannot express spans; keep text only at the cell's origin
            cells.append(cell.model_copy(update={
                "row_span": 1,
                "col_span": 1,
                "end_row_offset_idx": cell.start_row_offset_idx + 1,
                "end_col_offset_idx": cell.start_col_offset_idx + 1,
            }))
        data = table.data.model_copy(update={"table_cells": cells})
        tables.append(table.model_copy(update={"data": data}))

    # replace only export-time table objects, preserving the parsed source document
    export_document.tables = tables
    return export_document.export_to_markdown(compact_tables=True, traverse_pictures=True)
