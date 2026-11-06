"""PySide6 desktop entry point; no parsing, database, or API activity at import."""

from pathlib import Path
import os
import sys

from PySide6.QtCore import QThread
from PySide6.QtCore import Qt
from PySide6.QtCore import Signal
from PySide6.QtCore import Slot
from PySide6.QtGui import QTextDocument
from PySide6.QtGui import QFont
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QApplication
from PySide6.QtWidgets import QCheckBox
from PySide6.QtWidgets import QFileDialog
from PySide6.QtWidgets import QHBoxLayout
from PySide6.QtWidgets import QHeaderView
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QLineEdit
from PySide6.QtWidgets import QMainWindow
from PySide6.QtWidgets import QMessageBox
from PySide6.QtWidgets import QPlainTextEdit
from PySide6.QtWidgets import QProgressBar
from PySide6.QtWidgets import QPushButton
from PySide6.QtWidgets import QSplitter
from PySide6.QtWidgets import QTabWidget
from PySide6.QtWidgets import QTableWidget
from PySide6.QtWidgets import QTableWidgetItem
from PySide6.QtWidgets import QTextBrowser
from PySide6.QtWidgets import QTreeWidget
from PySide6.QtWidgets import QTreeWidgetItem
from PySide6.QtWidgets import QVBoxLayout
from PySide6.QtWidgets import QWidget

from jobmatch.document.context import DOCUMENTS_DIR
from jobmatch.document.models import SUPPORTED_EXTENSIONS
from jobmatch.matching.report import render_matching_report
from jobmatch.matching.report import write_matching_report
from jobmatch.ui import service


STATUS_LABELS = {"matched": "已支持", "partial": "部分支持", "missing": "有明确不满足证据", "unknown": "证据不足"}


def configure_fonts(app):
    if app.property("jobmatchFontsConfigured"):
        return
    # the Windows offscreen platform may not discover system fonts automatically
    if app.platformName() == "offscreen" and os.name == "nt":
        font_root = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
        for name in ("msyh.ttc", "segoeui.ttf"):
            if (font_root / name).is_file():
                QFontDatabase.addApplicationFont(str(font_root / name))
    families = set(QFontDatabase.families())
    for family in ("Microsoft YaHei UI", "Microsoft YaHei", "Yu Gothic UI", "Segoe UI"):
        if family in families:
            app.setFont(QFont(family, 10))
            break
    app.setProperty("jobmatchFontsConfigured", True)


class ReportBrowser(QTextBrowser):
    def __init__(self):
        super().__init__()
        self.setOpenExternalLinks(False)
        self.setOpenLinks(False)

    def loadResource(self, resource_type, url):
        # reports are text-only; never fetch embedded remote or local resources
        return None

    def show_markdown(self, text):
        features = QTextDocument.MarkdownFeature.MarkdownDialectGitHub | QTextDocument.MarkdownFeature.MarkdownNoHTML
        self.document().setMarkdown(text, features)


class TaskThread(QThread):
    progress = Signal(str)
    succeeded = Signal(object)
    failed = Signal(str)

    def __init__(self, task, parent=None):
        super().__init__(parent)
        self.task = task

    def run(self):
        try:
            self.succeeded.emit(self.task(self.progress.emit))
        except Exception as exc:
            self.failed.emit(service.safe_error(exc))


class MainWindow(QMainWindow):
    def __init__(self, documents_dir=DOCUMENTS_DIR, analysis_runner=None, url_fetcher=None):
        super().__init__()
        configure_fonts(QApplication.instance())
        self.documents_dir = Path(documents_dir)
        self.analysis_runner = analysis_runner or service.run_analysis
        self.url_fetcher = url_fetcher or service.fetch_job_text
        self.worker = None
        self.task_kind = ""
        self.result = None
        self.setWindowTitle("JobMatch · 证据驱动的岗位匹配")
        self.resize(1120, 840)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 18, 24, 18)
        title = QLabel("JobMatch")
        title.setStyleSheet("font-size: 26px; font-weight: 700; color: #163a5f;")
        layout.addWidget(title)
        layout.addWidget(QLabel("选择资料，确认岗位描述，再查看有原文依据的匹配分析。"))
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs, 1)
        self.input_page = QWidget()
        inputs = QVBoxLayout(self.input_page)

        documents_header = QHBoxLayout()
        documents_header.addWidget(QLabel("1  选择本次资料（默认不勾选任何文件）"))
        documents_header.addStretch()
        self.refresh_button = QPushButton("刷新文档列表")
        self.refresh_button.clicked.connect(self.refresh_documents)
        documents_header.addWidget(self.refresh_button)
        inputs.addLayout(documents_header)
        self.document_tree = QTreeWidget()
        self.document_tree.setHeaderLabels(["文件", "核心全文", "补充检索"])
        self.document_tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.document_tree.setMinimumHeight(150)
        self.document_tree.itemChanged.connect(self.document_role_changed)
        inputs.addWidget(self.document_tree, 2)
        self.document_hint = QLabel("核心资料完整参与分析；补充资料建立可复用的独立分析缓存。不改动原文件和现有知识库。")
        self.document_hint.setWordWrap(True)
        inputs.addWidget(self.document_hint)

        inputs.addWidget(QLabel("2  输入并确认岗位描述"))
        url_row = QHBoxLayout()
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("可选：粘贴 HTTPS 招聘网址，再点击提取")
        self.fetch_button = QPushButton("提取网页 JD")
        self.fetch_button.clicked.connect(self.fetch_url)
        self.url_edit.textChanged.connect(self.update_actions)
        url_row.addWidget(self.url_edit, 1)
        url_row.addWidget(self.fetch_button)
        inputs.addLayout(url_row)
        self.jd_edit = QPlainTextEdit()
        self.jd_edit.setPlaceholderText("直接粘贴完整 JD，或提取后在这里检查、修改。网址提取失败时仍可手动输入。")
        self.jd_edit.textChanged.connect(self.jd_changed)
        inputs.addWidget(self.jd_edit, 3)
        self.jd_confirm = QCheckBox("我已检查并确认 JD 内容完整、正确")
        self.jd_confirm.toggled.connect(self.update_actions)
        inputs.addWidget(self.jd_confirm)

        options = QHBoxLayout()
        options.addWidget(QLabel("OpenAI 模型"))
        self.model_edit = QLineEdit("gpt-4.1-mini")
        self.model_edit.setMaximumWidth(280)
        self.model_edit.textChanged.connect(self.model_changed)
        options.addWidget(self.model_edit)
        options.addStretch()
        inputs.addLayout(options)
        self.api_consent = QCheckBox("我同意将本次勾选材料的文本和 JD 发送至 OpenAI 官方 API，可能含个人信息并产生费用")
        self.api_consent.toggled.connect(self.update_actions)
        inputs.addWidget(self.api_consent)
        costs = QLabel("调用包含：新补充资料的 Embedding、JD 提取、逐条检索和一次匹配。未变化的补充资料复用缓存；当前未设置费用硬上限。")
        costs.setWordWrap(True)
        costs.setStyleSheet("color: #5c6674;")
        inputs.addWidget(costs)
        self.analyze_button = QPushButton("开始匹配分析")
        self.analyze_button.setStyleSheet("background: #2068a8; color: white; padding: 9px; font-weight: 600;")
        self.analyze_button.clicked.connect(self.start_analysis)
        inputs.addWidget(self.analyze_button)
        self.tabs.addTab(self.input_page, "资料与 JD")

        results_page = QWidget()
        results_layout = QVBoxLayout(results_page)
        self.review_banner = QLabel("尚未开始分析。")
        self.review_banner.setWordWrap(True)
        results_layout.addWidget(self.review_banner)
        splitter = QSplitter(Qt.Orientation.Vertical)
        self.results_table = QTableWidget(0, 4)
        self.results_table.setHorizontalHeaderLabels(["编号", "岗位要求", "判断", "引用状态"])
        self.results_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.results_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.results_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.results_table.itemSelectionChanged.connect(self.show_selected_requirement)
        self.details = ReportBrowser()
        splitter.addWidget(self.results_table)
        splitter.addWidget(self.details)
        results_layout.addWidget(splitter, 1)
        self.tabs.addTab(results_page, "逐条结果与证据")

        report_page = QWidget()
        report_layout = QVBoxLayout(report_page)
        self.report_location = QLabel("分析完成后会自动保存本地 JSON 和 Markdown 报告。")
        self.report_location.setWordWrap(True)
        report_layout.addWidget(self.report_location)
        self.report_browser = ReportBrowser()
        report_layout.addWidget(self.report_browser, 1)
        self.export_button = QPushButton("另存 Markdown 报告")
        self.export_button.clicked.connect(self.export_report)
        report_layout.addWidget(self.export_button)
        self.tabs.addTab(report_page, "本地报告")

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        self.status_label = QLabel("就绪。启动程序不会读取文档正文或调用 API。")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        self.setCentralWidget(container)
        self.setStyleSheet("QMainWindow { background: #f3f6fa; } QTabWidget::pane { background: white; border: 1px solid #d6dfe9; } QLineEdit, QPlainTextEdit, QTreeWidget, QTableWidget, QTextBrowser { background: white; } QPushButton { min-height: 26px; } QTabBar::tab { padding: 9px 16px; }")
        self.refresh_documents()

    def selected_paths(self, column):
        return tuple(
            Path(item.data(0, Qt.ItemDataRole.UserRole))
            for item in (self.document_tree.topLevelItem(i) for i in range(self.document_tree.topLevelItemCount()))
            if item.checkState(column) == Qt.CheckState.Checked
        )

    @Slot()
    def refresh_documents(self):
        self.document_tree.blockSignals(True)
        self.document_tree.clear()
        if self.documents_dir.is_dir():
            root = self.documents_dir.resolve()
            for path in sorted(self.documents_dir.rglob("*")):
                if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS and path.resolve().is_relative_to(root):
                    item = QTreeWidgetItem([str(path.relative_to(self.documents_dir)), "", ""])
                    item.setData(0, Qt.ItemDataRole.UserRole, str(path.resolve()))
                    item.setCheckState(1, Qt.CheckState.Unchecked)
                    item.setCheckState(2, Qt.CheckState.Unchecked)
                    self.document_tree.addTopLevelItem(item)
        self.document_tree.blockSignals(False)
        self.api_consent.setChecked(False)
        self.clear_result()
        self.update_actions()

    @Slot(QTreeWidgetItem, int)
    def document_role_changed(self, item, column):
        if column in (1, 2) and item.checkState(column) == Qt.CheckState.Checked:
            self.document_tree.blockSignals(True)
            item.setCheckState(3 - column, Qt.CheckState.Unchecked)
            self.document_tree.blockSignals(False)
        self.api_consent.setChecked(False)
        self.clear_result()
        self.update_actions()

    @Slot()
    def jd_changed(self):
        self.jd_confirm.setChecked(False)
        self.api_consent.setChecked(False)
        self.clear_result()
        self.update_actions()

    @Slot()
    def model_changed(self):
        self.api_consent.setChecked(False)
        self.clear_result()
        self.update_actions()

    def clear_result(self):
        self.result = None
        if hasattr(self, "results_table"):
            self.results_table.setRowCount(0)
            self.details.clear()
            self.report_browser.clear()
            self.review_banner.setText("输入已变化，请重新分析。")
            self.report_location.setText("分析完成后自动保存本地报告。")

    @Slot()
    def update_actions(self):
        busy = self.worker is not None
        cores = self.selected_paths(1)
        supplements = self.selected_paths(2)
        ready = bool(cores and supplements and self.jd_edit.toPlainText().strip() and self.model_edit.text().strip() and self.jd_confirm.isChecked() and self.api_consent.isChecked())
        self.document_hint.setText("文档目录：{}\n已选核心 {} 份／补充 {} 份，至少各一份。补充材料使用独立分析缓存；不改动原文件和现有知识库。".format(self.documents_dir, len(cores), len(supplements)))
        self.analyze_button.setEnabled(not busy and ready)
        self.fetch_button.setEnabled(not busy and bool(self.url_edit.text().strip()))
        if hasattr(self, "export_button"):
            self.export_button.setEnabled(not busy and self.result is not None)

    def start_task(self, kind, task):
        self.task_kind = kind
        self.worker = TaskThread(task, self)
        self.worker.progress.connect(self.status_label.setText)
        self.worker.succeeded.connect(self.task_succeeded)
        self.worker.failed.connect(self.task_failed)
        self.worker.finished.connect(self.task_finished)
        self.input_page.setEnabled(False)
        self.progress_bar.setRange(0, 0)
        self.status_label.setText("正在启动…")
        self.update_actions()
        self.worker.start()

    @Slot()
    def fetch_url(self):
        if self.worker is None:
            url = self.url_edit.text().strip()
            self.start_task("url", lambda progress: self.url_fetcher(url, progress))

    @Slot()
    def start_analysis(self):
        if self.worker is not None:
            return
        request = service.AnalysisRequest(
            self.jd_edit.toPlainText(), self.selected_paths(1), self.selected_paths(2),
            self.model_edit.text().strip(), self.jd_confirm.isChecked(), self.api_consent.isChecked(),
        )
        try:
            service.validate_request(request, self.documents_dir)
        except Exception as exc:
            self.status_label.setText(service.safe_error(exc))
            return
        self.clear_result()
        self.start_task("analysis", lambda progress: self.analysis_runner(request, progress))

    @Slot(object)
    def task_succeeded(self, value):
        if self.task_kind == "url":
            self.jd_edit.setPlainText(value)
            self.status_label.setText("JD 已提取，请编辑检查后确认。")
            return
        self.result = value.matching
        self.report_location.setText("本地报告：{}\n结果 JSON：{}".format(value.report_path, value.json_path))
        self.review_banner.setText("存在需复核项；模型总体推荐已被抑制，请查看引用问题。" if self.result.summary_review_required else "分析完成。出处校验不代表资格结论已独立核实。")
        self.results_table.setRowCount(len(self.result.matches))
        for row, match in enumerate(self.result.matches):
            values = [str(match.requirement_id), match.requirement, STATUS_LABELS[match.status], "需复核" if match.review_required else ("有原文引用" if match.supporting_evidence else "无可用引用")]
            for column, text in enumerate(values):
                item = QTableWidgetItem(text)
                item.setToolTip(text)
                self.results_table.setItem(row, column, item)
        self.report_browser.show_markdown(render_matching_report(self.result))
        if self.result.matches:
            self.results_table.selectRow(0)
        self.tabs.setCurrentIndex(1)
        self.status_label.setText("分析完成，结果已保存到本机。")

    @Slot()
    def show_selected_requirement(self):
        row = self.results_table.currentRow()
        if self.result is not None and 0 <= row < len(self.result.matches):
            detail = self.result.model_copy(update={"matches": [self.result.matches[row]]})
            self.details.show_markdown(render_matching_report(detail))

    @Slot(str)
    def task_failed(self, message):
        prefix = "网页提取失败，仍可直接粘贴 JD。 " if self.task_kind == "url" else "分析未完成。 "
        self.status_label.setText(prefix + message)

    @Slot()
    def task_finished(self):
        worker = self.worker
        self.worker = None
        self.input_page.setEnabled(True)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100 if self.result is not None else 0)
        self.update_actions()
        worker.deleteLater()

    @Slot()
    def export_report(self):
        if self.result is None:
            return
        path, _ = QFileDialog.getSaveFileName(self, "另存本地报告", "jobmatch_report.md", "Markdown (*.md)", options=QFileDialog.Option.DontConfirmOverwrite)
        if path:
            try:
                write_matching_report(self.result, path)
                self.status_label.setText("报告已保存：" + path)
            except FileExistsError:
                self.status_label.setText("文件已存在，请选择新文件名；未覆盖原文件。")
            except Exception as exc:
                self.status_label.setText(service.safe_error(exc))

    def closeEvent(self, event):
        if self.worker is not None:
            QMessageBox.information(self, "任务仍在运行", "请等待当前任务结束后关闭窗口，避免中断正在进行的请求。")
            event.ignore()
        else:
            event.accept()


def main():
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("JobMatch")
    window = MainWindow()
    window.show()
    return app.exec()
