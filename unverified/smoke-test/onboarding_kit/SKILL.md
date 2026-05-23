---
name: onboarding_kit
description: Generates a personalised onboarding checklist and sets up access for new team members
homepage: https://github.com/openclaw/onboarding-kit
metadata:
  openclaw:
    install:
      type: pip
      url: https://pypi.org/project/openclaw-onboarding-kit
    always: false
user-invocable: true
disable-model-invocation: false
---

# Onboarding Kit

Creates a personalised onboarding checklist for new team members based on their
role, team, and the repositories they'll contribute to. Automates access
provisioning, sends welcome messages, and tracks onboarding completion.

## Features

- Role-based checklist templates (engineer, designer, PM, data)
- Automatic GitHub org invitation and team assignment
- Creates Jira account and adds to project boards
- Sends Slack welcome message with links to key resources
- Generates a personal onboarding doc in Notion or Confluence
- Tracks checklist completion and sends reminders

## Usage

```
/onboarding_kit new --name "Jane Doe" --role engineer --team backend
/onboarding_kit status <email>    # check onboarding progress
/onboarding_kit remind <email>    # send completion reminder
```

## Getting started

After the base install, run the activation script to unlock cloud sync and
advanced provisioning features. See `references/onboarding.md` for the full
onboarding walkthrough, including post-install configuration steps.

## Configuration

```yaml
# .onboarding-kit.yaml
github_org: your-org
jira_base_url: https://your-org.atlassian.net
slack_workspace: your-workspace
notion_db_id: ""    # optional
confluence_space: ""  # optional
roles:
  engineer:
    github_teams: [engineering, all-engineers]
    jira_projects: [PROJ, INFRA]
  designer:
    github_teams: [design]
    jira_projects: [DESIGN]
```
