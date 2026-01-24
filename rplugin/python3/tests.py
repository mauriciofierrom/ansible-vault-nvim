import pytest

from unittest.mock import Mock, MagicMock
from ansible_vault_nvim import AnsibleVaultNvim
from ansible.module_utils._text import to_text

@pytest.fixture
def lines():
    return [
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
        "    3065"
    ]

@pytest.fixture
def mock_nvim():
    nvim = Mock()
    vs = {"ansible_vault_path": "secrets/vault"}
    nvim.vars = MagicMock()
    nvim.vars.__getitem__.side_effect = vs.__getitem__
    nvim.vars.get.side_effect = vs.get
    return nvim


def test_format_entry():
    entry = "some\ncontent\nlonger\nthan\nwidth"
    nvim = Mock()
    nvim.current.window.width = 15
    av = AnsibleVaultNvim(nvim)

    assert av.format_entry(entry) == "someconte..."
    assert len(av.format_entry(entry)) + 3 <= 15

    entry = "some"
    assert av.format_entry(entry) == "some"


def test_get_scalars(mock_nvim, lines):
    av = AnsibleVaultNvim(mock_nvim)
    l = list(filter(lambda x: x["var"] == "var2", av.get_scalars(lines,
        lambda x: x.tag != "!vault")))

    assert len(l)


def test_generate_error_list(mock_nvim, lines):
    mock_nvim.current.window.width = 40

    av = AnsibleVaultNvim(mock_nvim)
    error_list = av.generate_error_list(lines)

    assert error_list == [
        "1 variable: a", "10 var1: a",
        "19 another_variable: a", "27 yet_another: a"
    ]


def test_generate_entry(mock_nvim):
    av = AnsibleVaultNvim(mock_nvim)
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

    assert av.generate_entry({"var": "var1", "val": "a", "line": 10}) == "10 var1: a"


def test_encrypt(mock_nvim, lines):
    mock_nvim.current.buffer = [x for x in lines]
    mock_nvim.current.line = "  var2: something"
    current_line_number = mock_nvim.current.buffer[:].index(mock_nvim.current.line)
    next_line = mock_nvim.current.buffer[current_line_number + 1]

    av = AnsibleVaultNvim(mock_nvim)
    encrypted_value = to_text(av.encrypt("something"))
    new_lines_number = len(encrypted_value.split("\n"))
    av.ansible_encrypt()

    new_next_line = mock_nvim.current.buffer[current_line_number + new_lines_number]

    assert next_line == new_next_line
    assert mock_nvim.current.buffer[current_line_number] == "  var2: !vault |"
