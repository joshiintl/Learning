# Gmail Promotional Cleanup Agent

A safe Python automation agent that finds Gmail messages categorized as promotions and moves messages older than three months to Gmail Trash.

## Safety behavior

- Runs in preview mode unless `--delete` is supplied.
- Moves matching messages to Trash rather than permanently deleting them.
- Never stores OAuth credentials in source control.
- Search is recalculated for every run using Gmail's `older_than:90d` syntax.

## Local setup

1. Create a Google Cloud OAuth Desktop App and enable the Gmail API.
2. Download the desktop credentials JSON as `credentials.json`.
3. Install dependencies:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   py -m pip install -r requirements.txt
   ```

4. Preview matching messages:

   ```powershell
   py gmail_cleanup.py
   ```

5. Move matches to Trash:

   ```powershell
   py gmail_cleanup.py --delete
   ```

The first run opens the Google consent screen. The authorized token is saved to `token.json` locally.

## Scheduled GitHub Actions setup

The workflow is scheduled to run daily at 06:00 UTC. Configure these repository secrets:

- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REFRESH_TOKEN`

A refresh token can be generated from the local OAuth flow. Enabling the workflow sends matching messages to Trash by default.

## Main command

```powershell
py gmail_cleanup.py --months 3 --delete
```
