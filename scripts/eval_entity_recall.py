#!/usr/bin/env python3
# coding: utf-8

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from question_classifier import QuestionClassifier

CASES_PATH = ROOT / 'data' / 'eval_entity_cases.json'


def _match_expected(expected: set[str], result: set[str]) -> bool:
    if not expected:
        return not result
    for exp in expected:
        for got in result:
            if exp in got or got in exp:
                return True
    return bool(expected & result)


def _check_medical_ac_only(classifier: QuestionClassifier, question: str) -> dict:
    return classifier._check_medical_ac(question)


def _check_medical_es(classifier: QuestionClassifier, question: str) -> dict:
    if classifier.entity_linker.available:
        return classifier.entity_linker.link(question)
    return {}


def run_eval() -> dict:
    cases = json.loads(CASES_PATH.read_text(encoding='utf-8'))
    classifier = QuestionClassifier()

    ac_hits = 0
    es_hits = 0
    combined_hits = 0
    details = []

    for case in cases:
        question = case['question']
        expected = set(case.get('expected_entities', []))

        ac_result = set(_check_medical_ac_only(classifier, question).keys())
        es_result = set(_check_medical_es(classifier, question).keys())
        combined = set(classifier.check_medical(question).keys())

        ac_ok = _match_expected(expected, ac_result)
        es_ok = _match_expected(expected, es_result)
        combined_ok = _match_expected(expected, combined)

        ac_hits += int(ac_ok)
        es_hits += int(es_ok)
        combined_hits += int(combined_ok)

        details.append({
            'question': question,
            'expected': sorted(expected),
            'ac': sorted(ac_result),
            'es': sorted(es_result),
            'combined': sorted(combined),
            'ac_ok': ac_ok,
            'es_ok': es_ok,
            'combined_ok': combined_ok,
        })

    total = len(cases)
    summary = {
        'total': total,
        'ac_recall': ac_hits / total if total else 0,
        'es_recall': es_hits / total if total else 0,
        'combined_recall': combined_hits / total if total else 0,
        'details': details,
    }
    return summary


if __name__ == '__main__':
    result = run_eval()
    print(
        f"Total: {result['total']} | "
        f"AC: {result['ac_recall']:.1%} | "
        f"ES: {result['es_recall']:.1%} | "
        f"Combined: {result['combined_recall']:.1%}"
    )
    for item in result['details']:
        if not item['combined_ok']:
            print(f"FAIL: {item['question']}")
            print(f"  expected={item['expected']} got={item['combined']}")
