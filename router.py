#!/usr/bin/env python3
# coding: utf-8

import enum
import re


class RouteType(enum.Enum):
    META = 'meta'
    STRUCTURED = 'structured'
    OPEN = 'open'


META_PATTERNS = [
    r'你能(帮我)?做(些)?什么',
    r'你能(帮)?我什么',
    r'怎么用',
    r'如何使用',
    r'你是谁',
    r'你好',
    r'帮助',
    r'功能',
    r'可以问什么',
]

HELP_ANSWER = (
    '我是医疗知识图谱问答助手，可以回答例如：\n'
    '· 糖尿病有什么症状？\n'
    '· 百日咳怎么预防？\n'
    '· 阿莫西林主治什么病？\n'
    '请在问题中包含疾病、症状、药品等医疗实体，描述越具体越好。'
)


class QueryRouter:
    def route(self, question: str, classify_result: dict | None = None) -> RouteType:
        text = question.strip()
        if not text:
            return RouteType.META

        for pattern in META_PATTERNS:
            if re.search(pattern, text):
                return RouteType.META

        if classify_result and classify_result.get('question_types'):
            return RouteType.STRUCTURED

        if classify_result and classify_result.get('args'):
            return RouteType.OPEN

        return RouteType.OPEN
