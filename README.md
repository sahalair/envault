# envault

> A local-first secrets manager that syncs encrypted `.env` files across machines using a git-backed store.

---

## Installation

```bash
pip install envault
```

Or with [pipx](https://pypa.github.io/pipx/) for isolated installs:

```bash
pipx install envault
```

---

## Usage

**Initialize a vault in your project:**

```bash
envault init
```

**Add a secret:**

```bash
envault set DATABASE_URL "postgres://user:pass@localhost/mydb"
```

**Pull secrets into a local `.env` file:**

```bash
envault pull
```

**Push local changes back to the vault:**

```bash
envault push
```

**Use secrets in a command without writing them to disk:**

```bash
envault run -- python app.py
```

Secrets are AES-256 encrypted before being committed to the configured git remote. Each machine authenticates using a local key stored in `~/.envault/keyring`.

---

## How It Works

1. Secrets are encrypted locally using a machine-derived key.
2. Encrypted blobs are committed to a designated git repository.
3. Authorized machines decrypt and inject secrets at runtime.

No third-party servers. No SaaS. Just git.

---

## License

MIT © [envault contributors](https://github.com/yourname/envault)