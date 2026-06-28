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
