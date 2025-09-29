import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional

from .crypto import encrypt_json, decrypt_json


DEFAULT_VAULT_NAME = "vault"


def get_data_dir() -> Path:
    base = os.getenv("APPDATA") or os.path.expanduser("~/.config")
    path = Path(base) / "encrypted_task_cli"
    path.mkdir(parents=True, exist_ok=True)
    return path


def vault_filename(vault_name: str) -> str:
    return f"{vault_name}.todo"


def list_vaults(directory: Optional[Path] = None) -> List[str]:
    directory = directory or get_data_dir()
    return [p.stem for p in directory.glob("*.todo")]


def delete_vault(vault_name: str, directory: Optional[Path] = None) -> bool:
    directory = directory or get_data_dir()
    fp = directory / vault_filename(vault_name)
    if fp.exists():
        fp.unlink()
        return True
    return False


@dataclass
class Task:
    id: int
    text: str
    done: bool = False


@dataclass
class Vault:
    next_id: int
    tasks: List[Task]

    @staticmethod
    def empty() -> "Vault":
        return Vault(next_id=1, tasks=[])

    def add_task(self, text: str) -> Task:
        task = Task(id=self.next_id, text=text, done=False)
        self.tasks.append(task)
        self.next_id += 1
        return task

    def get_task(self, task_id: int) -> Optional[Task]:
        for t in self.tasks:
            if t.id == task_id:
                return t
        return None

    def remove_task(self, task_id: int) -> bool:
        before = len(self.tasks)
        self.tasks = [t for t in self.tasks if t.id != task_id]
        return len(self.tasks) != before

    def clear_completed(self) -> int:
        before = len(self.tasks)
        self.tasks = [t for t in self.tasks if not t.done]
        return before - len(self.tasks)


class EncryptedStorage:
    def __init__(self, directory: Optional[Path] = None, vault_name: str = DEFAULT_VAULT_NAME):
        self.directory = directory or get_data_dir()
        self.vault_name = vault_name
        self.filepath = self.directory / vault_filename(vault_name)

    def exists(self) -> bool:
        return self.filepath.exists()

    def initialize(self, password: str) -> None:
        vault = Vault.empty()
        self._write_encrypted(password, vault)

    def load(self, password: str) -> Vault:
        data = self.filepath.read_bytes()
        obj = json.loads(data.decode("utf-8"))
        kdf_params = obj["kdf"]
        nonce = bytes.fromhex(obj["nonce"])
        ciphertext = bytes.fromhex(obj["data"])
        plaintext = decrypt_json(password, kdf_params, nonce, ciphertext)
        payload = json.loads(plaintext.decode("utf-8"))
        tasks = [Task(**t) for t in payload["tasks"]]
        return Vault(next_id=payload["next_id"], tasks=tasks)

    def save(self, password: str, vault: Vault) -> None:
        self._write_encrypted(password, vault)

    def change_password(self, old_password: str, new_password: str) -> None:
        vault = self.load(old_password)
        self._write_encrypted(new_password, vault)

    def _write_encrypted(self, password: str, vault: Vault) -> None:
        payload = json.dumps({
            "next_id": vault.next_id,
            "tasks": [asdict(t) for t in vault.tasks],
        }, ensure_ascii=False).encode("utf-8")
        kdf_params, nonce, ciphertext = encrypt_json(password, payload)
        wrapper = {
            "version": 1,
            "kdf": kdf_params,
            "nonce": nonce.hex(),
            "data": ciphertext.hex(),
        }
        self.filepath.write_text(json.dumps(wrapper, ensure_ascii=False, indent=2))
