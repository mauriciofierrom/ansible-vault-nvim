[![Build Status](https://travis-ci.com/mauriciofierrom/ansible-vault-nvim.svg?branch=master)](https://travis-ci.com/mauriciofierrom/ansible-vault-nvim)

# Ansible Vault Nvim Plugin

## Not ready for production.

A plugin to help with inlined vault variables.

### Dependencies

```
pip3 install ansible pynvim
```

### To install:

```
Plug 'mauriciofierrom/ansible-vault-nvim', { 'do' : ':UpdateRemotePlugins' }
```

## How to use:

- `:AnsibleDecryptAll` to show the location list with all the variables. Press `v` in the list to open a vertical split with the contents or `q` to close the list.
- `:AnsibleEncrypt` on the line containing a variable to encrypt its value.