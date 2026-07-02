"""DeepEval quality gate (pytest), judged by Azure OpenAI.

Per golden question, runs the RAG pipeline once and asserts:
- **G-Eval correctness** vs the reference answer,
- **answer relevancy** and **faithfulness** to the retrieved context,
- low **bias** and **toxicity** in the output.

Run:  uv run pytest mecha_llm/eval/deepeval_tests.py
(Requires `uv sync --extra eval`, a populated index, and Azure creds in .env.)
"""

import asyncio
from functools import lru_cache

import pytest
from deepeval import assert_test
from deepeval.metrics import (
    AnswerRelevancyMetric,
    BiasMetric,
    FaithfulnessMetric,
    GEval,
    ToxicityMetric,
)
from deepeval.test_case import LLMTestCase, LLMTestCaseParams

from ._models import deepeval_model
from .dataset import GOLDEN
from .rag import answer


@lru_cache(maxsize=1)
def _judge():
    return deepeval_model()


@pytest.mark.parametrize("item", GOLDEN, ids=[g.question[:45] for g in GOLDEN])
def test_golden_item(item):
    result = asyncio.run(answer(item.question))
    test_case = LLMTestCase(
        input=item.question,
        actual_output=result.answer,
        expected_output=item.reference,
        retrieval_context=result.contexts,
    )

    judge = _judge()
    metrics = [
        GEval(
            name="Correctness",
            criteria=(
                "Determine whether the actual output is factually consistent with the "
                "expected output and does not contradict it or invent details."
            ),
            evaluation_params=[
                LLMTestCaseParams.INPUT,
                LLMTestCaseParams.ACTUAL_OUTPUT,
                LLMTestCaseParams.EXPECTED_OUTPUT,
            ],
            model=judge,
            threshold=0.6,
        ),
        AnswerRelevancyMetric(model=judge, threshold=0.6),
        FaithfulnessMetric(model=judge, threshold=0.6),
        BiasMetric(model=judge, threshold=0.5),
        ToxicityMetric(model=judge, threshold=0.5),
    ]
    assert_test(test_case, metrics)
