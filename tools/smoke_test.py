"""Verificación posterior a un despliegue simulado."""
import argparse
import json
from pathlib import Path


def check(environments, target, version):
    root = Path(environments) / target
    info = json.loads((root / 'current.json').read_text(encoding='utf-8'))
    if info['version'] != version:
        raise ValueError('El ambiente apunta a una version distinta')
    loadlib = root / 'versions' / version / 'LOADLIB'
    missing = [p for p in info['programs'] if not (loadlib / (p + '.load')).is_file()]
    if missing:
        raise ValueError('Modulos no presentes: ' + ', '.join(missing))
    print(f'[SMOKE TEST] {target}: OK, version={version}, programas={info["programs"]}')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--environments', required=True)
    parser.add_argument('--target', required=True)
    parser.add_argument('--version', required=True)
    args = parser.parse_args()
    try:
        check(args.environments, args.target, args.version)
    except (ValueError, OSError, KeyError, json.JSONDecodeError) as error:
        parser.exit(1, f'[SMOKE TEST] ERROR: {error}\n')


if __name__ == '__main__':
    main()
