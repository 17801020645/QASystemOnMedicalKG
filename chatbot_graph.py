#!/usr/bin/env python3
# coding: utf-8

# 启用终端行编辑（退格、方向键、Ctrl+U 清空等）
try:
    import readline  # noqa: F401
except ImportError:
    pass

import logging
import sys

from question_classifier import QuestionClassifier
from question_parser import QuestionPaser
from answer_search import AnswerSearcher

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

    def chat_main(self, sent):
        res_classify = self.classifier.classify(sent)
        if not res_classify:
            logger.debug('未识别到医疗实体: %s', sent)
            return DEFAULT_ANSWER
        res_sql = self.parser.parser_main(res_classify)
        final_answers = self.searcher.search_main(res_sql)
        if not final_answers:
            logger.debug('未查到答案: types=%s', res_classify.get('question_types'))
            return DEFAULT_ANSWER
        return '\n'.join(final_answers)


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
