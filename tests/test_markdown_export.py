"""Offline regression checks for merged-cell Markdown export."""

import unittest

from docling_core.types.doc import DoclingDocument
from docling_core.types.doc import TableCell
from docling_core.types.doc import TableData

from jobmatch.document.markdown import export_markdown


def cell(text, row, col, row_span=1, col_span=1):
    return TableCell(
        text=text,
        row_span=row_span,
        col_span=col_span,
        start_row_offset_idx=row,
        end_row_offset_idx=row + row_span,
        start_col_offset_idx=col,
        end_col_offset_idx=col + col_span,
    )


def document_with_table(cells, rows=3, cols=2):
    document = DoclingDocument(name="synthetic")
    document.add_table(data=TableData(num_rows=rows, num_cols=cols, table_cells=cells))
    return document


class MarkdownExportTests(unittest.TestCase):
    def test_column_span_is_emitted_once_without_mutating_source(self):
        document = document_with_table([
            cell("Role", 0, 0), cell("Date", 0, 1),
            cell("Synthetic Python project", 1, 0, col_span=2),
            cell("Team", 2, 0), cell("2025", 2, 1),
        ])
        original = document.model_dump()
        self.assertEqual(document.export_to_markdown().count("Synthetic Python project"), 2)
        result = export_markdown(document)
        self.assertEqual(result.count("Synthetic Python project"), 1)
        self.assertIn("| Synthetic Python project |  |", result)
        self.assertEqual(document.model_dump(), original)
        self.assertEqual(document.tables[0].data.table_cells[2].col_span, 2)

    def test_row_span_is_emitted_once(self):
        document = document_with_table([
            cell("Skill", 0, 0), cell("Level", 0, 1),
            cell("Synthetic skill", 1, 0, row_span=2),
            cell("Research", 1, 1), cell("Project", 2, 1),
        ])
        result = export_markdown(document)
        self.assertEqual(result.count("Synthetic skill"), 1)
        self.assertIn("Research", result)
        self.assertIn("Project", result)

    def test_distinct_cells_with_identical_text_are_preserved(self):
        document = document_with_table([
            cell("A", 0, 0), cell("B", 0, 1),
            cell("Same legitimate value", 1, 0), cell("Same legitimate value", 1, 1),
        ], rows=2)
        self.assertEqual(export_markdown(document).count("Same legitimate value"), 2)

    def test_combined_span_keeps_other_cells_and_table_dimensions(self):
        document = document_with_table([
            cell("A", 0, 0), cell("B", 0, 1), cell("C", 0, 2),
            cell("Merged description", 1, 0, row_span=2, col_span=2),
            cell("2024", 1, 2), cell("2025", 2, 2),
        ], cols=3)
        result = export_markdown(document)
        self.assertEqual(result.count("Merged description"), 1)
        self.assertEqual(len(result.splitlines()), 4)
        self.assertIn("2024", result)
        self.assertIn("2025", result)

    def test_numeric_precision_and_pipe_escaping_are_preserved(self):
        document = document_with_table([
            cell("Label", 0, 0), cell("Value", 0, 1),
            cell("A | B", 1, 0), cell("001.2300", 1, 1),
        ], rows=2)
        result = export_markdown(document)
        self.assertIn("001.2300", result)
        self.assertIn("A &#124; B", result)

    def test_document_without_tables_is_unchanged(self):
        document = DoclingDocument(name="empty")
        self.assertEqual(export_markdown(document), document.export_to_markdown())


if __name__ == "__main__":
    unittest.main()
