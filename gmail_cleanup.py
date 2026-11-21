from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]


def get_credentials(credentials_file: str, token_file: str) -> Credentials:
    creds = None

    refresh_token = os.getenv("GOOGLE_REFRESH_TOKEN")
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    if refresh_token and client_id and client_secret:
        creds = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
            scopes=SCOPES,
        )
    elif Path(token_file).exists():
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
            creds = flow.run_local_server(port=0)

        Path(token_file).parent.mkdir(parents=True, exist_ok=True)
        Path(token_file).write_text(creds.to_json(), encoding="utf-8")

    return creds


def find_old_promotions(service, months: int) -> list[str]:
    # Gmail's search syntax supports old-than-day queries. 90 days approximates
    # three months and is recalculated for every run from the current date.
    query = f"category:promotions older_than:{months * 30}d"
    message_ids: list[str] = []
    request = service.users().messages().list(userId="me", q=query)

    while request is not None:
        response = request.execute()
        message_ids.extend(item["id"] for item in response.get("messages", []))
        request = service.users().messages().list_next(request, response)

    return message_ids


def main() -> int:
    parser = argparse.ArgumentParser(description="Move old Gmail promotional messages to Trash.")
    parser.add_argument("--delete", action="store_true", help="Trash matching messages. Without this flag, preview only.")
    parser.add_argument("--months", type=int, default=3, help="Delete promotions older than this many months (default: 3).")
    parser.add_argument("--credentials", default="credentials.json", help="OAuth desktop credentials file.")
    parser.add_argument("--token", default="token.json", help="Authorized-user token file.")
    args = parser.parse_args()

    if args.months < 1:
        parser.error("--months must be at least 1")

    creds = get_credentials(args.credentials, args.token)
    service = build("gmail", "v1", credentials=creds, cache_discovery=False)
    ids = find_old_promotions(service, args.months)

    print(f"Run time: {datetime.now().isoformat(timespec='seconds')}")
    print(f"Found {len(ids)} promotional message(s) older than {args.months} month(s).")

    if not args.delete:
        print("Preview mode: no messages changed. Re-run with --delete to move them to Trash.")
        return 0

    for message_id in ids:
        service.users().messages().trash(userId="me", id=message_id).execute()

    print(f"Moved {len(ids)} promotional message(s) to Trash.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("Cancelled.", file=sys.stderr)
        raise SystemExit(130)
