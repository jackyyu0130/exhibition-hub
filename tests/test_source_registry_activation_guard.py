import importlib.util
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('guard',ROOT/'scripts/check_source_registry_activation.py')
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

class SourceRegistryActivationGuardTests(unittest.TestCase):
    def test_planned_addition_does_not_change_active_fingerprint(self):
        before={'sources':[{'id':'active','status':'active','enabled':True,'parser':'a'}]}
        after={'sources':[{'id':'active','status':'active','enabled':True,'parser':'a'},{'id':'planned','status':'planned','enabled':False,'parser':'x'}]}
        self.assertEqual(mod.active_fingerprint(before),mod.active_fingerprint(after))

    def test_active_parser_change_is_detected(self):
        before={'sources':[{'id':'active','status':'active','enabled':True,'parser':'a'}]}
        after={'sources':[{'id':'active','status':'active','enabled':True,'parser':'b'}]}
        self.assertNotEqual(mod.active_fingerprint(before),mod.active_fingerprint(after))

if __name__=='__main__': unittest.main()
