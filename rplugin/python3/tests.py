import unittest

from unittest.mock import Mock, MagicMock
from ansible_vault_nvim import AnsibleVaultNvim

class TestAnsibleVaultNvim(unittest.TestCase):
    lines = [
            "variable: !vault |",
            "    $ANSIBLE_VAULT;1.1;AES256",
            "    39353562313636366166643533373536386531303135626438666335396664626161316161666132",
            "    6161343431636430383666333735636136643634643665310a376139346463633531623136643263",
            "    63643837356436353630363239663263346230636336356364383133636230316233303836623938",
            "    3034303735396430360a633964393738666561623839343530643538393039306133346239386637",
            "    3065",
            "",
            "lvl1:",
            "  var1: !vault |",
            "    $ANSIBLE_VAULT;1.1;AES256",
            "    39353562313636366166643533373536386531303135626438666335396664626161316161666132",
            "    6161343431636430383666333735636136643634643665310a376139346463633531623136643263",
            "    63643837356436353630363239663263346230636336356364383133636230316233303836623938",
            "    3034303735396430360a633964393738666561623839343530643538393039306133346239386637",
            "    3065",
            "  var2: something",
            "non_vault_variable: something",
            "another_variable: !vault |",
            "    $ANSIBLE_VAULT;1.1;AES256",
            "    39353562313636366166643533373536386531303135626438666335396664626161316161666132",
            "    6161343431636430383666333735636136643634643665310a376139346463633531623136643263",
            "    63643837356436353630363239663263346230636336356364383133636230316233303836623938",
            "    3034303735396430360a633964393738666561623839343530643538393039306133346239386637",
            "    3065",
            "",
            "yet_another: !vault |",
            "    $ANSIBLE_VAULT;1.1;AES256",
            "    39353562313636366166643533373536386531303135626438666335396664626161316161666132",
            "    6161343431636430383666333735636136643634643665310a376139346463633531623136643263",
            "    63643837356436353630363239663263346230636336356364383133636230316233303836623938",
            "    3034303735396430360a633964393738666561623839343530643538393039306133346239386637",
            "    3065" ]

    def test_get_vault_variables(self):
        nvim = Mock()
        av = AnsibleVaultNvim(nvim)

        assert av.get_vault_variables(self.lines) == ["variable",
                                                      "var1",
                                                      "another_variable",
                                                      "yet_another" ]

    def test_format_entry(self):
        entry = "some\ncontent\nlonger\nthan\nwidth"
        nvim = Mock()
        nvim.current.window.width = 15
        av = AnsibleVaultNvim(nvim)

        assert av.format_entry(entry) == "someconte..."
        assert len(av.format_entry(entry)) + 3 <= 15

        entry = "some"
        assert av.format_entry(entry) == "some"

    def test_generate_error_list(self):
        nvim = Mock()
        vs = {"ansible_vault_path": "secrets/vault"}
        nvim.vars = MagicMock()
        nvim.vars.__getitem__.side_effect = vs.__getitem__
        nvim.vars.get.side_effect = vs.get
        nvim.current.window.width = 40

        av = AnsibleVaultNvim(nvim)
        error_list = av.generate_error_list(self.lines)

        assert error_list == [ "1 variable: a", "10 lvl1 - var1: a", "19 another_variable: a", "27 yet_another: a"]

    def test_is_var(self):
        nvim = Mock()
        decrypted_vars = {"lvl1": {"inner": "value"}, "lvl2": {"inner": {"deep": "value"}}}

        av = AnsibleVaultNvim(nvim)

        assert av.is_var("inner", decrypted_vars)
        assert av.is_var("lvl1", decrypted_vars) == False

    def test_find_end_or_other_var(self):
        nvim = Mock()
        decrypted_vars = {
            "variable": "a",
            "lvl1": {
                "var1": "a",
                "var2": "something",
            },
            "non_vault_variable": "something",
            "another_variable": "a",
            "yet_another": "a"
        }

        av = AnsibleVaultNvim(nvim)

        assert av.find_end_or_other_var("variable", decrypted_vars, self.lines, 0) == 7
        assert av.find_end_or_other_var("var1", decrypted_vars, self.lines, 9) == 16

    def test_get_variable_paths(self):
        nvim = Mock()
        av = AnsibleVaultNvim(nvim)
        graph = {"group1": {
            "sub1": {
                "var1": {
                    "leaf1" :"v4"
                },
                "var2": "v2",
                "var3": "v3"
            },
            "sub2": {"var1": "v4", "var2": "v2", "leaf1": "v4"}
            }
        }
        paths = av.get_variable_paths("var2", graph)

        assert paths == [['group1', 'sub1', 'var2'], ['group1', 'sub2', 'var2']]

    def test_get_var_siblings(self):
        nvim = Mock()
        av = AnsibleVaultNvim(nvim)

        graph = {
            "lvl1": {
                "var1": "yep",
                "var2": "nope"
            },
            "lvl2": {
                "lonely": "boy"
            },
            "top-mate": "yep too"
        }

        assert av.get_var_siblings("var1", graph) == ["var2"]
        assert len(av.get_var_siblings("loneley", graph)) == 0

    def test_get_value_in_path(self):
        nvim = Mock()
        av = AnsibleVaultNvim(nvim)

        graph = {"lvl1" : {"lvl2": "value"}, "some_other": "var"}
        path = ["lvl2", "lvl1"]

        assert av.get_value_in_path(graph, path) == "value"

    def test_generate_entry(self):
        nvim = Mock()
        av = AnsibleVaultNvim(nvim)
        decrypted_vars = {
            "variable": "a",
            "lvl1": {
                "var1": "a",
                "var2": "something",
            },
            "non_vault_variable": "something",
            "another_variable": "a",
            "yet_another": "a"
        }

        assert av.generate_entry("var1", decrypted_vars, self.lines) == ["10 lvl1 - var1: a"]


    if __name__ == '__main__':
        unittest.main()