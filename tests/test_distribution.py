import io
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from assemble import safe_name, unpack
from catalog import catalog


class DistributionSafety(unittest.TestCase):
    def test_catalog_never_installs_by_default(self):
        self.assertEqual(len(catalog()['plugins']), 3)
        for entry in catalog()['plugins']:
            self.assertEqual(entry['policy']['installation'], 'AVAILABLE')

    def test_archive_paths_cannot_escape_package(self):
        for name in ('/plug/a', 'plug/../a', 'other/a', 'plug\\a', 'plug/C:/a'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                safe_name(name, 'plug')

    def test_symlink_tar_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            with tarfile.open(path / 'bad.tar.gz', 'w:gz') as archive:
                item = tarfile.TarInfo('plug/escape')
                item.type = tarfile.SYMTYPE
                item.linkname = '/etc/passwd'
                archive.addfile(item)
            with self.assertRaises(ValueError):
                unpack(path / 'bad.tar.gz', path / 'out', 'plug')

    def test_duplicate_zip_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            with zipfile.ZipFile(path / 'bad.zip', 'w') as archive:
                archive.writestr('plug/a', b'1')
                with self.assertWarns(UserWarning):
                    archive.writestr('plug/a', b'2')
            with self.assertRaises(ValueError):
                unpack(path / 'bad.zip', path / 'out', 'plug')

    def test_extraction_preserves_bytes(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            with tarfile.open(path / 'good.tar.gz', 'w:gz') as archive:
                item = tarfile.TarInfo('plug/bin/plug')
                item.size = 4
                item.mode = 0o755
                archive.addfile(item, io.BytesIO(b'test'))
            inventory = unpack(path / 'good.tar.gz', path / 'out', 'plug')
            self.assertEqual((path / 'out/plug/bin/plug').read_bytes(), b'test')
            self.assertEqual(set(inventory), {'bin/plug'})


if __name__ == '__main__':
    unittest.main()
