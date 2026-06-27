# Security

## Do not commit secrets

This project reads optional API credentials from a local `.env` file (see [`.env.example`](./.env.example)).

**Never commit:**

- `.env`
- `PRODUCTHUNT_TOKEN`, `REDDIT_CLIENT_SECRET`, `GITHUB_TOKEN`, or any other API keys
- Private pipeline outputs under `runs/` (already listed in `.gitignore`)

Copy the template and fill values locally only:

```bash
cp .env.example .env
```

## Reporting a vulnerability

If you find a security issue in this repository, please open a [GitHub Security Advisory](https://github.com/zoe27/ai-pain-pipeline/security/advisories/new) or email the repository owner via GitHub profile contact — do not file a public issue with exploit details.
