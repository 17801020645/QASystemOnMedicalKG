#!/usr/bin/env python3
# coding: utf-8

from contextlib import contextmanager

from neo4j import GraphDatabase, Driver

from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

_driver: Driver | None = None


def get_driver() -> Driver:
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASSWORD),
        )
    return _driver


def close_driver() -> None:
    global _driver
    if _driver is not None:
        _driver.close()
        _driver = None


@contextmanager
def neo4j_session():
    session = get_driver().session()
    try:
        yield session
    finally:
        session.close()
