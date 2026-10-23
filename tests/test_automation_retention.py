import json
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import automation_retention as m
class RetentionTests(unittest.TestCase):
    def test_protects_three_good_latest_failure_and_unowned(self):
        with tempfile.TemporaryDirectory() as tmp:
            state=Path(tmp)/'state'
            builds=state/'builds'
            builds.mkdir(parents=True)
            (builds/'.chromium-stealthcdp-automation-owned').write_text('chromium-stealthcdp automation v1\n')
            installed=Path(tmp)/'installed'
            installed.mkdir()
            for i in range(7):
                identity=str(i)
                run=state/'runs'/identity
                run.mkdir(parents=True)
                (run/'run.json').write_text(json.dumps({'id':identity,'created_at':i,'state':'failed' if i==6 else 'complete'}))
                candidate=builds/'runs'/identity/'artifacts'
                candidate.mkdir(parents=True)
            unowned=Path(tmp)/'operator'
            unowned.mkdir()
            with patch.object(m,'inspect_live_versions',return_value={'processes':[],'unknownPids':[]}):
                result=m.maintain(state,installed)
            self.assertEqual(len(result['removed']),3)
            self.assertTrue((builds/'runs/6/artifacts').exists())
            self.assertTrue((builds/'runs/3/artifacts').exists())
            self.assertTrue(unowned.exists())

if __name__=='__main__': unittest.main()
