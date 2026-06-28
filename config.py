#!/usr/bin/env python3
# coding: utf-8

import os
from pathlib import Path

from dotenv import load_dotenv

_PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(_PROJECT_ROOT / '.env')

NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD', 'password')

DATA_PATH = _PROJECT_ROOT / 'data' / 'medical.json'
DICT_DIR = _PROJECT_ROOT / 'dict'

BATCH_SIZE = int(os.getenv('NEO4J_BATCH_SIZE', '500'))

# Elasticsearch
ES_HOST = os.getenv('ES_HOST', 'http://localhost:9200')
ES_INDEX_ENTITY = os.getenv('ES_INDEX_ENTITY', 'medical_entity')
ES_INDEX_DOC = os.getenv('ES_INDEX_DOC', 'medical_doc')
ES_ENABLED = os.getenv('ES_ENABLED', 'true').lower() in ('1', 'true', 'yes')
ENTITY_LINK_MIN_SCORE = float(os.getenv('ENTITY_LINK_MIN_SCORE', '3.0'))
ENTITY_LINK_TOP_K = int(os.getenv('ENTITY_LINK_TOP_K', '10'))

# LLM（阶段3 RAG）
LLM_API_KEY = os.getenv('LLM_API_KEY', '')
LLM_BASE_URL = os.getenv('LLM_BASE_URL', 'https://api.deepseek.com/v1')
LLM_MODEL = os.getenv('LLM_MODEL', 'deepseek-chat')
