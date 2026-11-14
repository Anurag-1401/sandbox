from __future__ import annotations

from app.core.config import settings
from app.modules.investigations.llm import InvestigationLLM
from app.modules.investigations.prompts import PLANNER_PROMPT


class PlannerAgent:

    def __init__(self, llm: InvestigationLLM):
        self.llm = llm

    def run(
        self,
        *,
        question: str,
        scope: dict,
    ) -> tuple[list[dict], list[str]]:

        response = self.llm.generate_json(
            system_prompt=PLANNER_PROMPT,
            user_prompt=(
                f"Investigation question:\n{question}\n\n"
                f"Investigation scope:\n{scope}\n\n"
                "Create the research plan."
            ),
        )

        raw_tasks = response.get("tasks", [])

        if not isinstance(raw_tasks, list):
            raise ValueError("Planner returned invalid tasks.")

        tasks = []
        seen_queries = set()

        for index, task in enumerate(
            raw_tasks[:settings.investigation_max_tasks],
            start=1,
        ):
            if not isinstance(task, dict):
                continue

            objective = str(task.get("objective", "")).strip()
            query = str(task.get("query", "")).strip()
            reason = str(task.get("reason", "")).strip()

            if not objective or not query:
                continue

            normalized = query.casefold()

            if normalized in seen_queries:
                continue

            seen_queries.add(normalized)

            tasks.append(
                {
                    "task_id": f"T{index}",
                    "objective": objective[:1000],
                    "query": query[:2000],
                    "reason": reason[:1000],
                }
            )

        if not tasks:
            # Safe deterministic fallback. The system remains usable
            # even if the model produces an unusable planning response.
            tasks = [
                {
                    "task_id": "T1",
                    "objective": "Find evidence relevant to the investigation.",
                    "query": question,
                    "reason": "Primary investigation question.",
                }
            ]

        limitations = response.get("limitations", [])

        if not isinstance(limitations, list):
            limitations = []

        return tasks, [
            str(item)[:1000]
            for item in limitations[:10]
        ]