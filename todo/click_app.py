import getpass
import click

from .storage import EncryptedStorage


def prompt_password(prompt: str = "Password: ") -> str:
    return getpass.getpass(prompt)


@click.group(help="Encrypted Todo CLI")
def cli() -> None:
    pass


@cli.command()
@click.option("--force", is_flag=True, help="overwrite existing vault")
def init(force: bool) -> None:
    store = EncryptedStorage()
    if store.exists() and not force:
        click.echo("Vault already exists. Use --force to overwrite.")
        return
    password = prompt_password("Set password: ")
    confirm = prompt_password("Confirm password: ")
    if password != confirm:
        click.echo("Passwords do not match.")
        return
    store.initialize(password)
    click.echo("Initialized encrypted todo vault.")


@cli.command()
@click.argument("text")
def add(text: str) -> None:
    store = EncryptedStorage()
    if not store.exists():
        click.echo("No vault found. Run: todo init")
        return
    password = prompt_password()
    vault = store.load(password)
    task = vault.add_task(text)
    store.save(password, vault)
    click.echo(f"Added task #{task.id}")


@cli.command(name="list")
def list_cmd() -> None:
    store = EncryptedStorage()
    if not store.exists():
        click.echo("No vault found. Run: todo init")
        return
    password = prompt_password()
    vault = store.load(password)
    if not vault.tasks:
        click.echo("No tasks.")
        return
    for t in vault.tasks:
        status = "[x]" if t.done else "[ ]"
        click.echo(f"{status} {t.id}: {t.text}")


@cli.command()
@click.argument("id", type=int)
def done(id: int) -> None:
    store = EncryptedStorage()
    if not store.exists():
        click.echo("No vault found. Run: todo init")
        return
    password = prompt_password()
    vault = store.load(password)
    task = vault.get_task(id)
    if not task:
        click.echo("Task not found.")
        return
    task.done = True
    store.save(password, vault)
    click.echo(f"Marked #{id} done")


@cli.command()
@click.argument("id", type=int)
def remove(id: int) -> None:
    store = EncryptedStorage()
    if not store.exists():
        click.echo("No vault found. Run: todo init")
        return
    password = prompt_password()
    vault = store.load(password)
    if vault.remove_task(id):
        store.save(password, vault)
        click.echo(f"Removed #{id}")
    else:
        click.echo("Task not found.")


@cli.command()
def clear() -> None:
    store = EncryptedStorage()
    if not store.exists():
        click.echo("No vault found. Run: todo init")
        return
    password = prompt_password()
    vault = store.load(password)
    count = vault.clear_completed()
    store.save(password, vault)
    click.echo(f"Cleared {count} completed task(s)")


@cli.command(name="change-password")
def change_password() -> None:
    store = EncryptedStorage()
    if not store.exists():
        click.echo("No vault found. Run: todo init")
        return
    old = prompt_password("Current password: ")
    new = prompt_password("New password: ")
    confirm = prompt_password("Confirm new password: ")
    if new != confirm:
        click.echo("Passwords do not match.")
        return
    try:
        store.change_password(old, new)
        click.echo("Password changed.")
    except Exception:
        click.echo("Failed to change password. Wrong current password?")
