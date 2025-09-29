import argparse
import getpass
from typing import Optional

from .storage import EncryptedStorage
from .click_app import cli


def prompt_password(prompt: str = "Password: ") -> str:
    return getpass.getpass(prompt)


def cmd_init(args: argparse.Namespace) -> None:
    password = prompt_password("Set password: ")
    confirm = prompt_password("Confirm password: ")
    if password != confirm:
        print("Passwords do not match.")
        return
    store = EncryptedStorage()
    if store.exists() and not getattr(args, "force", False):
        print("Vault already exists. Use --force to overwrite.")
        return
    store.initialize(password)
    print("Initialized encrypted todo vault.")


def cmd_add(args: argparse.Namespace) -> None:
    store = EncryptedStorage()
    if not store.exists():
        print("No vault found. Run: python -m todo init")
        return
    password = prompt_password()
    vault = store.load(password)
    task = vault.add_task(args.text)
    store.save(password, vault)
    print(f"Added task #{task.id}")


def cmd_list(_: argparse.Namespace) -> None:
    store = EncryptedStorage()
    if not store.exists():
        print("No vault found. Run: python -m todo init")
        return
    password = prompt_password()
    vault = store.load(password)
    if not vault.tasks:
        print("No tasks.")
        return
    for t in vault.tasks:
        status = "[x]" if t.done else "[ ]"
        print(f"{status} {t.id}: {t.text}")


def cmd_done(args: argparse.Namespace) -> None:
    store = EncryptedStorage()
    if not store.exists():
        print("No vault found. Run: python -m todo init")
        return
    password = prompt_password()
    vault = store.load(password)
    task = vault.get_task(args.id)
    if not task:
        print("Task not found.")
        return
    task.done = True
    store.save(password, vault)
    print(f"Marked #{args.id} done")


def cmd_remove(args: argparse.Namespace) -> None:
    store = EncryptedStorage()
    if not store.exists():
        print("No vault found. Run: python -m todo init")
        return
    password = prompt_password()
    vault = store.load(password)
    if vault.remove_task(args.id):
        store.save(password, vault)
        print(f"Removed #{args.id}")
    else:
        print("Task not found.")


def cmd_clear(_: argparse.Namespace) -> None:
    store = EncryptedStorage()
    if not store.exists():
        print("No vault found. Run: python -m todo init")
        return
    password = prompt_password()
    vault = store.load(password)
    count = vault.clear_completed()
    store.save(password, vault)
    print(f"Cleared {count} completed task(s)")


def cmd_change_password(_: argparse.Namespace) -> None:
    store = EncryptedStorage()
    if not store.exists():
        print("No vault found. Run: python -m todo init")
        return
    old = prompt_password("Current password: ")
    new = prompt_password("New password: ")
    confirm = prompt_password("Confirm new password: ")
    if new != confirm:
        print("Passwords do not match.")
        return
    try:
        store.change_password(old, new)
        print("Password changed.")
    except Exception:
        print("Failed to change password. Wrong current password?")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="todo", description="Encrypted Todo CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init", help="initialize vault")
    p_init.add_argument("--force", action="store_true", help="overwrite existing vault")
    p_init.set_defaults(func=cmd_init)

    p_add = sub.add_parser("add", help="add a task")
    p_add.add_argument("text", help="task text")
    p_add.set_defaults(func=cmd_add)

    p_list = sub.add_parser("list", help="list tasks")
    p_list.set_defaults(func=cmd_list)

    p_done = sub.add_parser("done", help="mark task done")
    p_done.add_argument("id", type=int)
    p_done.set_defaults(func=cmd_done)

    p_rm = sub.add_parser("remove", help="remove a task")
    p_rm.add_argument("id", type=int)
    p_rm.set_defaults(func=cmd_remove)

    p_clear = sub.add_parser("clear", help="clear completed tasks")
    p_clear.set_defaults(func=cmd_clear)

    p_chp = sub.add_parser("change-password", help="change password")
    p_chp.set_defaults(func=cmd_change_password)

    return parser


def main() -> None:
    cli(standalone_mode=True)


if __name__ == "__main__":
    main()
