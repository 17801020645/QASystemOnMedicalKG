#!/usr/bin/env python3
# coding: utf-8

from graph.models import AnswerContext, parse_query_results
from graph.repository import execute


class AnswerSearcher:
    def __init__(self):
        self.num_limit = 20

    def search_main(self, sqls):
        final_answers = []
        for sql_ in sqls:
            question_type = sql_['question_type']
            queries = sql_['queries']
            answers = []
            for query in queries:
                cypher = query.cypher if hasattr(query, 'cypher') else query['cypher']
                params = query.parameters if hasattr(query, 'parameters') else query.get('parameters', {})
                answers += execute(cypher, params)
            final_answer = self.format_answer(question_type, answers)
            if final_answer:
                final_answers.append(final_answer)
        return final_answers

    def format_answer(self, question_type, rows):
        ctx = parse_query_results(question_type, rows, self.num_limit)
        if ctx is None:
            return ''
        return self._render(question_type, ctx)

    def _render(self, question_type: str, ctx: AnswerContext) -> str:
        joiner = '；'

        if question_type == 'disease_symptom':
            return f'{ctx.subject}的症状包括：{joiner.join(ctx.items)}'

        if question_type == 'symptom_disease':
            return f'症状{ctx.subject}可能染上的疾病有：{joiner.join(ctx.items)}'

        if question_type == 'disease_cause':
            return f'{ctx.subject}可能的成因有：{joiner.join(ctx.items)}'

        if question_type == 'disease_prevent':
            return f'{ctx.subject}的预防措施包括：{joiner.join(ctx.items)}'

        if question_type == 'disease_lasttime':
            return f'{ctx.subject}治疗可能持续的周期为：{joiner.join(ctx.items)}'

        if question_type == 'disease_cureway':
            return f'{ctx.subject}可以尝试如下治疗：{joiner.join(ctx.items)}'

        if question_type == 'disease_cureprob':
            return f'{ctx.subject}治愈的概率为（仅供参考）：{joiner.join(ctx.items)}'

        if question_type == 'disease_easyget':
            return f'{ctx.subject}的易感人群包括：{joiner.join(ctx.items)}'

        if question_type == 'disease_desc':
            return f'{ctx.subject},熟悉一下：{joiner.join(ctx.items)}'

        if question_type == 'disease_acompany':
            return f'{ctx.subject}的症状包括：{joiner.join(ctx.items)}'

        if question_type == 'disease_not_food':
            return f'{ctx.subject}忌食的食物包括有：{joiner.join(ctx.items)}'

        if question_type == 'disease_do_food':
            do_items = ';'.join(ctx.rel_groups.get('宜吃', []))
            rec_items = ';'.join(ctx.rel_groups.get('推荐食谱', []))
            return (
                f'{ctx.subject}宜食的食物包括有：{do_items}\n'
                f'推荐食谱包括有：{rec_items}'
            )

        if question_type == 'food_not_disease':
            return f'患有{joiner.join(ctx.items)}的人最好不要吃{ctx.subject}'

        if question_type == 'food_do_disease':
            return f'患有{joiner.join(ctx.items)}的人建议多试试{ctx.subject}'

        if question_type == 'disease_drug':
            return f'{ctx.subject}通常的使用的药品包括：{joiner.join(ctx.items)}'

        if question_type == 'drug_disease':
            return f'{ctx.subject}主治的疾病有{joiner.join(ctx.items)},可以试试'

        if question_type == 'disease_check':
            return f'{ctx.subject}通常可以通过以下方式检查出来：{joiner.join(ctx.items)}'

        if question_type == 'check_disease':
            return f'通常可以通过{ctx.subject}检查出来的疾病有{joiner.join(ctx.items)}'

        return ''


if __name__ == '__main__':
    AnswerSearcher()
