"""Ejecuta unittest y genera un reporte JUnit XML solo con libreria estandar."""
import sys
import time
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


class Result(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.passed = []

    def addSuccess(self, test):
        self.passed.append(test)
        super().addSuccess(test)


def main():
    suite = unittest.defaultTestLoader.discover('tests', pattern='test_*.py')
    total = suite.countTestCases()
    start = time.monotonic()
    runner = unittest.TextTestRunner(verbosity=2, resultclass=Result)
    result = runner.run(suite)
    elapsed = time.monotonic() - start
    root = ET.Element('testsuite', tests=str(total), failures=str(len(result.failures)),
                      errors=str(len(result.errors)), time=f'{elapsed:.3f}')
    for test in result.passed:
        ET.SubElement(root, 'testcase', classname=test.__class__.__name__, name=test._testMethodName)
    for test, trace in result.failures:
        case = ET.SubElement(root, 'testcase', classname=test.__class__.__name__, name=test._testMethodName)
        ET.SubElement(case, 'failure', message='assertion failed').text = trace
    for test, trace in result.errors:
        case = ET.SubElement(root, 'testcase', classname=test.__class__.__name__, name=test._testMethodName)
        ET.SubElement(case, 'error', message='test error').text = trace
    Path('reports').mkdir(exist_ok=True)
    ET.ElementTree(root).write('reports/tests.xml', encoding='utf-8', xml_declaration=True)
    if not result.wasSuccessful() or not total:
        sys.exit(1)


if __name__ == '__main__':
    main()
