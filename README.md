[![Build Status](https://travis-ci.com/mauriciofierrom/ansible-vault-nvim.svg?branch=main)](https://travis-ci.com/mauriciofierrom/ansible-vault-nvim)

# Ansible Vault Nvim Plugin

A plugin to help with inlined ansible-vault variables.

## Not ready for production.

This is currently a toy project. It has the following caveats:

- It insecurely stores the decrypted data in the `/tmp` directory to show it from the
  location list
- Doesn't support different vault ids

### Dependencies

```
pip3 install ansible pynvim
```

### To install:

```
Plug 'mauriciofierrom/ansible-vault-nvim', { 'do' : ':UpdateRemotePlugins' }
```

## How to use:

- We currently support only password files and treat it as the `default`
  vault-id. Set `let g:ansible_vault_path='path/vault-password-file'` to the path to your vault password file.
- Use `:AnsibleDecryptAll` to show the location list with all the decrypted variables. Press `v` in the location list to open a vertical split with the contents of the current highlighted variable or `q` to close the list.
- `:AnsibleEncrypt` on the line containing a variable to encrypt its value in
  place.
