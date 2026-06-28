#!/usr/bin/env python3
# coding: utf-8

import logging

from graph.models import parse_query_results
from graph.repository import execute
from question_parser import QuestionPaser

logger = logging.getLogger(__name__)


class SubgraphFetcher:
    """为 GraphRAG 拉取实体相关的一跳子图事实。"""

    RELATION_QUERIES = {
        'disease': (
            'MATCH (m:Disease {name: $name})-[r]->(n) '
            'RETURN type(r) AS rel, labels(n)[0] AS target_label, n.name AS target_name '
            'LIMIT 30'
        ),
        'symptom': (
            'MATCH (m:Disease)-[:has_symptom]->(n:Symptom {name: $name}) '
            'RETURN "has_symptom" AS rel, "Disease" AS target_label, m.name AS target_name '
            'LIMIT 20'
        ),
        'drug': (
            'MATCH (m:Disease)-[r:common_drug|recommand_drug]->(n:Drug {name: $name}) '
            'RETURN type(r) AS rel, "Disease" AS target_label, m.name AS target_name '
            'LIMIT 20'
        ),
    }

    def fetch(self, entity_name: str, entity_types: list[str]) -> str:
        entity_type = entity_types[0] if entity_types else 'disease'
        cypher = self.RELATION_QUERIES.get(entity_type, self.RELATION_QUERIES['disease'])
        try:
            rows = execute(cypher, {'name': entity_name})
        except Exception as exc:
            logger.debug('Subgraph fetch failed: %s', exc)
            return ''

        if not rows:
            return ''

        lines = [f'实体：{entity_name}（{entity_type}）']
        for row in rows:
            rel = row.get('rel', '')
            label = row.get('target_label', '')
            target = row.get('target_name', '')
            lines.append(f'- {rel} -> {label}:{target}')
        return '\n'.join(lines)
