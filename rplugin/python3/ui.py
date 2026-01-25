from ansible_helper import DecryptedVar


def format_entry(nvim, entry: str) -> str:
    """
    Trim the entry if it exceeds the window size. Include three dots at
    the end to let the user know the contents aren't complete.
    """
    trimmed_entry = entry.strip().replace("\n", "")
    if len(trimmed_entry) + 3 > nvim.current.window.width:
        return trimmed_entry[: nvim.current.window.width - 6] + "..."

    return trimmed_entry


def generate_entry(decrypted_var: DecryptedVar) -> str:
    """Generate a raw error list entry <line-number> <var>: <val>"""
    return f"{decrypted_var['line']} {decrypted_var['var']}: {decrypted_var['val']}"
