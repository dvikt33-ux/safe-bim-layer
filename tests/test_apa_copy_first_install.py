"""Install native copy features into existing APA class WITHOUT replacing local code."""
import ast
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import apa_install_native_copy_features as I

SOURCE=(ROOT/"scripts"/"archicad_dynamic_commands.py").read_text(encoding="utf-8")

def old_apa_fixture():
    tree=ast.parse(SOURCE)
    cls=next(x for x in tree.body if isinstance(x,ast.ClassDef)
             and x.name=="DynamicCommands")
    lines=SOURCE.splitlines(keepends=True)
    methods=[x for x in cls.body if isinstance(x,ast.FunctionDef)
             and x.name in I.METHODS]
    for fn in sorted(methods,key=lambda x:x.lineno,reverse=True):
        start=min([fn.lineno]+[dec.lineno for dec in fn.decorator_list])
        del lines[start-1:fn.end_lineno]
    return "".join(lines)

class CopyDeployment(unittest.TestCase):
    def test_append_methods_to_existing_apa_without_replacing_existing(self):
        original=old_apa_fixture()
        self.assertTrue("def execute_batch(" in original)
        output,added,identical=I.inject(SOURCE,original)
        self.assertEqual(set(added),set(I.METHODS))
        self.assertFalse(identical)
        original_cls,original_funcs=I.class_methods(original,expect_existing=True)
        modified_cls,modified_funcs=I.class_methods(output,expect_existing=True)
        for name in set(original_funcs):
            self.assertEqual(ast.dump(original_funcs[name],include_attributes=False),
                             ast.dump(modified_funcs[name],include_attributes=False))
        self.assertEqual(set(I.METHODS)&set(modified_funcs),set(I.METHODS))
        self.assertEqual([ast.unparse(d) for d in modified_funcs["plan_reuse_existing"].decorator_list],["staticmethod"])
        repeat,new_methods,existing=I.inject(SOURCE,output)
        self.assertEqual(repeat,output)
        self.assertFalse(new_methods)
        self.assertEqual(set(existing),set(I.METHODS))

    def test_upgrades_old_local_prepare_without_replacing_existing_apa(self):
        original=old_apa_fixture()
        marker="        CONTRACTS._validator(self.catalog,command).validate(parameters)\n"
        next_stmt="        if command in self.constructors and"
        start=SOURCE.index(marker)+len(marker)
        stop=SOURCE.index(next_stmt,start)
        guard=SOURCE[start:stop]
        self.assertIn("NATIVE_MOVE_MIXED_COPY_AND_MUTATE_DENIED",guard)
        old_apa=original.replace(guard,"")
        self.assertNotIn("NATIVE_MOVE_MIXED_COPY_AND_MUTATE_DENIED",old_apa)
        new, added, already=I.inject(SOURCE,old_apa)
        self.assertIn("NATIVE_MOVE_MIXED_COPY_AND_MUTATE_DENIED",new)
        self.assertEqual(set(added),set(I.METHODS))
        self.assertEqual(new,original)
        repeated,new_methods,matching=I.inject(SOURCE,new)
        self.assertEqual(repeated,new)
        self.assertFalse(new_methods)
        self.assertEqual(set(matching),set(I.METHODS))

    def test_policy_patch_rejects_unknown_prepare_customizations(self):
        original=old_apa_fixture()
        marker="        CONTRACTS._validator(self.catalog,command).validate(parameters)\n"
        next_stmt="        if command in self.constructors and"
        start=SOURCE.index(marker)+len(marker)
        stop=SOURCE.index(next_stmt,start)
        guard=SOURCE[start:stop]
        old_apa=original.replace(guard,"        # user customized prepare in local checkout\n")
        with self.assertRaisesRegex(ValueError,"LOCAL_PREPARE_CUSTOMIZED"):
            I.inject(SOURCE,old_apa)

    def test_refuses_clobbering_a_locally_customized_method(self):
        altered=SOURCE.replace("Duplicate ONE existing native element",
                               "Local patched existing method",1)
        with self.assertRaisesRegex(ValueError,"EXISTING_LOCAL_METHOD_DIFFERS"):
            I.inject(SOURCE,altered)

    def test_prevents_nonapa_injection(self):
        with self.assertRaisesRegex(ValueError,"EXISTING_APA_DYNAMIC_COMMANDS_CLASS_MISSING"):
            I.inject(SOURCE,"print('not APA')\n")

if __name__=="__main__":
    unittest.main()
