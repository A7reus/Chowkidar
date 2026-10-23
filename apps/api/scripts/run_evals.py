"""Run the deterministic golden-set evaluation against the seeded database.

Usage:
    cd apps/api && uv run python -m scripts.run_evals
"""

from __future__ import annotations

import asyncio

from app.db.session import AsyncSessionLocal
from app.services.evals import run_evals


async def main() -> None:
    async with AsyncSessionLocal() as session:
        summary = await run_evals(session)
        await session.commit()

    print(f"{summary.name}: {summary.passed_cases}/{summary.total_cases} cases passed")
    print(f"  extraction accuracy : {summary.extraction_accuracy:.3f}")
    print(f"  citation coverage   : {summary.citation_coverage:.3f}")
    print(f"  verifier pass rate  : {summary.verifier_pass_rate:.3f}")
    print(f"  no legal advice     : {summary.no_legal_advice_rate:.3f}")
    print(f"  priority agreement  : {summary.priority_agreement:.3f}")
    for result in summary.results:
        mark = "PASS" if result.passed else "FAIL"
        print(f"  [{mark}] {result.case_id}")
        for note in result.notes:
            print(f"         {note}")


if __name__ == "__main__":
    asyncio.run(main())
