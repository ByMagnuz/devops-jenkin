"""Promoción de un artefacto versionado a directorios que representan ambientes z/OS."""
import argparse
import io
import json
import tarfile
from datetime import datetime, timezone
from pathlib import Path

from tools.common import write_json
from tools.nexus import resolve

TARGETS = ('TEST', 'QA', 'PREPROD', 'PROD')


def deploy(repository, environments, name, version, target):
    if target not in TARGETS:
        raise ValueError('Ambiente no permitido')
    archive, source_meta = resolve(repository, name, version)
    target_dir = Path(environments) / target
    version_dir = target_dir / 'versions' / version / 'LOADLIB'
    version_dir.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive, 'r:gz') as tar:
        members = tar.getmembers()
        manifest_member = next((m for m in members if m.name == 'manifest.json' and m.isfile()), None)
        if manifest_member is None:
            raise ValueError('Artefacto sin manifiesto')
        manifest = json.loads(tar.extractfile(manifest_member).read().decode('utf-8'))
        programs = {p['program'] for p in manifest['programs']}
        extracted = set()
        for member in members:
            if member.name.startswith('LOADLIB/'):
                if not member.isfile():
                    raise ValueError('Entrada de artefacto invalida')
                filename = member.name.split('/', 1)[1]
                if filename not in {f'{p}.load' for p in programs}:
                    raise ValueError('Archivo inesperado en LOADLIB')
                path = version_dir / filename
                content = tar.extractfile(member).read()
                if path.exists() and path.read_bytes() != content:
                    raise ValueError('El archivo desplegado para esta version difiere')
                path.write_bytes(content)
                extracted.add(filename)
        if extracted != {f'{p}.load' for p in programs}:
            raise ValueError('Faltan modulos LOADLIB en el artefacto')
    record = {
        'tool': 'SIMULATED_WAZI_DEPLOY_NOT_REAL',
        'environment': target,
        'artifact': name,
        'version': version,
        'sha256': source_meta['sha256'],
        'programs': sorted(programs),
        'deployed_at_utc': datetime.now(timezone.utc).isoformat(),
    }
    write_json(target_dir / 'versions' / version / 'deployment.json', record)
    write_json(target_dir / 'current.json', record)
    print(f'[WAZI SIMULADO] {name}:{version} -> {target}/LOADLIB ({len(programs)} modulo(s))')
    return record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['deploy'])
    parser.add_argument('--repository', required=True)
    parser.add_argument('--environments', required=True)
    parser.add_argument('--name', required=True)
    parser.add_argument('--version', required=True)
    parser.add_argument('--target', choices=TARGETS, required=True)
    args = parser.parse_args()
    try:
        deploy(args.repository, args.environments, args.name, args.version, args.target)
    except (ValueError, OSError, KeyError, tarfile.TarError, json.JSONDecodeError) as error:
        parser.exit(1, f'[WAZI SIMULADO] ERROR: {error}\n')


if __name__ == '__main__':
    main()
