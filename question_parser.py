#!/usr/bin/env python3
# coding: utf-8

from graph.models import CypherQuery


class QuestionPaser:

    def build_entitydict(self, args):
        entity_dict = {}
        for arg, types in args.items():
            for type_ in types:
                if type_ not in entity_dict:
                    entity_dict[type_] = [arg]
                else:
                    entity_dict[type_].append(arg)
        return entity_dict

    def parser_main(self, res_classify):
        args = res_classify['args']
        entity_dict = self.build_entitydict(args)
        question_types = res_classify['question_types']
        sqls = []
        for question_type in question_types:
            entity_key = self._entity_key_for_type(question_type)
            queries = self.sql_transfer(question_type, entity_dict.get(entity_key))
            if queries:
                sqls.append({
                    'question_type': question_type,
                    'queries': queries,
                })
        return sqls

    def _entity_key_for_type(self, question_type):
        mapping = {
            'disease_symptom': 'disease',
            'symptom_disease': 'symptom',
            'disease_cause': 'disease',
            'disease_acompany': 'disease',
            'disease_not_food': 'disease',
            'disease_do_food': 'disease',
            'food_not_disease': 'food',
            'food_do_disease': 'food',
            'disease_drug': 'disease',
            'drug_disease': 'drug',
            'disease_check': 'disease',
            'check_disease': 'check',
            'disease_prevent': 'disease',
            'disease_lasttime': 'disease',
            'disease_cureway': 'disease',
            'disease_cureprob': 'disease',
            'disease_easyget': 'disease',
            'disease_desc': 'disease',
        }
        return mapping.get(question_type)

    def sql_transfer(self, question_type, entities):
        if not entities:
            return []

        queries = []
        for name in entities:
            params = {'name': name}
            if question_type == 'disease_cause':
                cypher = 'MATCH (m:Disease) WHERE m.name = $name RETURN m.name, m.cause'
            elif question_type == 'disease_prevent':
                cypher = 'MATCH (m:Disease) WHERE m.name = $name RETURN m.name, m.prevent'
            elif question_type == 'disease_lasttime':
                cypher = 'MATCH (m:Disease) WHERE m.name = $name RETURN m.name, m.cure_lasttime'
            elif question_type == 'disease_cureprob':
                cypher = 'MATCH (m:Disease) WHERE m.name = $name RETURN m.name, m.cured_prob'
            elif question_type == 'disease_cureway':
                cypher = 'MATCH (m:Disease) WHERE m.name = $name RETURN m.name, m.cure_way'
            elif question_type == 'disease_easyget':
                cypher = 'MATCH (m:Disease) WHERE m.name = $name RETURN m.name, m.easy_get'
            elif question_type == 'disease_desc':
                cypher = 'MATCH (m:Disease) WHERE m.name = $name RETURN m.name, m.desc'
            elif question_type == 'disease_symptom':
                cypher = (
                    'MATCH (m:Disease)-[r:has_symptom]->(n:Symptom) '
                    'WHERE m.name = $name RETURN m.name, r.name, n.name'
                )
            elif question_type == 'symptom_disease':
                cypher = (
                    'MATCH (m:Disease)-[r:has_symptom]->(n:Symptom) '
                    'WHERE n.name = $name RETURN m.name, r.name, n.name'
                )
            elif question_type == 'disease_acompany':
                queries.append(CypherQuery(
                    'MATCH (m:Disease)-[r:acompany_with]->(n:Disease) '
                    'WHERE m.name = $name RETURN m.name, r.name, n.name',
                    params,
                ))
                queries.append(CypherQuery(
                    'MATCH (m:Disease)-[r:acompany_with]->(n:Disease) '
                    'WHERE n.name = $name RETURN m.name, r.name, n.name',
                    params,
                ))
                continue
            elif question_type == 'disease_not_food':
                cypher = (
                    'MATCH (m:Disease)-[r:no_eat]->(n:Food) '
                    'WHERE m.name = $name RETURN m.name, r.name, n.name'
                )
            elif question_type == 'disease_do_food':
                queries.append(CypherQuery(
                    'MATCH (m:Disease)-[r:do_eat]->(n:Food) '
                    'WHERE m.name = $name RETURN m.name, r.name, n.name',
                    params,
                ))
                queries.append(CypherQuery(
                    'MATCH (m:Disease)-[r:recommand_eat]->(n:Food) '
                    'WHERE m.name = $name RETURN m.name, r.name, n.name',
                    params,
                ))
                continue
            elif question_type == 'food_not_disease':
                cypher = (
                    'MATCH (m:Disease)-[r:no_eat]->(n:Food) '
                    'WHERE n.name = $name RETURN m.name, r.name, n.name'
                )
            elif question_type == 'food_do_disease':
                queries.append(CypherQuery(
                    'MATCH (m:Disease)-[r:do_eat]->(n:Food) '
                    'WHERE n.name = $name RETURN m.name, r.name, n.name',
                    params,
                ))
                queries.append(CypherQuery(
                    'MATCH (m:Disease)-[r:recommand_eat]->(n:Food) '
                    'WHERE n.name = $name RETURN m.name, r.name, n.name',
                    params,
                ))
                continue
            elif question_type == 'disease_drug':
                queries.append(CypherQuery(
                    'MATCH (m:Disease)-[r:common_drug]->(n:Drug) '
                    'WHERE m.name = $name RETURN m.name, r.name, n.name',
                    params,
                ))
                queries.append(CypherQuery(
                    'MATCH (m:Disease)-[r:recommand_drug]->(n:Drug) '
                    'WHERE m.name = $name RETURN m.name, r.name, n.name',
                    params,
                ))
                continue
            elif question_type == 'drug_disease':
                queries.append(CypherQuery(
                    'MATCH (m:Disease)-[r:common_drug]->(n:Drug) '
                    'WHERE n.name = $name RETURN m.name, r.name, n.name',
                    params,
                ))
                queries.append(CypherQuery(
                    'MATCH (m:Disease)-[r:recommand_drug]->(n:Drug) '
                    'WHERE n.name = $name RETURN m.name, r.name, n.name',
                    params,
                ))
                continue
            elif question_type == 'disease_check':
                cypher = (
                    'MATCH (m:Disease)-[r:need_check]->(n:Check) '
                    'WHERE m.name = $name RETURN m.name, r.name, n.name'
                )
            elif question_type == 'check_disease':
                cypher = (
                    'MATCH (m:Disease)-[r:need_check]->(n:Check) '
                    'WHERE n.name = $name RETURN m.name, r.name, n.name'
                )
            else:
                continue

            queries.append(CypherQuery(cypher, params))

        return queries


if __name__ == '__main__':
    QuestionPaser()
