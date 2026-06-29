#!/usr/bin/env python3
# coding: utf-8

# 启用终端行编辑（退格、方向键、Ctrl+U 清空等）
try:
    import readline  # noqa: F401
except ImportError:
    pass

import logging
import sys

from graph.subgraph import SubgraphFetcher
from question_classifier import QuestionClassifier
from question_parser import QuestionPaser
from answer_search import AnswerSearcher
from rag.generator import AnswerGenerator
from rag.retriever import DocRetriever
from router import HELP_ANSWER, QueryRouter, RouteType

logger = logging.getLogger(__name__)

DEFAULT_ANSWER = (
    '您好，我是小勇医药智能助理，希望可以帮到您。'
    '如果没答上来，可联系https://liuhuanyong.github.io/。祝您身体棒棒！'
)

PROMPT = '用户: '


def read_question() -> str:
    """读取用户输入；非交互终端时回退到标准 input。"""
    if sys.stdin.isatty():
        return input(PROMPT)
    print(PROMPT, end='', flush=True)
    return sys.stdin.readline().rstrip('\n')


class ChatBotGraph:
    def __init__(self):
        self.classifier = QuestionClassifier()
        self.parser = QuestionPaser()
        self.searcher = AnswerSearcher()
        self.router = QueryRouter()
        self.doc_retriever = DocRetriever()
        self.generator = AnswerGenerator()
        self.subgraph = SubgraphFetcher()

    def chat_main(self, sent):
        classify_result = self.classifier.classify(sent)
        route = self.router.route(sent, classify_result)

        if route == RouteType.META:
            return HELP_ANSWER

        if route == RouteType.STRUCTURED:
            return self._answer_structured(classify_result)

        open_answer = self._answer_open(sent, classify_result)
        if open_answer:
            return open_answer

        logger.debug('未识别到可回答内容: %s', sent)
        return DEFAULT_ANSWER

    def _answer_structured(self, res_classify):
        res_sql = self.parser.parser_main(res_classify)
        final_answers = self.searcher.search_main(res_sql)
        if not final_answers:
            logger.debug('未查到答案: types=%s', res_classify.get('question_types'))
            return DEFAULT_ANSWER
        return '\n'.join(final_answers)

    def _answer_open(self, question, classify_result):
        args = classify_result.get('args', {})
        disease_name = None
        graph_context = ''

        for name, types in args.items():
            if 'disease' in types:
                disease_name = name
                break

        # 口语查病：优先用完整问句做文档检索，症状子图信息噪声较大
        symptom_only = args and all('symptom' in types for types in args.values())
        colloquial = self.router._should_use_rag_for_symptom_inquiry(question, classify_result)

        if args and not (symptom_only and colloquial):
            entity_name, entity_types = next(iter(args.items()))
            graph_context = self.subgraph.fetch(entity_name, entity_types)

        chunks = self.doc_retriever.search(question, disease_name=disease_name)
        context = self.doc_retriever.format_context(chunks)

        if self.generator.available:
            answer = self.generator.generate(question, context, graph_context)
            if answer:
                return answer

        if context or graph_context:
            parts = []
            if graph_context:
                parts.append(graph_context)
            if context:
                parts.append(context)
            return '\n\n'.join(parts)

        return ''


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    handler = ChatBotGraph()
    if sys.stdin.isatty():
        print('医疗问答已启动。输入医疗问题后按回车；')
        print('编辑：退格/方向键 | Ctrl+U 清空整行 | Ctrl+C 退出')
        print('中文输入法：请先确认选词（空格/回车）再按退格修改')
        print('-' * 50)
    while True:
        try:
            question = read_question()
            if not question.strip():
                continue
            answer = handler.chat_main(question)
            print('小勇:', answer)
        except (KeyboardInterrupt, EOFError):
            print('\n再见！')
            break
