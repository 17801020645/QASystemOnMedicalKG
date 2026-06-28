#!/usr/bin/env python3
# coding: utf-8

import logging

import config

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    '你是医疗知识问答助手。仅根据提供的参考资料回答，不要编造。'
    '若资料不足，请明确说明无法从现有资料得出结论。'
    '回答简洁、分点，并提醒用户咨询专业医生。'
)


class AnswerGenerator:
    def __init__(self):
        self._client = None

    @property
    def available(self) -> bool:
        return bool(config.LLM_API_KEY)

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(
                api_key=config.LLM_API_KEY,
                base_url=config.LLM_BASE_URL,
            )
        return self._client

    def generate(self, question: str, context: str, graph_context: str = '') -> str:
        if not self.available:
            return self._fallback(question, context, graph_context)

        user_content = f'参考资料：\n{context}'
        if graph_context:
            user_content += f'\n\n图谱事实：\n{graph_context}'
        user_content += f'\n\n用户问题：{question}'

        try:
            resp = self._get_client().chat.completions.create(
                model=config.LLM_MODEL,
                messages=[
                    {'role': 'system', 'content': SYSTEM_PROMPT},
                    {'role': 'user', 'content': user_content},
                ],
                temperature=0.3,
            )
            return resp.choices[0].message.content.strip()
        except Exception as exc:
            logger.warning('LLM generate failed: %s', exc)
            return self._fallback(question, context, graph_context)

    @staticmethod
    def _fallback(question: str, context: str, graph_context: str = '') -> str:
        if graph_context:
            return f'根据图谱信息：\n{graph_context}\n\n参考资料：\n{context or "暂无"}'
        if context:
            return f'根据现有资料，关于「{question}」：\n{context}'
        return ''
