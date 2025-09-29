import getpass
import time
import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .storage import EncryptedStorage, list_vaults, delete_vault, DEFAULT_VAULT_NAME


def prompt_password(prompt: str = "Password: ") -> str:
    return getpass.getpass(prompt)


@click.group(help="Encrypted Todo CLI")
@click.option("--vault", "vault_name", default=DEFAULT_VAULT_NAME, show_default=True, help="vault name")
@click.pass_context
def cli(ctx: click.Context, vault_name: str) -> None:
    ctx.ensure_object(dict)
    ctx.obj["vault_name"] = vault_name


@cli.command()
@click.option("--force", is_flag=True, help="overwrite existing vault")
@click.pass_context
def init(ctx: click.Context, force: bool) -> None:
    console = Console()
    store = EncryptedStorage(vault_name=ctx.obj["vault_name"])
    if store.exists() and not force:
        click.echo("Vault already exists. Use --force to overwrite.")
        return
    password = prompt_password("Set password: ")
    confirm = prompt_password("Confirm password: ")
    if password != confirm:
        click.echo("Passwords do not match.")
        return

    with Progress(
        SpinnerColumn(spinner_name="dots"),
        TextColumn("[bold]The Vault[/bold]"),
        transient=True,
        console=console,
    ) as progress:
        task_id = progress.add_task("initializing", total=None)
        store.initialize(password)
        time.sleep(0.6)
        progress.remove_task(task_id)

    console.print("Initialized encrypted todo vault.")


@cli.command()
@click.argument("text")
@click.pass_context
def add(ctx: click.Context, text: str) -> None:
    store = EncryptedStorage(vault_name=ctx.obj["vault_name"])
    if not store.exists():
        click.echo("No vault found. Run: todo init")
        return
    password = prompt_password()
    vault = store.load(password)
    task = vault.add_task(text)
    store.save(password, vault)
    click.echo(f"Added task #{task.id}")


@cli.command(name="list")
@click.pass_context
def list_cmd(ctx: click.Context) -> None:
    store = EncryptedStorage(vault_name=ctx.obj["vault_name"])
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
@click.pass_context
def done(ctx: click.Context, id: int) -> None:
    store = EncryptedStorage(vault_name=ctx.obj["vault_name"])
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
@click.pass_context
def remove(ctx: click.Context, id: int) -> None:
    store = EncryptedStorage(vault_name=ctx.obj["vault_name"])
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
@click.pass_context
def clear(ctx: click.Context) -> None:
    store = EncryptedStorage(vault_name=ctx.obj["vault_name"])
    if not store.exists():
        click.echo("No vault found. Run: todo init")
        return
    password = prompt_password()
    vault = store.load(password)
    count = vault.clear_completed()
    store.save(password, vault)
    click.echo(f"Cleared {count} completed task(s)")


@cli.command(name="change-password")
@click.pass_context
def change_password(ctx: click.Context) -> None:
    store = EncryptedStorage(vault_name=ctx.obj["vault_name"])
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


@cli.group(help="Manage vaults")
def vaults() -> None:
    pass


@vaults.command("list")
def vaults_list() -> None:
    names = list_vaults()
    if not names:
        click.echo("No vaults found.")
        return
    for n in names:
        click.echo(n)


@vaults.command("remove")
@click.argument("name")
def vaults_remove(name: str) -> None:
    if delete_vault(name):
        click.echo(f"Removed vault '{name}'")
    else:
        click.echo("Vault not found.")
