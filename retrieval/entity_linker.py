#!/usr/bin/env python3
# coding: utf-8

import logging
import re
from difflib import SequenceMatcher
from typing import Any

import config
from retrieval.es_client import get_es_client, ping_es

logger = logging.getLogger(__name__)

MAX_ENTITIES = 3

SPAN_STOPWORDS = {
    '什么', '怎么', '哪些', '为什么', '如何', '原因', '症状', '疾病', '治疗',
    '预防', '检查', '用药', '怎么办', '能不能', '可以', '应该', '需要',
    '吗', '呢', '啊', '的', '了', '是', '有', '吗',
}


class EntityLinker:
    """基于 Elasticsearch 的医疗实体链接，输出格式与 check_medical 一致。"""

    def __init__(self, wdtype_dict: dict[str, list[str]] | None = None):
        self.wdtype_dict = wdtype_dict or {}
        self.min_score = config.ENTITY_LINK_MIN_SCORE
        self.top_k = config.ENTITY_LINK_TOP_K
        self._disease_names = [
            name for name, types in self.wdtype_dict.items() if 'disease' in types
        ]

    @property
    def available(self) -> bool:
        return config.ES_ENABLED and ping_es()

    def link(self, question: str) -> dict[str, list[str]]:
        if not question.strip() or not self.available:
            return {}

        spans = self._extract_spans(question)
        candidates: list[tuple[str, list[str], float]] = []

        for span in spans:
            try:
                hits = self._search(span)
            except Exception as exc:
                logger.warning('EntityLinker search failed: %s', exc)
                continue

            for hit in hits:
                score = hit.get('_score') or 0.0
                if score < self.min_score:
                    continue
                source = hit.get('_source', {})
                name = source.get('name') or ''
                if not name:
                    continue
                if not self._is_plausible_match(name, span, question):
                    continue
                types = self.wdtype_dict.get(name)
                if not types:
                    entity_type = source.get('type')
                    types = [entity_type] if entity_type else []
                if not types:
                    continue
                # 长 span 精确匹配加权
                span_bonus = len(span) * 0.5
                if span in name or name in span:
                    span_bonus += 5.0
                candidates.append((name, types, score + span_bonus))

            if candidates:
                break

        if not candidates:
            return self._fuzzy_dict_fallback(spans)

        deduped = self._dedupe_candidates(candidates)
        return dict(list(deduped.items())[:MAX_ENTITIES])

    def _fuzzy_dict_fallback(self, spans: list[str]) -> dict[str, list[str]]:
        """ES 未命中时的字形近似匹配（如 百曰咳 → 百日咳）。"""
        best_name = ''
        best_score = 0.65
        for span in spans:
            if len(span) < 3:
                continue
            for name in self._disease_names:
                sim = self._similarity(span, name)
                if sim > best_score:
                    best_score = sim
                    best_name = name
        if best_name:
            return {best_name: self.wdtype_dict[best_name]}
        return {}

    def _extract_spans(self, question: str) -> list[str]:
        spans: list[str] = []
        for part in re.findall(r'[\u4e00-\u9fffA-Za-z0-9]+', question):
            if part in SPAN_STOPWORDS or len(part) < 2:
                continue
            spans.append(part)
            if len(part) >= 4:
                for size in range(min(6, len(part)), 2, -1):
                    for i in range(len(part) - size + 1):
                        sub = part[i:i + size]
                        if sub not in SPAN_STOPWORDS:
                            spans.append(sub)
        spans.sort(key=len, reverse=True)
        return list(dict.fromkeys(spans))

    def _search(self, span: str) -> list[dict[str, Any]]:
        client = get_es_client()
        body = {
            'size': self.top_k,
            'query': {
                'bool': {
                    'should': [
                        {
                            'term': {
                                'name.keyword': {
                                    'value': span,
                                    'boost': 10.0,
                                },
                            },
                        },
                        {
                            'match': {
                                'aliases': {
                                    'query': span,
                                    'boost': 8.0,
                                    'fuzziness': 'AUTO',
                                },
                            },
                        },
                        {
                            'multi_match': {
                                'query': span,
                                'fields': ['name^3', 'aliases^2'],
                                'type': 'best_fields',
                                'fuzziness': 'AUTO',
                            },
                        },
                    ],
                    'minimum_should_match': 1,
                },
            },
        }
        resp = client.search(index=config.ES_INDEX_ENTITY, body=body)
        return resp.get('hits', {}).get('hits', [])

    @staticmethod
    def _similarity(a: str, b: str) -> float:
        return SequenceMatcher(None, a, b).ratio()

    def _is_plausible_match(self, name: str, span: str, question: str) -> bool:
        if name in question or span in name or name in span:
            return True
        if abs(len(span) - len(name)) <= 2 and self._similarity(name, span) >= 0.65:
            return True
        return False

    @staticmethod
    def _dedupe_candidates(
        candidates: list[tuple[str, list[str], float]],
    ) -> dict[str, list[str]]:
        candidates.sort(key=lambda item: (-item[2], -len(item[0])))
        names = [name for name, _, _ in candidates]
        stop_wds: set[str] = set()
        for wd1 in names:
            for wd2 in names:
                if wd1 != wd2 and wd1 in wd2:
                    stop_wds.add(wd1)

        result: dict[str, list[str]] = {}
        for name, types, _ in candidates:
            if name in stop_wds:
                continue
            if name not in result:
                result[name] = types
        return result
