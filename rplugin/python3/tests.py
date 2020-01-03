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
            "    3065"
            "",
            "non_vault_variable: something",
            "another_variable: !vault |",
            "    $ANSIBLE_VAULT;1.1;AES256",
            "    39353562313636366166643533373536386531303135626438666335396664626161316161666132",
            "    6161343431636430383666333735636136643634643665310a376139346463633531623136643263",
            "    63643837356436353630363239663263346230636336356364383133636230316233303836623938",
            "    3034303735396430360a633964393738666561623839343530643538393039306133346239386637",
            "    3065"
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

        assert av.get_vault_variables(self.lines) == ["variable: !vault |",
                                                      "another_variable: !vault |",
                                                      "yet_another: !vault |" ]
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

        assert error_list == [ "1 variable: a", "9 another_variable: a", "16 yet_another: a"]

    def test_find_end_or_other_var(self):
        nvim = Mock()
        decrypted_vars = {"variable": "a", "another_variable": "a", "yet_another": "a"}
        av = AnsibleVaultNvim(nvim)
        assert av.find_end_or_other_var(decrypted_vars, self.lines, 1) == 8

        assert av.find_end_or_other_var(decrypted_vars, self.lines, 17) == len(self.lines)-1

    if __name__ == '__main__':
        unittest.main()