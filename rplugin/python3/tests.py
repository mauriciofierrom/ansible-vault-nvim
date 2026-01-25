import pytest
from unittest.mock import Mock, MagicMock
import ui
import ansible_helper
import nvim_helper


@pytest.fixture
def lines() -> list[str]:
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
        "    3065",
    ]


@pytest.fixture
def mock_nvim() -> Mock:
    nvim = Mock()
    vs = {"ansible_vault_path": "secrets/vault"}
    nvim.vars = MagicMock()
    nvim.vars.__getitem__.side_effect = vs.__getitem__
    nvim.vars.get.side_effect = vs.get
    return nvim


@pytest.fixture
def secrets(mock_nvim: Mock) -> ansible_helper.vault.VaultSecret:
    return ansible_helper.generate_secrets(mock_nvim)


def test_format_entry(mock_nvim: Mock) -> None:
    entry = "some\ncontent\nlonger\nthan\nwidth"
    mock_nvim.current.window.width = 15

    assert ui.format_entry(mock_nvim, entry) == "someconte..."
    assert len(ui.format_entry(mock_nvim, entry)) <= 15

    entry = "some"
    assert ui.format_entry(mock_nvim, entry) == "some"


def test_extract_vault_data(
    lines: list[str], secrets: ansible_helper.vault.VaultSecret
) -> None:
    decrypted_vars = ansible_helper.extract_vault_data(lines, secrets)

    expected = [
        {"line": 1, "var": "variable", "val": "a"},
        {"line": 10, "var": "var1", "val": "a"},
        {"line": 19, "var": "another_variable", "val": "a"},
        {"line": 27, "var": "yet_another", "val": "a"},
    ]

    assert decrypted_vars == expected


def test_generate_error_list(
    mock_nvim: Mock, lines: list[str], secrets: ansible_helper.vault.VaultSecret
) -> None:
    mock_nvim.current.window.width = 40

    decrypted_vars = ansible_helper.extract_vault_data(lines, secrets)
    error_list = nvim_helper.generate_error_list(mock_nvim, decrypted_vars)

    assert error_list == [
        {"text": "1 variable: a"},
        {"text": "10 var1: a"},
        {"text": "19 another_variable: a"},
        {"text": "27 yet_another: a"},
    ]


def test_generate_entry() -> None:
    assert ui.generate_entry({"var": "var1", "val": "a", "line": 10}) == "10 var1: a"


def test_encrypt(
    mock_nvim: Mock, lines: list[str], secrets: ansible_helper.vault.VaultSecret
) -> None:
    buffer_mock = MagicMock()
    buffer_mock.__iter__.return_value = iter(lines)
    buffer_mock.__getitem__.side_effect = lines.__getitem__
    mock_nvim.current.buffer = buffer_mock
    mock_nvim.current.line = "  var2: something"

    nvim_helper.ansible_encrypt(mock_nvim, secrets)

    # Check that the buffer was modified correctly
    args, _ = mock_nvim.current.buffer.__setitem__.call_args
    assert args[1][0] == "  var2: !vault |"
