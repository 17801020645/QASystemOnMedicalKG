#!/usr/bin/env python3
# coding: utf-8

import json
import logging
from typing import Any

from config import BATCH_SIZE, DATA_PATH
from graph.client import neo4j_session

logger = logging.getLogger(__name__)


class MedicalGraphImporter:
    def __init__(self, data_path=None):
        self.data_path = data_path or DATA_PATH

    def read_nodes(self):
        drugs = []
        foods = []
        checks = []
        departments = []
        producers = []
        diseases = []
        symptoms = []
        disease_infos = []

        rels_department = []
        rels_noteat = []
        rels_doeat = []
        rels_recommandeat = []
        rels_commonddrug = []
        rels_recommanddrug = []
        rels_check = []
        rels_drug_producer = []
        rels_symptom = []
        rels_acompany = []
        rels_category = []

        with open(self.data_path, encoding='utf-8') as f:
            for count, line in enumerate(f, 1):
                if count % 1000 == 0:
                    logger.info('已解析 %d 条记录', count)
                data_json = json.loads(line)
                disease = data_json['name']
                disease_dict = {
                    'name': disease,
                    'desc': '',
                    'prevent': '',
                    'cause': '',
                    'easy_get': '',
                    'cure_department': '',
                    'cure_way': '',
                    'cure_lasttime': '',
                    'symptom': '',
                    'cured_prob': '',
                }
                diseases.append(disease)

                if 'symptom' in data_json:
                    symptoms += data_json['symptom']
                    for symptom in data_json['symptom']:
                        rels_symptom.append([disease, symptom])

                if 'acompany' in data_json:
                    for acompany in data_json['acompany']:
                        rels_acompany.append([disease, acompany])

                if 'desc' in data_json:
                    disease_dict['desc'] = data_json['desc']
                if 'prevent' in data_json:
                    disease_dict['prevent'] = data_json['prevent']
                if 'cause' in data_json:
                    disease_dict['cause'] = data_json['cause']
                if 'easy_get' in data_json:
                    disease_dict['easy_get'] = data_json['easy_get']

                if 'cure_department' in data_json:
                    cure_department = data_json['cure_department']
                    if len(cure_department) == 1:
                        rels_category.append([disease, cure_department[0]])
                    if len(cure_department) == 2:
                        big = cure_department[0]
                        small = cure_department[1]
                        rels_department.append([small, big])
                        rels_category.append([disease, small])
                    disease_dict['cure_department'] = cure_department
                    departments += cure_department

                if 'cure_way' in data_json:
                    disease_dict['cure_way'] = data_json['cure_way']
                if 'cure_lasttime' in data_json:
                    disease_dict['cure_lasttime'] = data_json['cure_lasttime']
                if 'cured_prob' in data_json:
                    disease_dict['cured_prob'] = data_json['cured_prob']

                if 'common_drug' in data_json:
                    for drug in data_json['common_drug']:
                        rels_commonddrug.append([disease, drug])
                    drugs += data_json['common_drug']

                if 'recommand_drug' in data_json:
                    for drug in data_json['recommand_drug']:
                        rels_recommanddrug.append([disease, drug])
                    drugs += data_json['recommand_drug']

                if 'not_eat' in data_json:
                    for item in data_json['not_eat']:
                        rels_noteat.append([disease, item])
                    foods += data_json['not_eat']
                    for item in data_json.get('do_eat', []):
                        rels_doeat.append([disease, item])
                    foods += data_json.get('do_eat', [])
                    for item in data_json.get('recommand_eat', []):
                        rels_recommandeat.append([disease, item])
                    foods += data_json.get('recommand_eat', [])

                if 'check' in data_json:
                    for item in data_json['check']:
                        rels_check.append([disease, item])
                    checks += data_json['check']

                if 'drug_detail' in data_json:
                    for detail in data_json['drug_detail']:
                        producer = detail.split('(')[0]
                        drug_name = detail.split('(')[-1].replace(')', '')
                        rels_drug_producer.append([producer, drug_name])
                        producers.append(producer)

                disease_infos.append(disease_dict)

        return (
            set(drugs), set(foods), set(checks), set(departments), set(producers),
            set(symptoms), set(diseases), disease_infos,
            rels_check, rels_recommandeat, rels_noteat, rels_doeat, rels_department,
            rels_commonddrug, rels_drug_producer, rels_recommanddrug,
            rels_symptom, rels_acompany, rels_category,
        )

    def _run_batches(self, cypher: str, rows: list[dict[str, Any]], label: str) -> None:
        total = len(rows)
        for i in range(0, total, BATCH_SIZE):
            batch = rows[i:i + BATCH_SIZE]
            with neo4j_session() as session:
                session.run(cypher, {'rows': batch})
            done = min(i + BATCH_SIZE, total)
            logger.info('%s: %d / %d', label, done, total)

    def _merge_name_nodes(self, label: str, names: set) -> None:
        rows = [{'name': n} for n in names]
        cypher = f"""
        UNWIND $rows AS row
        MERGE (n:{label} {{name: row.name}})
        """
        self._run_batches(cypher, rows, label)

    def create_disease_nodes(self, disease_infos: list) -> None:
        rows = [
            {
                'name': d['name'],
                'desc': d.get('desc') or '',
                'prevent': d.get('prevent') or '',
                'cause': d.get('cause') or '',
                'easy_get': d.get('easy_get') or '',
                'cure_lasttime': d.get('cure_lasttime') or '',
                'cure_department': d.get('cure_department') or [],
                'cure_way': d.get('cure_way') or [],
                'cured_prob': d.get('cured_prob') or '',
            }
            for d in disease_infos
        ]
        cypher = """
        UNWIND $rows AS row
        MERGE (d:Disease {name: row.name})
        SET d.desc = row.desc,
            d.prevent = row.prevent,
            d.cause = row.cause,
            d.easy_get = row.easy_get,
            d.cure_lasttime = row.cure_lasttime,
            d.cure_department = row.cure_department,
            d.cure_way = row.cure_way,
            d.cured_prob = row.cured_prob
        """
        self._run_batches(cypher, rows, 'Disease')

    def create_graphnodes(self) -> None:
        parsed = self.read_nodes()
        disease_infos = parsed[7]
        self.create_disease_nodes(disease_infos)
        self._merge_name_nodes('Drug', parsed[0])
        self._merge_name_nodes('Food', parsed[1])
        self._merge_name_nodes('Check', parsed[2])
        self._merge_name_nodes('Department', parsed[3])
        self._merge_name_nodes('Producer', parsed[4])
        self._merge_name_nodes('Symptom', parsed[5])

    def _merge_relationships(
        self,
        start_label: str,
        end_label: str,
        edges: list,
        rel_type: str,
        rel_name: str,
    ) -> None:
        unique = {tuple(edge) for edge in edges}
        rows = [
            {'start_name': s, 'end_name': e, 'rel_name': rel_name}
            for s, e in unique
        ]
        cypher = f"""
        UNWIND $rows AS row
        MATCH (p:{start_label} {{name: row.start_name}})
        MATCH (q:{end_label} {{name: row.end_name}})
        MERGE (p)-[r:{rel_type}]->(q)
        SET r.name = row.rel_name
        """
        self._run_batches(cypher, rows, rel_type)

    def create_graphrels(self) -> None:
        parsed = self.read_nodes()
        (
            _, _, _, _, _, _, _, _,
            rels_check, rels_recommandeat, rels_noteat, rels_doeat, rels_department,
            rels_commonddrug, rels_drug_producer, rels_recommanddrug,
            rels_symptom, rels_acompany, rels_category,
        ) = parsed

        self._merge_relationships('Disease', 'Food', rels_recommandeat, 'recommand_eat', '推荐食谱')
        self._merge_relationships('Disease', 'Food', rels_noteat, 'no_eat', '忌吃')
        self._merge_relationships('Disease', 'Food', rels_doeat, 'do_eat', '宜吃')
        self._merge_relationships('Department', 'Department', rels_department, 'belongs_to', '属于')
        self._merge_relationships('Disease', 'Drug', rels_commonddrug, 'common_drug', '常用药品')
        self._merge_relationships('Producer', 'Drug', rels_drug_producer, 'drugs_of', '生产药品')
        self._merge_relationships('Disease', 'Drug', rels_recommanddrug, 'recommand_drug', '好评药品')
        self._merge_relationships('Disease', 'Check', rels_check, 'need_check', '诊断检查')
        self._merge_relationships('Disease', 'Symptom', rels_symptom, 'has_symptom', '症状')
        self._merge_relationships('Disease', 'Disease', rels_acompany, 'acompany_with', '并发症')
        self._merge_relationships('Disease', 'Department', rels_category, 'belongs_to', '所属科室')

    def export_data(self, output_dir=None) -> None:
        from pathlib import Path
        output_dir = Path(output_dir or DATA_PATH.parent.parent)
        parsed = self.read_nodes()
        names_map = {
            'drug.txt': parsed[0],
            'food.txt': parsed[1],
            'check.txt': parsed[2],
            'department.txt': parsed[3],
            'producer.txt': parsed[4],
            'symptoms.txt': parsed[5],
            'disease.txt': parsed[6],
        }
        for filename, names in names_map.items():
            path = output_dir / filename
            path.write_text('\n'.join(sorted(names)), encoding='utf-8')
            logger.info('已导出 %s (%d 条)', path, len(names))
