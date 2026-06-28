#!/usr/bin/env python3
# coding: utf-8

import logging

from elasticsearch import Elasticsearch

import config

logger = logging.getLogger(__name__)

_client: Elasticsearch | None = None


def get_es_client() -> Elasticsearch:
    global _client
    if _client is None:
        _client = Elasticsearch(config.ES_HOST, request_timeout=30)
    return _client


def ping_es() -> bool:
    try:
        return bool(get_es_client().ping())
    except Exception as exc:
        logger.debug('Elasticsearch ping failed: %s', exc)
        return False
