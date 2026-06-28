#!/usr/bin/env python3
# coding: utf-8

import logging
from typing import Any

import config
from retrieval.es_client import get_es_client, ping_es

logger = logging.getLogger(__name__)


class DocRetriever:
    def __init__(self, top_k: int = 5):
        self.top_k = top_k

    @property
    def available(self) -> bool:
        return config.ES_ENABLED and ping_es()

    def search(self, question: str, disease_name: str | None = None) -> list[dict[str, Any]]:
        if not self.available:
            return []

        must = [
            {
                'multi_match': {
                    'query': question,
                    'fields': ['text^2', 'disease_name'],
                    'type': 'best_fields',
                },
            },
        ]
        if disease_name:
            must.append({'term': {'disease_name': disease_name}})

        body = {
            'size': self.top_k,
            'query': {'bool': {'must': must}},
        }
        try:
            resp = get_es_client().search(index=config.ES_INDEX_DOC, body=body)
        except Exception as exc:
            logger.warning('DocRetriever search failed: %s', exc)
            return []

        hits = resp.get('hits', {}).get('hits', [])
        return [hit.get('_source', {}) for hit in hits if hit.get('_source')]

    def format_context(self, chunks: list[dict[str, Any]]) -> str:
        parts = []
        for chunk in chunks:
            disease = chunk.get('disease_name', '')
            field = chunk.get('field', '')
            text = chunk.get('text', '')
            parts.append(f'【{disease}/{field}】{text}')
        return '\n\n'.join(parts)
