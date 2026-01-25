import ansible_helper
from ansible_helper import DecryptedVar
import ui


def populate_location_list(nvim, decrypted_vars: list[DecryptedVar]) -> None:
    """
    Populates the location list with the error list containing the
    decrypted variables. This also adds the mapping to the function that
    opens the decrypted variables in a vertical split
    """
    # Generate formatted error list
    error_list = generate_error_list(nvim, decrypted_vars)

    # Create location list
    nvim.call("setloclist", 0, error_list, "r")
    nvim.command("lopen")
    nvim.command("nnoremap <silent> <buffer> v :call SplitSecret() <CR>")
    nvim.command("nnoremap <silent> <buffer> q :q<CR>")


def view_secret(nvim, decrypted_cache: dict[str, str]) -> None:
    """
    A Neovim function that only works in the location list populated by the
    AnsibleDecryptAll command.
    """
    line_number = nvim.current.line.split(" ")[1]
    variable_name = nvim.current.line.split(" ")[2].replace(":", "")

    # Retrieve from cache
    cache_key = f"{line_number}-{variable_name}"
    content = decrypted_cache.get(cache_key, "Not found")

    # Create scratch buffer
    nvim.command("wincmd k")
    nvim.command("vnew")
    nvim.current.buffer[:] = content.split("\n")
    nvim.command("setlocal buftype=nofile bufhidden=wipe")
    nvim.command(f"file {variable_name}")


def ansible_encrypt(nvim, secrets: ansible_helper.vault.VaultSecret) -> None:
    """
    A Neovim command to encrypt the scalar value under the current line.
    """
    current_line = nvim.current.line
    original_var = current_line.split(":")[0]

    # Use a copy for buffer operations to avoid issues with mock objects
    buffer_content = list(nvim.current.buffer)
    current_line_number = buffer_content.index(current_line)

    regular_scalars = ansible_helper.get_scalars(
        buffer_content, lambda x: x.tag != "!vault", secrets
    )

    to_encrypt_list = [
        s for s in regular_scalars if s["line"] == current_line_number + 1
    ]
    if not to_encrypt_list:
        nvim.err_write("No scalar found on the next line to encrypt.\n")
        return

    to_encrypt = to_encrypt_list[0]["val"]
    encrypted_content = ansible_helper.encrypt(to_encrypt, secrets)

    INDENT = "    "
    lines = [f"{original_var}: !vault |"] + [
        f"{INDENT}{i}" for i in encrypted_content.decode("utf-8").strip().split("\n")
    ]

    nvim.current.buffer[current_line_number : current_line_number + 1] = lines


def generate_error_list(nvim, decrypted_vars: list[DecryptedVar]) -> list[dict]:
    """Format decrypted variables as error list entries."""
    error_list = []
    for decrypted_var in decrypted_vars:
        entry = ui.generate_entry(decrypted_var)
        error_list.append({"text": ui.format_entry(nvim, entry)})

    return sorted(error_list, key=lambda x: x["text"])
