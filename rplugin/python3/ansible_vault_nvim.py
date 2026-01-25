import pynvim
import ansible_helper
import nvim_helper
from typing import Optional, Any


@pynvim.plugin
class AnsibleVaultNvim:
    """A class to perform Ansible Vault operations on Neovim buffers."""

    def __init__(self, nvim) -> None:
        self.nvim = nvim
        self.secrets: Optional[ansible_helper.vault.VaultSecret] = None
        self.decrypted_cache: dict[str, str] = {}

    def _get_secrets(self) -> ansible_helper.vault.VaultSecret:
        if not self.secrets:
            self.secrets = ansible_helper.generate_secrets(self.nvim)
        return self.secrets

    @pynvim.command("AnsibleDecryptAll")
    def decrypt_command(self) -> None:
        """Adds the AnsibleDecryptAll command to Neovim."""
        secrets = self._get_secrets()
        decrypted_vars = ansible_helper.extract_vault_data(
            self.nvim.current.buffer[:], secrets
        )
        self.decrypted_cache = {
            f"{v['line']}-{v['var']}": v["val"] for v in decrypted_vars
        }

        nvim_helper.populate_location_list(self.nvim, decrypted_vars)

    @pynvim.function("SplitSecret")
    def view_secret(self, _: Any) -> None:
        """Opens decrypted variable in a vertical split."""
        nvim_helper.view_secret(self.nvim, self.decrypted_cache)

    @pynvim.command("AnsibleEncrypt")
    def ansible_encrypt(self) -> None:
        """
        A Neovim command to encrypt the scalar value under the current line.
        """
        secrets = self._get_secrets()
        nvim_helper.ansible_encrypt(self.nvim, secrets)
