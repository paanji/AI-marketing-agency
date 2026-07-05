"""
seo_agent.py

Pulls Search Console performance data for allaidunia.com and identifies:
  1. Quick-win queries — ranking positions 5-15 (page 1 bottom / page 2),
     close enough to page 1 that a small push (better title, more internal
     links, a supporting blog post) could meaningfully help.
  2. Declining pages — comparing the last 28 days to the prior 28 days,
     flags pages that lost significant clicks.

Writes findings to seo_report.md — this becomes input for a future
Content Agent, and is also just useful for you to read directly.

Auth: uses a Google Cloud service account (credentials via the
GSC_SERVICE_ACCOUNT_JSON GitHub secret, written to a temp file by the
workflow before this script runs).
"""
import json
import os
from datetime import date, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build

SITE_URL = "https://www.allaidunia.com/"   # URL-prefix property — must match exactly, trailing slash included
CREDENTIALS_PATH = os.environ.get("GSC_CREDENTIALS_PATH", "gsc_credentials.json")
REPORT_PATH = "agents/seo/seo_report.md"

QUICK_WIN_MIN_POSITION = 5
QUICK_WIN_MAX_POSITION = 15
QUICK_WIN_MIN_IMPRESSIONS = 20   # ignore near-zero-traffic queries, too noisy to act on
DECLINE_THRESHOLD_PCT = 25        # flag pages that lost at least this % of clicks

SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]


def get_service():
    creds = service_account.Credentials.from_service_account_file(
        CREDENTIALS_PATH, scopes=SCOPES
    )
    return build("searchconsole", "v1", credentials=creds)


def query_search_analytics(service, start_date, end_date, dimensions, row_limit=1000):
    body = {
        "startDate": start_date.isoformat(),
        "endDate": end_date.isoformat(),
        "dimensions": dimensions,
        "rowLimit": row_limit,
    }
    response = service.searchanalytics().query(siteUrl=SITE_URL, body=body).execute()
    return response.get("rows", [])


def find_quick_wins(query_rows):
    wins = []
    for row in query_rows:
        query = row["keys"][0]
        position = row["position"]
        impressions = row["impressions"]
        clicks = row["clicks"]
        if (QUICK_WIN_MIN_POSITION <= position <= QUICK_WIN_MAX_POSITION
                and impressions >= QUICK_WIN_MIN_IMPRESSIONS):
            wins.append({
                "query": query,
                "position": round(position, 1),
                "impressions": impressions,
                "clicks": clicks,
                "ctr": round(row["ctr"] * 100, 1),
            })
    wins.sort(key=lambda w: w["impressions"], reverse=True)
    return wins


def find_declining_pages(recent_rows, prior_rows):
    recent_by_page = {r["keys"][0]: r["clicks"] for r in recent_rows}
    prior_by_page = {r["keys"][0]: r["clicks"] for r in prior_rows}

    declines = []
    for page, prior_clicks in prior_by_page.items():
        if prior_clicks < 5:
            continue  # too small a base to call it a meaningful decline
        recent_clicks = recent_by_page.get(page, 0)
        drop_pct = ((prior_clicks - recent_clicks) / prior_clicks) * 100
        if drop_pct >= DECLINE_THRESHOLD_PCT:
            declines.append({
                "page": page,
                "prior_clicks": prior_clicks,
                "recent_clicks": recent_clicks,
                "drop_pct": round(drop_pct, 1),
            })
    declines.sort(key=lambda d: d["drop_pct"], reverse=True)
    return declines


def main():
    service = get_service()

    today = date.today()
    # GSC data has a ~2-3 day lag, so end the window a few days back
    end_date = today - timedelta(days=3)
    recent_start = end_date - timedelta(days=28)
    prior_start = recent_start - timedelta(days=28)
    prior_end = recent_start - timedelta(days=1)

    print(f"Querying Search Console for {SITE_URL}")
    print(f"Recent window: {recent_start} to {end_date}")
    print(f"Prior window:  {prior_start} to {prior_end}")

    query_rows = query_search_analytics(service, recent_start, end_date, ["query"])
    recent_page_rows = query_search_analytics(service, recent_start, end_date, ["page"])
    prior_page_rows = query_search_analytics(service, prior_start, prior_end, ["page"])

    quick_wins = find_quick_wins(query_rows)
    declines = find_declining_pages(recent_page_rows, prior_page_rows)

    lines = [
        f"# SEO Report — {today.isoformat()}",
        f"",
        f"Data window: {recent_start} to {end_date} (vs. prior {prior_start} to {prior_end})",
        f"",
        f"## Quick-Win Opportunities",
        f"Queries ranking positions {QUICK_WIN_MIN_POSITION}-{QUICK_WIN_MAX_POSITION} — close to page 1, "
        f"worth a small push (better title/meta, more internal links, or a supporting blog post).",
        f"",
    ]

    if quick_wins:
        lines.append("| Query | Position | Impressions | Clicks | CTR |")
        lines.append("|---|---|---|---|---|")
        for w in quick_wins[:25]:
            lines.append(f"| {w['query']} | {w['position']} | {w['impressions']} | {w['clicks']} | {w['ctr']}% |")
    else:
        lines.append("_No quick-win queries found in this window._")

    lines += ["", "## Declining Pages", f"Pages that lost {DECLINE_THRESHOLD_PCT}%+ of clicks vs. the prior 28 days.", ""]

    if declines:
        lines.append("| Page | Prior Clicks | Recent Clicks | Drop |")
        lines.append("|---|---|---|---|")
        for d in declines[:25]:
            lines.append(f"| {d['page']} | {d['prior_clicks']} | {d['recent_clicks']} | -{d['drop_pct']}% |")
    else:
        lines.append("_No significant declines found._")

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\nFound {len(quick_wins)} quick-win queries, {len(declines)} declining pages")
    print(f"Report written to {REPORT_PATH}")


if __name__ == "__main__":
    main()
