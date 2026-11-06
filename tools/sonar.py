"""Reglas pedagógicas; NO es SonarQube ni un scanner real de COBOL."""
import argparse
from pathlib import Path

from tools.common import write_json


def scan(source_dir):
    violations = []
    files = list(Path(source_dir).rglob('*.cbl')) + list(Path(source_dir).rglob('*.cpy'))
    for path in sorted(files):
        for index, line in enumerate(path.read_text(encoding='utf-8').splitlines(), start=1):
            upper = line.upper()
            # Reglas inventadas para enseñar cómo un gate corta el pipeline.
            if 'TODO' in upper or 'FIXME' in upper:
                violations.append({'file': str(path), 'line': index, 'rule': 'NO_TODO', 'message': 'Hay deuda pendiente (TODO/FIXME)'})
            if 'DISPLAY' in upper and ('PASSWORD' in upper or 'SECRET' in upper):
                violations.append({'file': str(path), 'line': index, 'rule': 'NO_SECRET_DISPLAY', 'message': 'Posible exposición de secretos'})
        if len(path.read_text(encoding='utf-8').splitlines()) > 100:
            violations.append({'file': str(path), 'line': 1, 'rule': 'MAX_LINES', 'message': 'Archivo mayor a 100 líneas'})
    if not files:
        violations.append({'file': str(source_dir), 'line': 0, 'rule': 'NO_SOURCES', 'message': 'No hay fuentes para analizar'})
    return violations


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', required=True)
    parser.add_argument('--report', required=True)
    args = parser.parse_args()
    issues = scan(args.source)
    passed = not issues
    write_json(args.report, {
        'tool': 'SIMULATED_SONARQUBE_NOT_REAL',
        'quality_gate': 'PASSED' if passed else 'FAILED',
        'issues': issues,
    })
    print(f'[SONAR SIMULADO] Quality Gate: {"PASSED" if passed else "FAILED"}; hallazgos: {len(issues)}')
    for issue in issues:
        print(f"  {issue['file']}:{issue['line']} [{issue['rule']}] {issue['message']}")
    if not passed:
        parser.exit(1, 'Se bloquea la publicación y el despliegue por calidad.\n')


if __name__ == '__main__':
    main()
