#!/usr/bin/env python3
# coding: utf-8

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CypherQuery:
    cypher: str
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass
class AnswerContext:
    """结构化查询结果，供答案模板使用。"""

    subject: str
    items: list[str] = field(default_factory=list)
    rel_groups: dict[str, list[str]] = field(default_factory=dict)


def _dedupe_limit(items: list[str], limit: int) -> list[str]:
    seen = set()
    result = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
        if len(result) >= limit:
            break
    return result


def parse_query_results(question_type: str, rows: list[dict[str, Any]], limit: int = 20) -> AnswerContext | None:
    if not rows:
        return None

    if question_type == 'disease_symptom':
        return AnswerContext(
            subject=rows[0]['m.name'],
            items=_dedupe_limit([r['n.name'] for r in rows], limit),
        )

    if question_type == 'symptom_disease':
        return AnswerContext(
            subject=rows[0]['n.name'],
            items=_dedupe_limit([r['m.name'] for r in rows], limit),
        )

    if question_type in ('disease_cause', 'disease_prevent', 'disease_lasttime',
                         'disease_cureprob', 'disease_easyget', 'disease_desc'):
        key_map = {
            'disease_cause': 'm.cause',
            'disease_prevent': 'm.prevent',
            'disease_lasttime': 'm.cure_lasttime',
            'disease_cureprob': 'm.cured_prob',
            'disease_easyget': 'm.easy_get',
            'disease_desc': 'm.desc',
        }
        attr = key_map[question_type]
        return AnswerContext(
            subject=rows[0]['m.name'],
            items=_dedupe_limit([r[attr] for r in rows if r.get(attr)], limit),
        )

    if question_type == 'disease_cureway':
        items = []
        for r in rows:
            val = r.get('m.cure_way')
            if isinstance(val, list):
                items.append(';'.join(val))
            elif val:
                items.append(str(val))
        return AnswerContext(
            subject=rows[0]['m.name'],
            items=_dedupe_limit(items, limit),
        )

    if question_type == 'disease_acompany':
        subject = rows[0]['m.name']
        desc1 = [r['n.name'] for r in rows]
        desc2 = [r['m.name'] for r in rows]
        items = [i for i in desc1 + desc2 if i != subject]
        return AnswerContext(subject=subject, items=_dedupe_limit(items, limit))

    if question_type == 'disease_not_food':
        return AnswerContext(
            subject=rows[0]['m.name'],
            items=_dedupe_limit([r['n.name'] for r in rows], limit),
        )

    if question_type == 'disease_do_food':
        return AnswerContext(
            subject=rows[0]['m.name'],
            rel_groups={
                '宜吃': _dedupe_limit([r['n.name'] for r in rows if r.get('r.name') == '宜吃'], limit),
                '推荐食谱': _dedupe_limit([r['n.name'] for r in rows if r.get('r.name') == '推荐食谱'], limit),
            },
        )

    if question_type == 'food_not_disease':
        return AnswerContext(
            subject=rows[0]['n.name'],
            items=_dedupe_limit([r['m.name'] for r in rows], limit),
        )

    if question_type == 'food_do_disease':
        return AnswerContext(
            subject=rows[0]['n.name'],
            items=_dedupe_limit([r['m.name'] for r in rows], limit),
        )

    if question_type == 'disease_drug':
        return AnswerContext(
            subject=rows[0]['m.name'],
            items=_dedupe_limit([r['n.name'] for r in rows], limit),
        )

    if question_type == 'drug_disease':
        return AnswerContext(
            subject=rows[0]['n.name'],
            items=_dedupe_limit([r['m.name'] for r in rows], limit),
        )

    if question_type == 'disease_check':
        return AnswerContext(
            subject=rows[0]['m.name'],
            items=_dedupe_limit([r['n.name'] for r in rows], limit),
        )

    if question_type == 'check_disease':
        return AnswerContext(
            subject=rows[0]['n.name'],
            items=_dedupe_limit([r['m.name'] for r in rows], limit),
        )

    return None
