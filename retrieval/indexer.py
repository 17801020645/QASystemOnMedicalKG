#!/usr/bin/env python3
# coding: utf-8

import json
import logging
from pathlib import Path

import config
from retrieval.es_client import get_es_client

logger = logging.getLogger(__name__)

ENTITY_DICT_FILES = {
    'disease.txt': 'disease',
    'symptom.txt': 'symptom',
    'drug.txt': 'drug',
    'food.txt': 'food',
    'check.txt': 'check',
    'department.txt': 'department',
    'producer.txt': 'producer',
}

DRUG_SUFFIXES = (
    '克拉维酸钾分散片', '克拉维酸钾片', '克拉维酸钾干混悬剂', '克拉维酸钾',
    '缓释片', '肠溶片', '分散片', '胶囊', '颗粒', '片',
)

DOC_FIELDS = [
    'desc', 'cause', 'prevent', 'symptom', 'cure_way',
    'cure_lasttime', 'cured_prob', 'easy_get', 'check',
    'recommand_drug', 'drug_detail', 'not_eat', 'do_eat', 'recommand_eat',
]

ENTITY_INDEX_BODY = {
    'settings': {
        'number_of_shards': 1,
        'number_of_replicas': 0,
        'analysis': {
            'analyzer': {
                'ik_medical': {
                    'type': 'custom',
                    'tokenizer': 'ik_max_word',
                },
            },
        },
    },
    'mappings': {
        'properties': {
            'name': {
                'type': 'text',
                'analyzer': 'ik_medical',
                'fields': {'keyword': {'type': 'keyword'}},
            },
            'type': {'type': 'keyword'},
            'aliases': {'type': 'text', 'analyzer': 'ik_medical'},
            'canonical_id': {'type': 'keyword'},
        },
    },
}

DOC_INDEX_BODY = {
    'settings': {
        'number_of_shards': 1,
        'number_of_replicas': 0,
        'analysis': {
            'analyzer': {
                'ik_medical': {
                    'type': 'custom',
                    'tokenizer': 'ik_max_word',
                },
            },
        },
    },
    'mappings': {
        'properties': {
            'disease_name': {'type': 'keyword'},
            'field': {'type': 'keyword'},
            'text': {'type': 'text', 'analyzer': 'ik_medical'},
            'chunk_id': {'type': 'keyword'},
        },
    },
}


def _aliases_for_name(name: str, entity_type: str) -> list[str]:
    aliases: list[str] = []
    if entity_type in ('drug', 'producer', 'check'):
        for suffix in DRUG_SUFFIXES:
            if name.endswith(suffix) and len(name) > len(suffix) + 1:
                core = name[:-len(suffix)]
                if len(core) >= 2:
                    aliases.append(core)
                break
    return list(dict.fromkeys(aliases))


def _load_dict_entities() -> list[dict]:
    entities: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for filename, entity_type in ENTITY_DICT_FILES.items():
        path = config.DICT_DIR / filename
        if not path.exists():
            continue
        for line in path.read_text(encoding='utf-8').splitlines():
            name = line.strip()
            if not name:
                continue
            key = (name, entity_type)
            if key in seen:
                continue
            seen.add(key)
            entities.append({
                'name': name,
                'type': entity_type,
                'aliases': _aliases_for_name(name, entity_type),
                'canonical_id': f'{entity_type}:{name}',
            })
    return entities


def _field_to_text(value) -> str:
    if value is None:
        return ''
    if isinstance(value, list):
        return '；'.join(str(v) for v in value if v)
    return str(value)


def _load_doc_chunks() -> list[dict]:
    chunks: list[dict] = []
    if not config.DATA_PATH.exists():
        return chunks

    with config.DATA_PATH.open(encoding='utf-8') as fh:
        for line_no, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                logger.warning('Skip invalid JSON at line %s', line_no)
                continue

            disease_name = record.get('name', '')
            if not disease_name:
                continue

            for field in DOC_FIELDS:
                text = _field_to_text(record.get(field))
                if not text:
                    continue
                chunks.append({
                    'disease_name': disease_name,
                    'field': field,
                    'text': text,
                    'chunk_id': f'{disease_name}:{field}',
                })
    return chunks


def _recreate_index(client, index_name: str, body: dict) -> None:
    if client.indices.exists(index=index_name):
        client.indices.delete(index=index_name)
    client.indices.create(index=index_name, body=body)


def _bulk_index(client, index_name: str, docs: list[dict], batch_size: int = 500) -> int:
    total = 0
    for start in range(0, len(docs), batch_size):
        batch = docs[start:start + batch_size]
        operations = []
        for doc in batch:
            operations.append({'index': {'_index': index_name}})
            operations.append(doc)
        if not operations:
            continue
        resp = client.bulk(operations=operations, refresh='wait_for')
        if resp.get('errors'):
            logger.warning('Bulk index had errors in batch starting at %s', start)
        total += len(batch)
    return total


def build_entity_index(recreate: bool = True) -> int:
    client = get_es_client()
    entities = _load_dict_entities()
    if recreate:
        _recreate_index(client, config.ES_INDEX_ENTITY, ENTITY_INDEX_BODY)
    return _bulk_index(client, config.ES_INDEX_ENTITY, entities)


def build_doc_index(recreate: bool = True) -> int:
    client = get_es_client()
    chunks = _load_doc_chunks()
    if recreate:
        _recreate_index(client, config.ES_INDEX_DOC, DOC_INDEX_BODY)
    return _bulk_index(client, config.ES_INDEX_DOC, chunks)


def build_all(recreate: bool = True) -> tuple[int, int]:
    entity_count = build_entity_index(recreate=recreate)
    doc_count = build_doc_index(recreate=recreate)
    return entity_count, doc_count


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    entity_n, doc_n = build_all(recreate=True)
    print(f'Indexed entities: {entity_n}, doc chunks: {doc_n}')
