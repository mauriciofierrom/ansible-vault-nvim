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
            end_line = self.find_end_or_other_var(current_var, decrypted_vars, current_buffer, current_line_number)
            lines = [current_var + ": !vault |"] + [(" " * 4) + i
                for i in encrypted_content.decode('utf-8').strip().split("\n")]
            self.nvim.current.buffer[current_line_number : end_line + 1] = lines

    def buffer_as_string(self, raw_buffer):
        return "\n".join(raw_buffer[:])

    def find_end_or_other_var(self, key, decrypted_vars, current_buffer, current_line_number):
        var = current_buffer[current_line_number].split(":")[0].strip()
        if (current_line_number >= len(current_buffer) - 1) or (self.is_var(var, decrypted_vars) and var in self.get_var_siblings(key, decrypted_vars)) or not current_buffer[current_line_number].strip():
            return current_line_number
        else:
            return self.find_end_or_other_var(key, decrypted_vars, current_buffer, current_line_number + 1)

    def is_var(self, key, graph):
        if key in graph.keys():
            if not isinstance(graph[key], dict):
                return True
        else:
            for x in graph.keys():
                if isinstance(graph[x], dict):
                    found = self.is_var(key, graph[x])
                    if found is not None:
                        return found
        return False

    def get_var_siblings(self, key, graph):
        if key in graph.keys():
            keys = list(graph.keys())
            keys.remove(key)
            return keys
        else:
            for x in graph.keys():
                if isinstance(graph[x], dict):
                    sibls = self.get_var_siblings(key, graph[x])
                    if sibls:
                        return sibls
        return []

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
        return [i.strip().split(":")[0] for i in raw_buffer if "!vault" in i]

    def format_entry(self, entry):
        trimmed_entry = entry.strip().replace("\n", "")
        if len(trimmed_entry) + 3 > self.nvim.current.window.width:
            return trimmed_entry[:self.nvim.current.window.width-6] + "..."
        else:
            return trimmed_entry

    def generate_error_list(self, raw_buffer_list):
        error_list = []
        variables = self.decrypt("\n".join(raw_buffer_list))
        vault_variables = list(set(self.get_vault_variables(raw_buffer_list)))

        for vault_var in vault_variables:
            entries = self.generate_entry(vault_var, variables, raw_buffer_list)
            entries = list(map(self.format_entry, entries))
            error_list = error_list + entries

        error_list.sort()

        return error_list

    def generate_entry(self, vault_var, decrypted_vars, raw_buffer_list):
        paths_to_var = self.get_variable_paths(vault_var, decrypted_vars)
        entries = []

        for path in paths_to_var:
            path_stack = path.copy()
            path_stack.reverse()

            for line in raw_buffer_list:
                if not line.strip():
                    if not path == path_stack:
                        path_stack = path.copy()
                        path_stack.reverse()

                if path_stack and path_stack[-1] in line:
                    path_stack.pop()

                if not path_stack:
                    line_number = raw_buffer_list.index(line) + 1
                    formatted_path = " - ".join(path)
                    path.reverse()
                    value = self.get_value_in_path(decrypted_vars, path)
                    entry = str(line_number) + " " + formatted_path + ": " + str(value)
                    with open("/tmp/" + str(line_number) + vault_var, "w") as f:
                        f.write(str(value))
                    entries.append(entry)
                    break

        return entries

    def populate_location_list(self, raw_buffer_list):
        error_list = self.generate_error_list(raw_buffer_list)

        with open("/tmp/efile", "w") as error_file:
            error_file.write("\n".join(error_list))

        self.nvim.command("lf! /tmp/efile")
        self.nvim.command("lopen")
        self.nvim.command('nnoremap <silent> <buffer> v :call SplitSecret() <CR>')
        self.nvim.command('nnoremap <silent> <buffer> q :q<CR>')

        os.remove("/tmp/efile")

    def get_variable_paths(self, key, graph, visited=[], paths=[]):
        if key in graph.keys():
            paths.append(visited + [key])
        else:
            for x in graph.keys():
                visited.append(x)
                if isinstance(graph[x], dict):
                    self.get_variable_paths(key, graph[x], visited, paths)
                visited.pop()
        return list(filter(None, paths))

    def get_value_in_path(self, graph, indices):
        head = indices.pop()

        if not indices:
            return graph[head]
        else:
            return self.get_value_in_path(graph[head], indices)