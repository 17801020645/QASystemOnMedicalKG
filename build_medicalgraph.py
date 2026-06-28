#!/usr/bin/env python3
# coding: utf-8

import logging

from graph.importer import MedicalGraphImporter

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')


if __name__ == '__main__':
    handler = MedicalGraphImporter()
    print('step1: 导入图谱节点中')
    handler.create_graphnodes()
    print('step2: 导入图谱边中')
    handler.create_graphrels()
    print('导入完成')
