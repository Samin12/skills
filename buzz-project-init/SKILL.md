---
name: buzz-project-init
description: Initialize a new project — creates a GitHub repo with a README, clones it locally, and announces it on Buzz with a project wrapper. Use when the user says "create new project", "init project", or "new repo".
metadata:
  trigger: "create new project", "init project", "new project", "new repo"
  author: Samin Yasar
---

# Buzz Project Init

Create a new GitHub-backed project and announce it on Buzz in one shot.

## What It Does

1. Creates a **public GitHub repo** under the user's account with a README
2. **Clones it locally** to `REPOS/<project-id>/`
3. **Announces the repo on Buzz** with the GitHub clone URL
4. **Creates a Buzz project** that groups the repo and binds it to the current channel
5. Returns the GitHub URL and Buzz project link

## Usage

The user provides a project name. Everything else is automatic.

```
User: "Create new project called my-cool-app"
```

## Steps

### 1. Parse Input

Extract the project name from the user's message. Convert to kebab-case for the repo ID (e.g., "My Cool App" → `my-cool-app`).

If no name is given, ask for one.

### 2. Create GitHub Repo

```bash
gh repo create <github-username>/‹project-id› --public --description "‹description›"
```

Use the user's GitHub account. Get the username from `gh auth status`. If no description is provided, use the project name.

### 3. Clone Locally and Add README

```bash
cd REPOS/ && git clone https://github.com/<user>/<project-id>.git
```

Create a `README.md` with the project name as the heading and a one-line description. Commit and push.

```markdown
# Project Name

Description of the project.
```

### 4. Announce on Buzz

```bash
buzz repos create \
  --id <project-id> \
  --name "<Project Name>" \
  --description "<description>" \
  --clone https://github.com/<user>/<project-id>.git \
  --web https://github.com/<user>/<project-id> \
  --channel <current-channel-uuid>
```

### 5. Create Buzz Project

```bash
buzz projects create <project-id> \
  --name "<Project Name>" \
  --description "<description>" \
  --channel <current-channel-uuid> \
  --repo <project-id>
```

### 6. Report Back

Post a message to the channel with:
- GitHub repo URL
- Buzz project link (from the `link` field in the create response)
- Confirmation that README exists

## Conventions

- **Repo IDs:** kebab-case, lowercase, max 64 chars
- **GitHub account:** Always use the authenticated `gh` user
- **Local path:** Always clone to `REPOS/<project-id>/`
- **README:** Every project gets one. Always.
- **Channel binding:** Always bind to the channel where the request was made
- **Clone URL:** Always points to GitHub. Buzz repos reference GitHub as the source of truth.

## Error Handling

- If the GitHub repo already exists, tell the user and ask if they want to use it
- If the Buzz repo ID is taken, append a number suffix
- If `gh` auth fails, tell the user to run `gh auth login`
