import tempfile
import unittest
from pathlib import Path

from tools.dbb import inspect_sources
from tools.sonar import scan


class DevopsLabTests(unittest.TestCase):
    def test_program_and_copy_dependencies(self):
        units = inspect_sources('fuentes/cobol', 'fuentes/copybooks')
        self.assertEqual(units[0]['program'], 'SALDOS')
        self.assertIn('CLIENTE', units[0]['copybooks'])

    def test_missing_copybook_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / 'src'
            source.mkdir()
            (source / 'BAD.cbl').write_text('PROGRAM-ID. BAD.\nCOPY NOEXISTE.\n', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'COPY inexistentes'):
                inspect_sources(source, tmp)

    def test_clean_source_passes_quality_gate(self):
        self.assertEqual([], scan('fuentes'))

    def test_quality_gate_catches_todo(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / 'BAD.cbl').write_text('      * TODO: revisar\n', encoding='utf-8')
            problems = scan(tmp)
            self.assertEqual(problems[0]['rule'], 'NO_TODO')


if __name__ == '__main__':
    unittest.main()
