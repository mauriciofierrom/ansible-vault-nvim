import pynvim
import os

from ansible.parsing import vault
from ansible.module_utils._text import to_bytes, to_text
from ansible.parsing.utils.yaml import from_yaml
from ansible.parsing.vault import VaultLib

@pynvim.plugin
class AnsibleVaultNvim(object):
    def __init__(self, nvim):
        self.nvim = nvim

    @pynvim.command('AnsibleDecryptAll')
    def decrypt_command(self):
        self.populate_location_list(self.nvim.current.buffer[:])

    @pynvim.function('SplitSecret')
    def view_secret(self, args):
        line = self.nvim.current.line
        line_number = line.split(" ")[1]
        value = line.split(" ")[2].replace(":", "")
        self.nvim.command("wincmd k")
        self.nvim.command("vsplit /tmp/" + str(line_number) + str(value))

    @pynvim.command('AnsibleEncrypt')
    def ansible_encrypt(self):
        current_line = self.nvim.current.line
        current_var = current_line.split(":")[0]
        current_buffer = self.nvim.current.buffer
        decrypted_vars = self.decrypt("\n".join(current_buffer))
        if current_var and decrypted_vars[current_var]:
            encrypted_content = self.encrypt(current_var, self.buffer_as_string(current_buffer))
            current_line_number = current_buffer[:].index(current_line)
            end_line = self.find_end_or_other_var(decrypted_vars, current_buffer, current_line_number)
            lines = [current_var + ": !vault |"] + [(" " * 4) + i
                for i in encrypted_content.decode('utf-8').strip().split("\n")]
            self.nvim.current.buffer[current_line_number : end_line + 1] = lines

    def buffer_as_string(self, raw_buffer):
        return "\n".join(raw_buffer[:])

    def find_end_or_other_var(self, decrypted_vars, current_buffer, current_line_number):
        if (current_line_number >= len(current_buffer) - 1) or (current_buffer[current_line_number].split(":")[0] in decrypted_vars):
            return current_line_number
        else:
            return self.find_end_or_other_var(decrypted_vars, current_buffer, current_line_number + 1)

    def encrypt(self, current_var, current_buffer_content):
        return VaultLib().encrypt(self.decrypt(current_buffer_content)[current_var], self.generate_secrets())

    def generate_secrets(self):
        vault_path = self.nvim.vars.get("ansible_vault_path", "vault")
        with open(vault_path) as vault_file:
            secret_text = vault_file.read().strip()
            secret_bytes = to_bytes(secret_text)
            secrets = vault.VaultSecret(secret_bytes)
            secrets.load()
            return secrets

    def decrypt(self, encrypted_content):
        return from_yaml(encrypted_content, "current buffer", True, [("", self.generate_secrets())])

    def get_vault_variables(self, raw_buffer):
        """
        Gets only variables that contain the !vault tag
        """
        return [i for i in raw_buffer if "!vault" in i]

    def format_entry(self, entry):
        trimmed_entry = entry.strip().replace("\n", "")
        if len(trimmed_entry) + 3 > self.nvim.current.window.width:
            return trimmed_entry[:self.nvim.current.window.width-6] + "..."
        else:
            return trimmed_entry

    def generate_error_list(self, raw_buffer_list):
        error_list = []
        variables = self.decrypt("\n".join(raw_buffer_list))
        vault_variables = self.get_vault_variables(raw_buffer_list)

        for x in variables:
            for l in vault_variables:
                if l.split(":")[0] == x:
                    entry = str(raw_buffer_list.index(l)+1) + " " + str(x) + ": " + str(variables[x])
                    error_list.append(self.format_entry(entry))
                    # Save a tmp file that we can show on pressing v on a line of the location list
                    # TODO: Find a better/safer way to do this.
                    with open("/tmp/" + str(raw_buffer_list.index(l)+1) + str(x), "w") as f:
                        f.write(str(variables[x]))
        return error_list

    def save_to_tmp_file(self, line, variable, content):
        with open("/tmp/" + str(line) + variable) as f:
            f.write(content)

    def populate_location_list(self, raw_buffer_list):
        error_list = self.generate_error_list(raw_buffer_list)

        with open("/tmp/efile", "w") as error_file:
            error_file.write("\n".join(error_list))

        self.nvim.command("lf! /tmp/efile")
        self.nvim.command("lopen")
        self.nvim.command('nnoremap <silent> <buffer> v :call SplitSecret() <CR>')
        self.nvim.command('nnoremap <silent> <buffer> q :q<CR>')

        os.remove("/tmp/efile")