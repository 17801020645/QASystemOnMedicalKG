#!/usr/bin/env python3
# coding: utf-8

from typing import Any

from graph.client import neo4j_session


def execute(cypher: str, parameters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    params = parameters or {}
    with neo4j_session() as session:
        result = session.run(cypher, params)
        return [record.data() for record in result]


def execute_write(cypher: str, parameters: dict[str, Any] | None = None) -> None:
    params = parameters or {}
    with neo4j_session() as session:
        session.run(cypher, params)
