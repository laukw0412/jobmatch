"""Exercise the desktop journey with synthetic documents and no cloud/network access."""

import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from pathlib import Path
import socket
from tempfile import TemporaryDirectory
import time
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock
from unittest.mock import patch

from PySide6.QtCore import QTimer
from PySide6.QtCore import Qt
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import QApplication

from jobmatch.document import context
from jobmatch.ui.app import MainWindow
from jobmatch.ui import service


class DesktopFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def wait_for_task(self, window):
        deadline = time.monotonic() + 45
        while window.worker is not None and time.monotonic() < deadline:
            self.app.processEvents()
            # release the GIL while worker-thread imports and Python callbacks run
            time.sleep(0.01)
        self.assertIsNone(window.worker, "Background task did not finish")

    def test_complete_desktop_analysis_cache_reuse_review_and_error_recovery(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            documents = root / "documents"
            documents.mkdir()
            (documents / "resume.txt").write_text("Python development.\nPyTorch model training.", encoding="utf-8")
            (documents / "certificate.txt").write_text("English written and spoken communication.", encoding="utf-8")
            sdk = MagicMock()
            sdk.embeddings.create.side_effect = lambda **kwargs: SimpleNamespace(data=[SimpleNamespace(embedding=[1.0, 0.0]) for text in kwargs["input"]])

            def parse(**kwargs):
                if kwargs["response_format"].__name__ == "JobDescription":
                    value = {"job_title": "Synthetic engineer", "company_name": None, "location": None, "requirements": [
                        {"description": "Python and PyTorch or TensorFlow", "category": "technical_skill", "priority": "required"},
                        {"description": "English communication", "category": "language", "priority": "required"},
                    ]}
                else:
                    value = {"matches": [
                        {"requirement_id": 1, "status": "matched", "reason": "Synthetic source support", "supporting_evidence": [{"evidence_id": "core:1", "start_line": 1, "end_line": 2}]},
                        {"requirement_id": 2, "status": "matched", "reason": "Unconfirmed synthetic proposal", "supporting_evidence": [{"evidence_id": "rag:2:1", "start_line": 99, "end_line": 100}]},
                    ], "overall_summary": "UNSAFE_AGGREGATE", "application_recommendation": "UNSAFE_RECOMMENDATION"}
                parsed = kwargs["response_format"].model_validate(value)
                return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(parsed=parsed))])

            sdk.chat.completions.parse.side_effect = parse

            def runner(request, progress):
                return service.run_analysis(request, progress, documents_dir=documents, cache_root=root / "cache", report_root=root / "reports")

            with (
                patch.object(context, "DOCUMENTS_DIR", documents),
                patch.object(service, "create_api_client", return_value=sdk),
                patch.object(socket.socket, "connect", side_effect=AssertionError("Network forbidden")),
                patch.dict(os.environ, {"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"}),
            ):
                window = MainWindow(documents_dir=documents, analysis_runner=runner)
                try:
                    window.show()
                    self.app.processEvents()
                    self.assertFalse(window.analyze_button.isEnabled())
                    sdk.chat.completions.parse.assert_not_called()
                    for index in range(window.document_tree.topLevelItemCount()):
                        item = window.document_tree.topLevelItem(index)
                        item.setCheckState(1 if item.text(0) == "resume.txt" else 2, Qt.CheckState.Checked)
                    window.jd_edit.setPlainText("Synthetic JD: Python and English")
                    window.jd_confirm.setChecked(True)
                    window.api_consent.setChecked(True)
                    self.assertTrue(window.analyze_button.isEnabled())
                    screenshot_root = Path("data/test_outputs/gui_smoke")
                    screenshot_root.mkdir(parents=True, exist_ok=True)
                    self.app.processEvents()
                    self.assertTrue(window.grab().save(str(screenshot_root / "input.png")))
                    tick = []
                    window.analyze_button.click()
                    QTimer.singleShot(0, lambda: tick.append(True))
                    self.assertFalse(window.input_page.isEnabled())
                    self.wait_for_task(window)
                    self.assertTrue(tick)
                    self.assertIsNotNone(window.result, window.status_label.text())
                    self.assertEqual([item.status for item in window.result.matches], ["matched", "unknown"])
                    self.assertIn("需复核", window.review_banner.text())
                    self.assertNotIn("UNSAFE_", window.report_browser.toPlainText())
                    self.assertIn("Python", window.details.toPlainText())
                    self.assertIsNone(window.report_browser.loadResource(2, QUrl("https://example.com/image.png")))
                    self.assertEqual(sdk.embeddings.create.call_count, 3)
                    self.assertEqual(len(list((root / "reports").glob("*/review.md"))), 1)
                    self.app.processEvents()
                    self.assertTrue(window.grab().save(str(screenshot_root / "result.png")))

                    window.analyze_button.click()
                    self.wait_for_task(window)
                    self.assertIsNotNone(window.result, window.status_label.text())
                    self.assertEqual(sdk.embeddings.create.call_count, 5, "Unchanged certificate should not be embedded twice")
                    self.assertEqual(len(list((root / "reports").glob("*/result.json"))), 2)

                    sdk.chat.completions.parse.side_effect = RuntimeError("PRIVATE_SECRET_DO_NOT_DISPLAY")
                    window.analyze_button.click()
                    self.wait_for_task(window)
                    self.assertIsNone(window.result)
                    self.assertTrue(window.input_page.isEnabled())
                    self.assertIn("RuntimeError", window.status_label.text())
                    self.assertNotIn("PRIVATE_SECRET", window.status_label.text())
                    window.jd_edit.appendPlainText("Updated requirement")
                    self.assertFalse(window.jd_confirm.isChecked())
                    self.assertFalse(window.api_consent.isChecked())
                    self.assertFalse(window.analyze_button.isEnabled())
                finally:
                    if window.worker is not None:
                        window.worker.wait(45_000)
                        self.app.processEvents()
                    window.close()

    def test_url_failure_keeps_manual_input_and_success_requires_confirmation(self):
        with TemporaryDirectory() as directory, patch.object(socket.socket, "connect", side_effect=AssertionError("Network forbidden")):
            def failure(url, progress):
                raise ValueError("Private upstream response")

            window = MainWindow(documents_dir=Path(directory), url_fetcher=failure)
            try:
                window.jd_edit.setPlainText("Existing synthetic manual JD")
                window.jd_confirm.setChecked(True)
                window.url_edit.setText("https://example.com/job")
                window.fetch_button.click()
                self.wait_for_task(window)
                self.assertEqual(window.jd_edit.toPlainText(), "Existing synthetic manual JD")
                self.assertIn("粘贴", window.status_label.text())
                self.assertNotIn("Private upstream", window.status_label.text())
                window.url_fetcher = lambda url, progress: "New synthetic extracted JD"
                window.fetch_button.click()
                self.wait_for_task(window)
                self.assertEqual(window.jd_edit.toPlainText(), "New synthetic extracted JD")
                self.assertFalse(window.jd_confirm.isChecked())
                self.assertFalse(window.api_consent.isChecked())
            finally:
                window.close()


if __name__ == "__main__":
    unittest.main()
