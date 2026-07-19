"""GUI-independent controller for the OpenAI opportunity-analysis workflow.

The desktop GUI (and any future web UI) calls this controller instead of doing
business logic inline. It:

* builds an :class:`AnalysisRequest` from a selected ranked record + active
  preset + the deterministic evidence,
* runs the analysis (deterministic evidence is always preserved),
* produces a render-ready view that keeps the deterministic conclusions and the
  AI's advisory conclusions in clearly separate sections, and
* saves/exports the combined result.

No tkinter import.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from tenderfinder_ai_analysis import (
    AiAnalysisResult,
    AnalysisConfig,
    AnalysisRequest,
    DeterministicEvidence,
    STATUS_CACHED,
    STATUS_OK,
    STATUS_SETUP_REQUIRED,
    analyze_opportunity,
    public_record_fields,
)
from tenderfinder_presets import ContractorPreset


def build_request_from_record(
    record: dict[str, Any],
    preset: ContractorPreset,
    evidence: DeterministicEvidence,
    *,
    record_id: str | None = None,
) -> AnalysisRequest:
    rid = record_id or str(
        record.get("record_id")
        or record.get("lead_id")
        or record.get("app_no")
        or record.get("tender_title")
        or "unknown_record"
    )
    return AnalysisRequest(
        record_id=rid,
        public_fields=public_record_fields(record),
        profile_id=preset.preset_id,
        profile_name=preset.display_name,
        profile_description=preset.description,
        deterministic=evidence,
    )


@dataclass(frozen=True)
class AnalysisView:
    """Render-ready separation of deterministic vs AI conclusions."""

    status: str
    record_id: str
    deterministic_section: dict[str, Any]
    ai_section: dict[str, Any] | None
    disagreement: dict[str, Any] | None
    provenance: dict[str, Any]
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "record_id": self.record_id,
            "deterministic_section": self.deterministic_section,
            "ai_section": self.ai_section,
            "disagreement": self.disagreement,
            "provenance": self.provenance,
            "message": self.message,
        }


class AiAnalysisController:
    """Thin, testable orchestration layer between the GUI and the AI service."""

    def __init__(
        self,
        *,
        config: AnalysisConfig | None = None,
        client_factory: Callable[[], Any] | None = None,
        state_root: str | Path | None = None,
        package_root: str | Path | None = None,
    ) -> None:
        self.config = config or AnalysisConfig.from_env()
        self.client_factory = client_factory
        self.state_root = state_root
        self.package_root = package_root

    def analyze(
        self,
        record: dict[str, Any],
        preset: ContractorPreset,
        evidence: DeterministicEvidence,
        *,
        record_id: str | None = None,
        use_cache: bool = True,
        cancel_event: Any = None,
    ) -> AiAnalysisResult:
        request = build_request_from_record(record, preset, evidence, record_id=record_id)
        return analyze_opportunity(
            request,
            config=self.config,
            client_factory=self.client_factory,
            state_root=self.state_root,
            package_root=self.package_root,
            use_cache=use_cache,
            cancel_event=cancel_event,
        )

    @staticmethod
    def build_view(result: AiAnalysisResult) -> AnalysisView:
        """Compose the render view. Deterministic evidence is authoritative and
        is presented unchanged, separate from the AI's advisory conclusions."""
        deterministic_section = {
            "title": "Deterministic result (authoritative)",
            "fit_score": result.deterministic.get("fit_score"),
            "routing_bucket": result.deterministic.get("routing_bucket"),
            "matched_positive_terms": result.deterministic.get("matched_positive_terms", []),
            "matched_negative_terms": result.deterministic.get("matched_negative_terms", []),
        }
        provenance = {
            "model": result.model,
            "prompt_version": result.prompt_version,
            "schema_version": result.schema_version,
            "cached": result.cached,
            "generated_at": result.generated_at,
        }

        if result.status == STATUS_SETUP_REQUIRED:
            return AnalysisView(
                status=result.status, record_id=result.record_id,
                deterministic_section=deterministic_section, ai_section=None,
                disagreement=None, provenance=provenance,
                message=result.setup_instructions,
            )
        if not result.ok:
            return AnalysisView(
                status=result.status, record_id=result.record_id,
                deterministic_section=deterministic_section, ai_section=None,
                disagreement=None, provenance=provenance,
                message=f"AI analysis unavailable ({result.error_kind}): {result.error_message}",
            )

        analysis = result.analysis or {}
        ai_section = {
            "title": "AI advisory analysis (does not change the score or bucket)",
            "project_summary": analysis.get("project_summary", ""),
            "match_assessment": analysis.get("match_assessment", ""),
            "recommended_action": analysis.get("recommended_action", ""),
            "positive_factors": analysis.get("positive_factors", []),
            "negative_factors": analysis.get("negative_factors", []),
            "eligibility_uncertainties": analysis.get("eligibility_uncertainties", []),
            "missing_information": analysis.get("missing_information", []),
            "potential_scope": analysis.get("potential_scope", []),
            "next_steps": analysis.get("next_steps", []),
            "confidence": analysis.get("confidence", ""),
            "limitations": analysis.get("limitations", []),
        }
        message = "Cached AI analysis." if result.status == STATUS_CACHED else "AI analysis complete."
        return AnalysisView(
            status=result.status, record_id=result.record_id,
            deterministic_section=deterministic_section, ai_section=ai_section,
            disagreement=result.disagreement, provenance=provenance, message=message,
        )

    @staticmethod
    def export_result(result: AiAnalysisResult, destination: str | Path) -> Path:
        """Write the combined deterministic + AI analysis to a JSON file."""
        view = AiAnalysisController.build_view(result)
        dest = Path(destination)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(
            json.dumps(view.to_dict(), indent=2, ensure_ascii=False, default=str) + "\n",
            encoding="utf-8",
        )
        return dest

    @staticmethod
    def export_markdown(result: AiAnalysisResult, destination: str | Path) -> Path:
        """Write an estimator-friendly Markdown summary."""
        view = AiAnalysisController.build_view(result)
        det = view.deterministic_section
        lines = [
            f"# Opportunity analysis — {view.record_id}",
            "",
            "## Deterministic result (authoritative)",
            f"- Fit score: {det.get('fit_score')}",
            f"- Routing bucket: {det.get('routing_bucket')}",
            f"- Matched positive terms: {', '.join(det.get('matched_positive_terms', [])) or '—'}",
            f"- Matched negative terms: {', '.join(det.get('matched_negative_terms', [])) or '—'}",
            "",
        ]
        if view.ai_section:
            ai = view.ai_section
            lines += [
                "## AI advisory analysis (does not change the score or bucket)",
                f"- Match assessment: {ai.get('match_assessment')}",
                f"- Recommended action: {ai.get('recommended_action')}",
                f"- Confidence: {ai.get('confidence')}",
                "",
                f"**Project summary:** {ai.get('project_summary', '')}",
                "",
                "**Positive factors:**",
            ]
            lines += [
                f"- {f.get('factor')} (evidence: {f.get('evidence_field')} = {f.get('evidence_value')})"
                for f in ai.get("positive_factors", [])
            ] or ["- —"]
            lines += ["", "**Negative factors:**"]
            lines += [
                f"- {f.get('factor')} (evidence: {f.get('evidence_field')} = {f.get('evidence_value')})"
                for f in ai.get("negative_factors", [])
            ] or ["- —"]
            lines += ["", "**Eligibility uncertainties:**"]
            lines += [
                f"- {u.get('question')} — {u.get('reason')}"
                for u in ai.get("eligibility_uncertainties", [])
            ] or ["- —"]
            lines += ["", "**Missing information:**"]
            lines += [f"- {item}" for item in ai.get("missing_information", [])] or ["- —"]
            lines += ["", "**Next steps:**"]
            lines += [f"- {item}" for item in ai.get("next_steps", [])] or ["- —"]
            lines += [f"", f"_Model: {view.provenance.get('model')} · prompt {view.provenance.get('prompt_version')} · schema {view.provenance.get('schema_version')} · cached: {view.provenance.get('cached')}_"]
        else:
            lines += [f"_AI analysis unavailable: {view.message}_"]
        if view.disagreement:
            lines += [
                "",
                "## Disagreement (requires human review)",
                f"- Deterministic bucket: {view.disagreement.get('deterministic_bucket')}",
                f"- AI recommended action: {view.disagreement.get('ai_recommended_action')}",
                f"- {view.disagreement.get('note')}",
            ]
        dest = Path(destination)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return dest
