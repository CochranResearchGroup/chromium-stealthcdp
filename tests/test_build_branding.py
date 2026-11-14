"""Build entry point must reject resolved Chrome for Testing before compilation."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/build.sh'


class BuildBrandingTests(unittest.TestCase):
    def run_build(self, flag, existing):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / '.git').mkdir()
            bindir = root / 'bin'
            bindir.mkdir()
            (bindir / 'gn').write_text('''#!/bin/sh
if [ "$1" = gen ]; then
 mkdir -p "$2"
 printf '%s' "$3" > "$2/args.gn"
 exit 0
fi
case "$3" in
 --list=is_chrome_for_testing) echo "is_chrome_for_testing = ${TEST_CFT:-false}";;
 *) echo 'is_chrome_for_testing_branded = false';;
esac
''')
            (bindir / 'autoninja').write_text('#!/bin/sh\ntouch compiled\n')
            for tool in bindir.iterdir():
                tool.chmod(0o755)
            if existing:
                (root / 'out/Default').mkdir(parents=True)
                (root / 'out/Default/args.gn').write_text('# existing output\n')
            result = subprocess.run(['bash', str(SCRIPT), '--src', str(root), '--depot-tools', str(bindir)],
                                    env={**os.environ, 'PATH': f'{bindir}:' + os.environ['PATH'],
                                         'TEST_CFT': flag}, capture_output=True, text=True)
            compiled = (root / 'compiled').exists()
            args = (root / 'out/Default/args.gn').read_text()
            return result, compiled, args

    def test_new_output_explicitly_disables_testing(self):
        result, compiled, args = self.run_build('false', False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(compiled)
        self.assertIn('is_chrome_for_testing=false', args)
        self.assertIn('is_chrome_for_testing_branded=false', args)

    def test_existing_testing_output_cannot_compile(self):
        result, compiled, args = self.run_build('true', True)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(compiled)
        self.assertIn('prohibited', result.stderr)
        self.assertEqual(args, '# existing output\n')

    def test_unknown_resolved_value_cannot_compile(self):
        result, compiled, _ = self.run_build('unknown', True)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(compiled)
