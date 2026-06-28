#!/usr/bin/env python3
# coding: utf-8

import logging

from question_classifier import QuestionClassifier
from question_parser import QuestionPaser
from answer_search import AnswerSearcher

logger = logging.getLogger(__name__)

DEFAULT_ANSWER = (
    '您好，我是小勇医药智能助理，希望可以帮到您。'
    '如果没答上来，可联系https://liuhuanyong.github.io/。祝您身体棒棒！'
)


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
    while True:
        try:
            question = input('用户:')
            answer = handler.chat_main(question)
            print('小勇:', answer)
        except (KeyboardInterrupt, EOFError):
            print('\n再见！')
            break
