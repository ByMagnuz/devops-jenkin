"""Repositorio de artefactos en filesystem: simula publish/retrieve e inmutabilidad."""
import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from tools.common import safe_name, sha256, write_json


def publish(repository, artifact, name, version):
    safe_name(name)
    safe_name(version)
    artifact = Path(artifact)
    if not artifact.is_file():
        raise FileNotFoundError(f'No existe el artefacto: {artifact}')
    location = Path(repository) / name / version
    destination = location / 'programas.tar.gz'
    metadata_file = location / 'metadata.json'
    digest = sha256(artifact)
    if metadata_file.exists():
        data = json.loads(metadata_file.read_text(encoding='utf-8'))
        if data.get('sha256') != digest or not destination.is_file() or sha256(destination) != digest:
            raise ValueError('La version ya existe con un contenido distinto: no se permite sobrescribir')
        print(f'[NEXUS SIMULADO] Version ya publicada, checksum valido: {version}')
        return data
    location.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(artifact, destination)
    data = {
        'tool': 'SIMULATED_NEXUS_NOT_REAL',
        'name': name,
        'version': version,
        'sha256': digest,
        'published_at_utc': datetime.now(timezone.utc).isoformat(),
    }
    write_json(metadata_file, data)
    print(f'[NEXUS SIMULADO] Publicado {name}:{version} sha256={digest[:16]}...')
    return data


def resolve(repository, name, version):
    safe_name(name)
    safe_name(version)
    location = Path(repository) / name / version
    path = location / 'programas.tar.gz'
    meta = location / 'metadata.json'
    if not path.is_file() or not meta.is_file():
        raise FileNotFoundError(f'No existe el artefacto {name}:{version} en el repositorio')
    data = json.loads(meta.read_text(encoding='utf-8'))
    if sha256(path) != data['sha256']:
        raise ValueError('SHA-256 no coincide: artefacto corrupto')
    return path, data


def main():
    parser = argparse.ArgumentParser()
    actions = parser.add_subparsers(dest='command', required=True)
    publish_parser = actions.add_parser('publish')
    publish_parser.add_argument('--repository', required=True)
    publish_parser.add_argument('--artifact', required=True)
    publish_parser.add_argument('--name', required=True)
    publish_parser.add_argument('--version', required=True)
    fetch_parser = actions.add_parser('verify')
    fetch_parser.add_argument('--repository', required=True)
    fetch_parser.add_argument('--name', required=True)
    fetch_parser.add_argument('--version', required=True)
    args = parser.parse_args()
    try:
        if args.command == 'publish':
            publish(args.repository, args.artifact, args.name, args.version)
        else:
            path, _ = resolve(args.repository, args.name, args.version)
            print(f'[NEXUS SIMULADO] Checksum correcto: {path}')
    except (ValueError, OSError, KeyError) as error:
        parser.exit(1, f'[NEXUS SIMULADO] ERROR: {error}\n')


if __name__ == '__main__':
    main()
