"""Desktop orchestration with explicit inputs and an isolated reusable evidence cache."""

from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
from pathlib import Path
from zoneinfo import ZoneInfo

from jobmatch.document.context import DEFAULT_MAX_INPUT_CHARS
from jobmatch.document.context import DOCUMENTS_DIR
from jobmatch.document.models import SUPPORTED_EXTENSIONS
from jobmatch.matching.models import MatchingResult


PROJECT_ROOT = DOCUMENTS_DIR.parent.parent
CACHE_ROOT = PROJECT_ROOT / "data" / "cache" / "desktop_evidence"
REPORT_ROOT = PROJECT_ROOT / "data" / "test_outputs" / "desktop_runs"
CACHE_VERSION = "picture-text-v1"
COLLECTION_NAME = "jobmatch_desktop_evidence"


@dataclass(frozen=True)
class AnalysisRequest:
    jd_text: str
    core_paths: tuple[Path, ...]
    supplementary_paths: tuple[Path, ...]
    model: str = "gpt-4.1-mini"
    jd_confirmed: bool = False
    api_authorized: bool = False


@dataclass(frozen=True)
class DesktopResult:
    matching: MatchingResult
    report_path: Path
    json_path: Path


class AnalysisError(ValueError):
    """User-actionable desktop failure that contains no raw API payload."""


def validate_request(request: AnalysisRequest, documents_dir: Path = DOCUMENTS_DIR):
    if not request.jd_text.strip():
        raise AnalysisError("请粘贴或提取 JD 文本。")
    if not request.jd_confirmed:
        raise AnalysisError("请先检查并确认 JD；编辑后需要重新确认。")
    if not request.api_authorized:
        raise AnalysisError("请先确认本次所选材料的 OpenAI 数据发送与付费调用。")
    if not request.core_paths or not request.supplementary_paths:
        raise AnalysisError("至少选择一份核心文档和一份补充文档；补充文档用于实际 RAG 检索。")
    if not request.model.strip():
        raise AnalysisError("请填写模型名称。")
    root = documents_dir.resolve()
    cores = {path.resolve() for path in request.core_paths}
    supplements = {path.resolve() for path in request.supplementary_paths}
    if cores & supplements:
        raise AnalysisError("同一文档不能同时作为核心资料和补充资料。")
    for path in cores | supplements:
        if not path.is_relative_to(root) or not path.is_file() or path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            raise AnalysisError("所选文件不存在、类型不支持，或位于 data/documents/ 之外。")


def create_api_client():
    from dotenv import load_dotenv
    import httpx
    from openai import OpenAI

    load_dotenv()
    return OpenAI(
        base_url="https://api.openai.com/v1", max_retries=0, timeout=60,
        http_client=httpx.Client(trust_env=False),
    )


def safe_error(error: Exception) -> str:
    if isinstance(error, AnalysisError):
        return str(error)
    if type(error).__name__ == "AuthenticationError":
        return "OpenAI 认证失败，请检查本机 API 密钥配置。未自动重试。"
    if type(error).__name__ in {"APIConnectionError", "APITimeoutError", "RateLimitError"}:
        return "网络、请求超时或服务限流；本次已停止，未自动重试，已发出的请求可能产生费用。"
    return "操作失败（{}）。请检查所选文件、输入长度和服务配置；未自动重试。".format(type(error).__name__)


def fetch_job_text(url: str, progress):
    from jobmatch.jobs.web_extractor import extract_job_text_from_url

    progress("正在提取网页 JD；失败时可直接粘贴文本")
    return extract_job_text_from_url(url)


def run_analysis(request: AnalysisRequest, progress, *, documents_dir=DOCUMENTS_DIR, cache_root=CACHE_ROOT, report_root=REPORT_ROOT) -> DesktopResult:
    validate_request(request, documents_dir)
    from jobmatch.document.context import load_core_documents
    from jobmatch.jobs.extractor import extract_job_description
    from jobmatch.matching.analyzer import analyze_matches
    from jobmatch.matching.analyzer import SYSTEM_PROMPT
    from jobmatch.matching.report import write_matching_report
    from jobmatch.matching.retriever import retrieve_job_requirements
    from jobmatch.rag.indexing import calculate_file_hash
    from jobmatch.rag.indexing import index_document
    from jobmatch.rag.storage import create_chroma_client

    progress("读取所选核心资料")
    cores = []
    for path in dict.fromkeys(request.core_paths):
        try:
            cores.extend(load_core_documents([path]))
        except Exception as exc:
            raise AnalysisError("核心文档处理失败：{}（{}）。请检查文件。".format(path.name, type(exc).__name__)) from None
    if len(SYSTEM_PROMPT) + len(request.jd_text) + sum(len(item.text) for item in cores) > DEFAULT_MAX_INPUT_CHARS:
        raise AnalysisError("核心资料与 JD 超出当前上下文预算，请减少核心文档或精简 JD。")
    supplements = sorted({path.resolve() for path in request.supplementary_paths})
    signature = json.dumps([(str(path), calculate_file_hash(path)) for path in supplements]) + CACHE_VERSION
    cache_path = Path(cache_root) / hashlib.sha256(signature.encode("utf-8")).hexdigest() / "chroma"
    run_dir = Path(report_root) / datetime.now(ZoneInfo("Asia/Tokyo")).strftime("%Y%m%d_%H%M%S_%f")
    run_dir.mkdir(parents=True, exist_ok=False)
    client = create_api_client()
    try:
        with create_chroma_client(path=str(cache_path)) as database:
            collection = database.get_or_create_collection(COLLECTION_NAME, embedding_function=None)
            for index, path in enumerate(supplements, 1):
                progress("准备补充证据 {}/{}（未变化文件复用缓存）".format(index, len(supplements)))
                try:
                    status = index_document(path, collection, client)
                except Exception as exc:
                    raise AnalysisError("补充文档处理失败：{}（{}）。本次已停止。".format(path.name, type(exc).__name__)) from None
                if status == "empty":
                    raise AnalysisError("补充文档未提取到内容：{}。请检查文件。".format(path.name))
        progress("提取已确认 JD 的逐条要求")
        job = extract_job_description(request.jd_text, model=request.model, client=client)
        if not job.requirements:
            raise AnalysisError("未提取到岗位要求，请检查 JD 完整性并重新确认。")
        evidence = retrieve_job_requirements(
            job, top_k=3, strategy="source", chroma_path=str(cache_path), collection_name=COLLECTION_NAME,
            included_source_paths={str(path) for path in supplements},
            excluded_source_paths={item.source_path for item in cores}, client=client, progress=progress,
        )
        progress("结合完整核心资料和检索证据进行匹配")
        result = analyze_matches(evidence, model=request.model, core_documents=cores, confirmed_jd_text=request.jd_text, client=client)
        progress("保存本地结果与可审阅报告")
        report_path = write_matching_report(result, run_dir / "review.md")
        json_path = run_dir / "result.json"
        with json_path.open("x", encoding="utf-8", newline="") as output:
            output.write(result.model_dump_json(indent=2))
        return DesktopResult(result, report_path, json_path)
    finally:
        client.close()
