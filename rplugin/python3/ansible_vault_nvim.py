""" A Remote plugin to decrypt in-line ansible-vault variables """
import os
import pynvim
import pdb

from ansible.parsing import vault
from ansible.module_utils._text import to_bytes, to_text
from ansible.parsing.utils.yaml import from_yaml
from ansible.parsing.vault import VaultLib
from ansible.parsing.yaml.loader import AnsibleLoader
from yaml import ScalarNode, MappingNode

@pynvim.plugin
class AnsibleVaultNvim:
    """ A class to perform Ansible Vault operations on Neovim buffers. """

    def __init__(self, nvim):
        self.nvim = nvim

    @pynvim.command('AnsibleDecryptAll')
    def decrypt_command(self):
        """
        Adds the AnsibleDecryptAll command to Neovim.

        The command decrypts all vault-encrypted in-line variables present
        in the active buffer and populates the location list with the
        decrypted values:

        <line-number> <variable-name> <decrypted-value>

        The output is trimmed to fit the available width but can be opened
        in-full in a vertical split (see view_secret).
        """

        self.populate_location_list(self.nvim.current.buffer[:])

    @pynvim.function('SplitSecret')
    def view_secret(self, _):
        """
        A Neovim function that only works in the location list populated by the
        AnsibleDecryptAll command.

        Upon pressing v on a line of the location list it opens a vertical split
        with the whole decrypted contents of the variable.

        Caveats:

        In order to be able to show the variable in a buffer it has to be saved
        in the /tmp folder, which is a security concern.
        """

        line_number = self.nvim.current.line.split(" ")[1]
        variable_name = self.nvim.current.line.split(" ")[2].replace(":", "")

        self.nvim.command("wincmd k")
        self.nvim.command("vsplit /tmp/" + line_number + "-" + variable_name)

    @pynvim.command('AnsibleEncrypt')
    def ansible_encrypt(self):
        """
        A Neovim command to encrypt the scalar value under the current line.
        """

        current_line = self.nvim.current.line
        original_var = current_line.split(":")[0]
        current_line_number = self.nvim.current.buffer[:].index(current_line)
        regular_scalars = self.get_scalars(self.nvim.current.buffer[:], lambda x: x.tag != "!vault")
        to_encrypt = list(filter(lambda x: x["line"] == (current_line_number + 1),
            regular_scalars))[0]["val"]
        encrypted_content = self.encrypt(to_encrypt)
        lines = [original_var + ": !vault |"] + [(" " * 4) + i
                for i in encrypted_content.decode('utf-8').strip().split("\n")]
        tmp_rest = self.nvim.current.buffer[current_line_number + 1:]
        self.nvim.current.buffer[current_line_number : len(encrypted_content)] = lines
        # Check this abomination
        self.nvim.current.buffer[current_line_number + len(encrypted_content) +
                1:] = tmp_rest

    @staticmethod
    def _buffer_as_string(raw_buffer):
        return "\n".join(raw_buffer[:])

    def encrypt(self, to_encrypt):
        """Encrypts a scalar value using ansible-vault"""

        return VaultLib().encrypt(to_encrypt, self.generate_secrets())

    # TODO: Improve support for vault files with multiple secrets
    def generate_secrets(self):
        """
        Generates secrets from a global setting pointing to a vault file, to be
        used for de/encryption.
        """

        vault_path = self.nvim.vars.get("ansible_vault_path", "vault")
        with open(vault_path) as vault_file:
            secret_text = vault_file.read().strip()
            secret_bytes = to_bytes(secret_text)
            secrets = vault.VaultSecret(secret_bytes)
            secrets.load()
            return secrets

    def format_entry(self, entry):
        """
        Trim the entry if it exceeds the window size. Include three dots at
        the end to let the user know the contents aren't complete.
        """

        trimmed_entry = entry.strip().replace("\n", "")
        if len(trimmed_entry) + 3 > self.nvim.current.window.width:
            return trimmed_entry[:self.nvim.current.window.width-6] + "..."

        return trimmed_entry

    def generate_error_list(self, raw_buffer_list):
        """Creates the error list that contains the entries."""

        error_list = []
        vault_variables = self.get_scalars(raw_buffer_list, lambda x: x.tag == "!vault")

        for vault_var in vault_variables:
            # TODO: This is done for now because we don't know how to change the
            # buffer to the previous/parent of the loclist
            with open("/tmp/" + str(vault_var["line"]) + "-" + vault_var["var"], "w") as file:
                file.write(to_text(vault_var["val"]))

            entry = self.generate_entry(vault_var)
            error_list = error_list + [self.format_entry(entry)]

        error_list.sort()

        return error_list

    # TODO: Restore the formatted path
    # TODO: Still need to write secrets to tmp dir
    def generate_entry(self, decrypted_var):
        """Generate a raw error list entry <line-number> <var>: <val>"""

        return str(decrypted_var["line"]) + " " + str(decrypted_var["var"]) + ": " + str(to_text(decrypted_var["val"]))

    def populate_location_list(self, raw_buffer_list):
        """
        Populates the location list with the error list containing the
        decrypted variables. This also adds the mapping to the function that
        opens the decrypted variables in a vertical split
        """

        error_list = self.generate_error_list(raw_buffer_list)

        with open("/tmp/efile", "w") as error_file:
            error_file.write("\n".join(error_list))

        self.nvim.command("lf! /tmp/efile")
        self.nvim.command("lopen")
        self.nvim.command('nnoremap <silent> <buffer> v :call SplitSecret() <CR>')
        self.nvim.command('nnoremap <silent> <buffer> q :q<CR>')

        os.remove("/tmp/efile")

    def recurse_mappings(self, tup, secrets, vals, predicate):
        """
        Recurses the MappingNode to fetch only ScalarNode that satisfy the
        given predicate
        """

        var = tup[0]
        val = tup[1]

        # TODO: Wonky. Fix this.
        if isinstance(tup[1], ScalarNode) and predicate(val):
            vals.append({
                "var": var.value,
                "val":
                VaultLib([("default",secrets)]).decrypt(to_bytes(val.value)) if
                val.tag == "!vault" else val.value,
                "line": var.start_mark.line + 1
                })

        if isinstance(tup[1], MappingNode):
            for mapping in tup[1].value:
                self.recurse_mappings(mapping, secrets, vals, predicate)

        return vals

    def get_scalars(self, raw_buffer_list, predicate):
        """
        Gets all scalar values that satisfy the predicate. Any encrypted value
        is decrypted.
        """

        secrets = self.generate_secrets()
        loader = AnsibleLoader(self._buffer_as_string(raw_buffer_list), "some", [("default", secrets)])
        vals = []

        scalar_nodes = loader.get_single_node()

        for node in scalar_nodes.value:
            self.recurse_mappings(node, secrets, vals, predicate)

        return vals
