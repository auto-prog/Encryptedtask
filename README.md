## Encrypted Task CLI

A simple Python CLI todo tool that stores tasks encrypted. Unlock with a password, using modern AES-GCM and Argon2id key derivation.

### Features
- Initialize an encrypted task vault
- Add/list/complete/remove/clear tasks
- Change password (secure re-encryption)
- Multiple vaults with `--vault` and `vaults` management commands

### Quickstart
```bash
python -m venv .venv
. .venv/Scripts/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .  # creates `todo` console command

todo init
todo add "Buy milk"
todo list
```

### Multiple vaults
```bash
# work in a separate vault named "work"
todo --vault work init
todo --vault work add "Prepare slides"

todo vaults list
# remove a vault file
todo vaults remove work
```

### Security
- Argon2id via cryptography's KDF for password-based key derivation with random salt
- AES-256-GCM with fresh nonce per encryption
- Encrypted file includes KDF parameters and salt

Files are written to the user's config directory (platform aware). Avoid committing your vault to version control.

### Commands
- `init`: Create a new vault
- `add <text>`: Add a new task
- `list`: Show tasks
- `done <id>`: Mark task done
- `remove <id>`: Delete a task
- `clear`: Remove all completed tasks
- `change-password`: Re-encrypt vault with a new password
- `vaults list|remove`: Manage vault files

### Notes
- If you forget your password, data cannot be recovered.
- Back up your vault file if the tasks are important.
