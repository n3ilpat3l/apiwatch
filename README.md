# APIWatch

Async API health checker that loads APIs from a YAML file and optionally sends alerts to Slack/Discord webhooks.

Quick start

1. Create a virtualenv and install deps:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Update `apis.yaml` with your APIs and webhook URLs.

3. Run a check:

```bash
python -m apiwatch.apiwatch check apis.yaml
```

Run tests

```bash
pytest -q
```

Notes

- This repository includes a minimal `tests/test_apiwatch.py` used for unit testing. It uses mocking to avoid network calls.
- Consider adding CI (GitHub Actions) and improving alert payload handling.
