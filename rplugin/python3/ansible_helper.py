from ansible.parsing import vault
from ansible.module_utils._text import to_bytes, to_text  # type: ignore
from ansible.parsing.vault import VaultLib
from ansible.parsing.yaml.loader import AnsibleLoader
from yaml import ScalarNode, MappingNode
from typing import Callable, TypedDict


class DecryptedVar(TypedDict):
    line: int
    var: str
    val: str


def _buffer_as_string(raw_buffer: list[str]) -> str:
    return "\n".join(raw_buffer)


def encrypt(to_encrypt: str, secrets: vault.VaultSecret) -> bytes:
    """Encrypts a scalar value using ansible-vault"""
    return VaultLib().encrypt(to_encrypt, secrets)


def generate_secrets(nvim) -> vault.VaultSecret:
    """
    Generates secrets from a global setting pointing to a vault file, to be
    used for de/encryption.
    """
    vault_path = nvim.vars.get("ansible_vault_path", "vault")
    with open(vault_path) as vault_file:
        secret_text = vault_file.read().strip()
        secret_bytes = to_bytes(secret_text)  # type: ignore
        secrets = vault.VaultSecret(secret_bytes)
        secrets.load()
        return secrets


def recurse_mappings(
    tup: tuple,
    secrets: vault.VaultSecret,
    vals: list[DecryptedVar],
    predicate: Callable,
) -> list[DecryptedVar]:
    """
    Recurses the MappingNode to fetch only ScalarNode that satisfy the
    given predicate
    """
    var = tup[0]
    val = tup[1]

    if isinstance(tup[1], ScalarNode) and predicate(val):
        decrypted_var: DecryptedVar = {
            "var": var.value,
            "val": VaultLib([("default", secrets)]).decrypt(to_bytes(val.value))  # type: ignore
            if val.tag == "!vault"
            else val.value,
            "line": var.start_mark.line + 1,
        }
        vals.append(decrypted_var)

    if isinstance(tup[1], MappingNode):
        for mapping in tup[1].value:
            recurse_mappings(mapping, secrets, vals, predicate)

    return vals


def get_scalars(
    raw_buffer_list: list[str], predicate: Callable, secrets: vault.VaultSecret
) -> list[DecryptedVar]:
    """
    Gets all scalar values that satisfy the predicate. Any encrypted value
    is decrypted.
    """
    loader = AnsibleLoader(_buffer_as_string(raw_buffer_list))
    vals: list[DecryptedVar] = []
    scalar_nodes = loader.get_single_node()

    for node in scalar_nodes.value:
        recurse_mappings(node, secrets, vals, predicate)

    return vals


def extract_vault_data(
    raw_buffer_list: list[str], secrets: vault.VaultSecret
) -> list[DecryptedVar]:
    """Extract and decrypt vault variables, returning structured data."""
    vault_variables = get_scalars(raw_buffer_list, lambda x: x.tag == "!vault", secrets)

    decrypted_vars: list[DecryptedVar] = [
        {
            "line": vault_var["line"],
            "var": vault_var["var"],
            "val": to_text(vault_var["val"]),  # type: ignore
        }
        for vault_var in vault_variables
    ]

    return decrypted_vars
