"""Print an inspectable hybrid-retrieval report for portfolio questions."""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from .retrieval import RetrievalIndex, preferred_kinds_for_question


DEFAULT_QUESTIONS = (
    "Tell me about Rahul's experience leading teams.",
    "What kinds of projects does Rahul build?",
    "What cloud and infrastructure work has Rahul done?",
    "What experience does Rahul have with mobile development?",
    "Which programming languages does Rahul use?",
)


def _default_data_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "data"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Show the chunks selected by portfolio hybrid retrieval."
    )
    parser.add_argument(
        "questions",
        nargs="*",
        help="Questions to inspect. Uses a representative set when omitted.",
    )
    parser.add_argument("--data", type=Path, default=_default_data_dir())
    parser.add_argument("--top-k", type=int, default=8)
    parser.add_argument("--show-text", action="store_true")
    return parser.parse_args()


async def _run(args: argparse.Namespace) -> None:
    index = RetrievalIndex.load(args.data)
    try:
        questions = args.questions or DEFAULT_QUESTIONS
        for question_number, question in enumerate(questions):
            if question_number:
                print()
            preferred_kinds = preferred_kinds_for_question(question)
            results = await index.search(
                question,
                limit=args.top_k,
                preferred_kinds=preferred_kinds or None,
            )
            print(f"Question: {question}")
            print(
                "Preferred kinds: "
                + (", ".join(sorted(preferred_kinds)) if preferred_kinds else "none")
            )
            for rank, result in enumerate(results, start=1):
                print(
                    f"{rank}. [{result.kind}] {result.heading} | "
                    f"semantic={result.score:.4f} "
                    f"lexical={result.lexical_score:.4f} "
                    f"hybrid={result.retrieval_score:.6f}"
                )
                if args.show_text:
                    print(f"   {result.text.replace(chr(10), ' ')}")
    finally:
        await index.close()


def main() -> None:
    asyncio.run(_run(parse_args()))


if __name__ == "__main__":
    main()
