"""Render source-backed results locally without making model or database calls."""

import argparse
from pathlib import Path
import re

from jobmatch.matching.models import MatchingResult


def fenced_text(text: str) -> str:
    fence = "`" * (max([2] + [len(run) for run in re.findall(r"`+", text)]) + 1)
    return fence + "\n" + text + ("" if text.endswith("\n") else "\n") + fence


def render_matching_report(result: MatchingResult) -> str:
    """Keep citation review visible and suppress unsafe aggregate claims."""
    review = result.summary_review_required or bool(result.validation_warnings) or any(item.review_required for item in result.matches)
    lines = ["# JobMatch 匹配报告", "", "模型判断不等同于已独立核实的资格结论。", ""]
    if review:
        lines.extend(["## 需要复核", "", "部分引用或摘录覆盖尚待确认，暂不展示模型的总体优劣势和申请推荐。", ""])
    else:
        lines.extend(["## 总体结果", "", result.overall_summary, "", result.application_recommendation, ""])
        for title, items in (("优势", result.strengths), ("差距", result.gaps)):
            if items:
                lines.extend(["### " + title, ""] + ["- " + item for item in items] + [""])

    for match in result.matches:
        if match.review_required:
            citation_state = "需复核"
        elif not match.supporting_evidence:
            citation_state = "无可用引用"
        elif any(item.start_line is None or item.end_line is None for item in match.supporting_evidence):
            citation_state = "历史引用，未记录行号"
        else:
            citation_state = "出处与行号已校验"
        lines.extend([
            "## 要求 {}：{}".format(match.requirement_id, match.requirement.replace("\n", " ")),
            "", "状态：{}；引用：{}".format(match.status, citation_state),
            "", match.reason, "",
        ])
        if match.review_required and match.model_status is not None:
            lines.extend(["模型原始建议：{}（未经引用校验确认）".format(match.model_status), ""])
        for issue in match.citation_issues:
            lines.extend(["- 引用问题：{} — {}".format(issue.code, issue.message), ""])
        for citation in match.supporting_evidence:
            position = "第 {}–{} 行".format(citation.start_line, citation.end_line) if citation.start_line is not None else "历史引用，未记录行号"
            lines.extend([
                "来源：{} / {} / {} / {}".format(citation.source_type, citation.evidence_id, citation.source_file, position),
                "", fenced_text(citation.quote), "",
            ])
    if result.validation_warnings:
        lines.extend(["## 校验提示", ""] + ["- " + warning for warning in result.validation_warnings] + [""])
    return "\n".join(lines)


def write_matching_report(result: MatchingResult, output_path: str | Path) -> Path:
    """Save a potentially private report without overwriting an existing file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="") as report:
        report.write(render_matching_report(result))
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = MatchingResult.model_validate_json(args.input.read_text(encoding="utf-8"))
    saved = write_matching_report(result, args.output)
    print("Report saved to:", saved)
