"""Construye un .tar.gz DIDACTICO a partir de fuentes COBOL; NO compila COBOL."""
import argparse
import io
import json
import re
import tarfile
from datetime import datetime, timezone
from pathlib import Path

from tools.common import sha256

PROGRAM_RE = re.compile(r'\bPROGRAM-ID\s*\.\s*([\w-]+)\s*\.', re.IGNORECASE)
COPY_RE = re.compile(r'\bCOPY\s+([\w-]+)\s*\.', re.IGNORECASE)


def inspect_sources(source_dir, copy_dir):
    source_dir, copy_dir = Path(source_dir), Path(copy_dir)
    items = []
    all_files = sorted(source_dir.glob('*.cbl'))
    if not all_files:
        raise ValueError('No se encontraron fuentes .cbl')
    copybooks = {p.stem.upper(): p for p in copy_dir.glob('*.cpy')}
    for path in all_files:
        text = path.read_text(encoding='utf-8')
        match = PROGRAM_RE.search(text)
        if not match:
            raise ValueError(f'{path}: falta PROGRAM-ID')
        program = match.group(1).upper()
        names = sorted(set(x.upper() for x in COPY_RE.findall(text)))
        missing = [n for n in names if n not in copybooks]
        if missing:
            raise ValueError(f'{path}: COPY inexistentes: {", ".join(missing)}')
        items.append({
            'program': program,
            'source': str(path),
            'source_sha256': sha256(path),
            'copybooks': {n: sha256(copybooks[n]) for n in names},
        })
    if len({x['program'] for x in items}) != len(items):
        raise ValueError('PROGRAM-ID duplicado')
    return items


def build(source_dir, copy_dir, output, commit):
    units = inspect_sources(source_dir, copy_dir)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        'type': 'SIMULATED_COBOL_BUILD_NOT_EXECUTABLE',
        'commit': commit,
        'built_at_utc': datetime.now(timezone.utc).isoformat(),
        'programs': units,
    }
    with tarfile.open(output, 'w:gz') as tar:
        data = json.dumps(manifest, indent=2, ensure_ascii=False).encode('utf-8')
        info = tarfile.TarInfo('manifest.json')
        info.size = len(data)
        tar.addfile(info, io.BytesIO(data))
        for unit in units:
            content = json.dumps({
                'artifact_type': 'SIMULATED_LOAD_MODULE_NOT_EXECUTABLE',
                **unit
            }, indent=2, ensure_ascii=False).encode('utf-8')
            info = tarfile.TarInfo(f"LOADLIB/{unit['program']}.load")
            info.size = len(content)
            tar.addfile(info, io.BytesIO(content))
    print(f'[DBB SIMULADO] {len(units)} programa(s) -> {output}')
    for unit in units:
        print(f"  - {unit['program']} dependencias: {list(unit['copybooks'])}")
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', required=True)
    parser.add_argument('--copybooks', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--commit', required=True)
    args = parser.parse_args()
    try:
        build(args.source, args.copybooks, args.output, args.commit)
    except (ValueError, OSError) as error:
        parser.exit(1, f'[DBB SIMULADO] ERROR: {error}\n')


if __name__ == '__main__':
    main()
