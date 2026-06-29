#!/usr/bin/env python3
# coding: utf-8

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from question_classifier import QuestionClassifier
from router import QueryRouter, RouteType

CASES = [
    ('血糖高是什么病', RouteType.OPEN),
    ('多饮多尿是什么病', RouteType.OPEN),
    ('头痛可能是什么病', RouteType.STRUCTURED),
    ('胸痛是什么病', RouteType.STRUCTURED),
    ('糖尿病有什么症状', RouteType.STRUCTURED),
    ('什么是百日咳', RouteType.STRUCTURED),
    ('你能帮我做什么', RouteType.META),
    ('老是口渴是什么病', RouteType.OPEN),
]


def main():
    classifier = QuestionClassifier()
    router = QueryRouter()
    ok = 0
    for question, expected in CASES:
        classify_result = classifier.classify(question)
        got = router.route(question, classify_result)
        passed = got == expected
        ok += int(passed)
        status = 'OK' if passed else 'FAIL'
        print(f'{status} [{got.value}] {question}')
        if not passed:
            print(f'     expected={expected.value} types={classify_result.get("question_types")}')
    print(f'\n{ok}/{len(CASES)} passed')


if __name__ == '__main__':
    main()
