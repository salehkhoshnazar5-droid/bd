`uvicorn` resolves the value passed to `--host` using the OS resolver (`getaddrinfo`).
If the hostname is not present in local DNS/hosts, startup fails.

Example failing command:

```bash
uvicorn app.main:app --reload --host kerman_bd --port 8011
```

## 1) Verify current resolution

Run one of these:

```bash
ping kerman_bd
```

```bash
python -c "import socket; print(socket.getaddrinfo('kerman_bd', 8011))"
```

If resolution fails, continue with host-file mapping.

## 2) Add host mapping

Add this exact line to your hosts file:

```text
127.0.0.1    kerman_bd
```

- Windows file: `C:\Windows\System32\drivers\etc\hosts`
- Linux/macOS file: `/etc/hosts`

Notes:
- Use administrator/root privileges when editing.
- Use plain text encoding (no `.txt` extension on Windows).
- Keep one mapping per line and avoid hidden characters.

## 3) Flush DNS cache

After saving hosts file, flush cache:

- Windows:

```bash
ipconfig /flushdns
```

- Linux (systemd):

```bash
sudo resolvectl flush-caches
```

- macOS:

```bash
sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder
```

## 4) Confirm mapping works

```bash
ping kerman_bd
```

Expected: replies from `127.0.0.1`.

Optional direct check:

```bash
python - <<'PY'
import socket
print(sorted({x[4][0] for x in socket.getaddrinfo('kerman_bd', 8011)}))
PY
```

Expected output includes `127.0.0.1`.

## 5) Start FastAPI

```bash
uvicorn app.main:app --reload --host kerman_bd --port 8011
```

## 6) Workaround (always valid)

If custom hostname resolution is blocked by policy, start directly on loopback:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8011
```

## 7) If it still fails

Check:
- Security software/firewall that intercepts local name resolution.
- VPN/proxy tools that override DNS or hosts lookup order.
- Application-level config that overrides host binding (env vars, startup scripts, container config).