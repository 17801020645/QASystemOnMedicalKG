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

# 口语化「描述 → 查病」问句
COLLOQUIAL_DISEASE_PATTERNS = [
    r'是什么病',
    r'啥病',
    r'什么病',
    r'哪种病',
    r'怎么回事',
    r'咋回事',
    r'像什么病',
    r'是不是.{0,6}病',
]

HELP_ANSWER = (
    '我是医疗知识图谱问答助手，可以回答例如：\n'
    '· 糖尿病有什么症状？\n'
    '· 百日咳怎么预防？\n'
    '· 阿莫西林主治什么病？\n'
    '· 血糖高是什么病？（口语描述也支持）\n'
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

        if self._should_use_rag_for_symptom_inquiry(text, classify_result):
            return RouteType.OPEN

        if classify_result and classify_result.get('question_types'):
            return RouteType.STRUCTURED

        if classify_result and classify_result.get('args'):
            return RouteType.OPEN

        return RouteType.OPEN

    def _should_use_rag_for_symptom_inquiry(
        self,
        question: str,
        classify_result: dict | None,
    ) -> bool:
        """口语化症状描述查病 → RAG；标准 symptom 查病仍走 Structured。"""
        if not classify_result or not classify_result.get('args'):
            return False

        args = classify_result['args']
        if any('disease' in types for types in args.values()):
            return False

        if not self._matches_colloquial_disease_pattern(question):
            return False

        symptom_entities = [name for name, types in args.items() if 'symptom' in types]
        if not symptom_entities:
            return False

        question_types = classify_result.get('question_types', [])

        # 多个症状组合描述 → RAG
        if len(symptom_entities) >= 2:
            return True

        # 仅 symptom_disease 兜底 intent，且为口语表达 → RAG
        if question_types == ['symptom_disease']:
            name = symptom_entities[0]
            if self._is_standard_symptom_disease_query(question, name):
                return False
            return self._is_colloquial_symptom_mention(question, name)

        return False

    @staticmethod
    def _matches_colloquial_disease_pattern(question: str) -> bool:
        return any(re.search(p, question) for p in COLLOQUIAL_DISEASE_PATTERNS)

    @staticmethod
    def _is_standard_symptom_disease_query(question: str, symptom_name: str) -> bool:
        """标准问法：头痛可能是什么病、胸痛是什么病"""
        escaped = re.escape(symptom_name)
        patterns = [
            rf'^{escaped}可能是什么病',
            rf'^{escaped}是什么病',
            rf'^{escaped}会是什么病',
            rf'^{escaped}是啥病',
            rf'症状{escaped}',
            rf'^{escaped}的疾病',
        ]
        return any(re.search(p, question) for p in patterns)

    @staticmethod
    def _is_colloquial_symptom_mention(question: str, symptom_name: str) -> bool:
        """症状词被口语修饰，如 血糖高、老是口渴。"""
        idx = question.find(symptom_name)
        if idx == -1:
            return True

        before = question[:idx]
        after = question[idx + len(symptom_name):]

        standard_after_prefixes = (
            '可能是什么病', '是什么病', '会是什么病', '是啥病', '的疾病', '怎么回事',
        )
        if idx == 0 and any(after.startswith(p) for p in standard_after_prefixes):
            return False

        # 前有修饰（老是、最近总…）→ 口语
        if before.strip():
            return True

        # 后有紧连汉字（血糖**高**）→ 口语
        if after and re.match(r'^[\u4e00-\u9fff]', after):
            if not any(after.startswith(p) for p in standard_after_prefixes):
                return True

        return False
