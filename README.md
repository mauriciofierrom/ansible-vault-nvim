# Ansible Vault Nvim Plugin

A plugin to help with inline ansible-vault variables.

> [!NOTE]
> This plugin is a work in progress and under sparse development.

## Features

- Decrypt and view all vault variables in a location list
- View decrypted secrets in split scratch buffers for improved visibility
- Encrypt plain text variables in place

## Dependencies

The following python packages must be available to Neovim's python:

- `ansible>=13.2.0`
- `pynvim>=0.6.0`

## Installation

E.g. via `vim-plug`
```vim
Plug 'mauriciofierrom/ansible-vault-nvim', { 'do' : ':UpdateRemotePlugins' }
```

## Usage

1. Set the vault password file path:
```vim
   let g:ansible_vault_path = 'path/to/vault-password-file'
```
   (Defaults to `vault` if not set)

2. **Decrypt all variables**: Use `:AnsibleDecryptAll` to populate the location list with all decrypted variables
   - Press `v` on any entry to view the full decrypted content in a split
   - Press `q` to close the location list

3. **Encrypt a variable**: Position cursor on a line with a plain text variable and run `:AnsibleEncrypt`

## Limitations

- Only supports single vault-id
- Requires password file authentication

## Development

### First-time setup

1. Install development dependencies:
```bash
   uv sync
```

Most work is done inside the `rplugin/python3` directory

### Run tests
```bash
   uv run pytest
```

### Typecheck
```bash
   uv run pyright
```

### Lint
```bash
   uv run ruff check .
```

### Format
```bash
   uv run ruff format .
```

### Testing in Neovim

#### Install the plugin locally

E.g. via `vim-plug`

```vim
   " In your nvim config
   Plug '/absolute/path/to/ansible-vault-nvim', { 'do': ':UpdateRemotePlugins' }
```
#### Via socket + python shell

1. Start Neovim with a socket:
```bash
   NVIM_LISTEN_ADDRESS=/tmp/nvim nvim
```

2. In a Python shell
```python
   import ansible_vault_nvim
   from pynvim import attach

   nvim = attach('socket', path='/tmp/nvim')
   plugin = ansible_vault_nvim.AnsibleVaultNvim(nvim)
```

3. You can then use the editor and where appropriate run plugin commands:

``` python
   plugin.decrypt_command()
```
