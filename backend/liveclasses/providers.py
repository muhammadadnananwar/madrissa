"""
Meeting providers for live classes.

* jitsi        – free & open source. No account needed for meet.jit.si; for
                 production self-host Jitsi on a small VPS (unlimited, no per-user cost).
* google_meet  – free with any Google account (60 min limit for 3+ people on
                 personal accounts; unlimited with Google Workspace for Education
                 Fundamentals which is free for eligible non-profit institutions).
                 Meetings are created through the Google Calendar API.
* zoom         – Server-to-Server OAuth app (free plan limits meetings to 40 minutes).
"""
import base64
import json
import re
import secrets
import urllib.parse
import urllib.request
from datetime import timedelta
from datetime import timezone as dt_timezone

from django.conf import settings


class ProviderError(Exception):
    pass


def _http(url, data=None, headers=None, method=None, form=False):
    body = None
    headers = dict(headers or {})
    if data is not None:
        if form:
            body = urllib.parse.urlencode(data).encode()
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        else:
            body = json.dumps(data).encode()
            headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=headers, method=method or ("POST" if body else "GET"))
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raise ProviderError(f"{e.code}: {e.read()[:200].decode(errors='ignore')}")
    except urllib.error.URLError as e:
        raise ProviderError(str(e.reason))


def _slug(text):
    return re.sub(r"[^A-Za-z0-9]+", "", text.title())[:40] or "Class"


def create_jitsi(lc):
    room = f"Madrasa{_slug(lc.title)}{secrets.token_hex(4)}"
    url = f"https://{settings.JITSI_DOMAIN}/{room}"
    return {"meeting_id": room, "join_url": url, "host_url": url, "passcode": ""}


def _google_token():
    if not (settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET and settings.GOOGLE_REFRESH_TOKEN):
        raise ProviderError("Google Meet is not configured (GOOGLE_CLIENT_ID / SECRET / REFRESH_TOKEN).")
    res = _http("https://oauth2.googleapis.com/token", {
        "client_id": settings.GOOGLE_CLIENT_ID, "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "refresh_token": settings.GOOGLE_REFRESH_TOKEN, "grant_type": "refresh_token"}, form=True)
    return res["access_token"]


def create_google_meet(lc):
    token = _google_token()
    start = lc.scheduled_start
    end = start + timedelta(minutes=lc.duration_minutes)
    cal = urllib.parse.quote(settings.GOOGLE_CALENDAR_ID)
    event = _http(
        f"https://www.googleapis.com/calendar/v3/calendars/{cal}/events?conferenceDataVersion=1",
        {"summary": lc.title, "description": lc.description,
         "start": {"dateTime": start.isoformat()}, "end": {"dateTime": end.isoformat()},
         "conferenceData": {"createRequest": {"requestId": secrets.token_hex(8),
                                              "conferenceSolutionKey": {"type": "hangoutsMeet"}}}},
        headers={"Authorization": f"Bearer {token}"})
    link = event.get("hangoutLink")
    if not link:
        raise ProviderError("Google did not return a Meet link.")
    return {"meeting_id": event.get("id", ""), "join_url": link, "host_url": link, "passcode": ""}


def delete_google_meet(lc):
    if not lc.meeting_id:
        return
    token = _google_token()
    cal = urllib.parse.quote(settings.GOOGLE_CALENDAR_ID)
    _http(f"https://www.googleapis.com/calendar/v3/calendars/{cal}/events/{lc.meeting_id}",
          headers={"Authorization": f"Bearer {token}"}, method="DELETE")


def _zoom_token():
    if not (settings.ZOOM_ACCOUNT_ID and settings.ZOOM_CLIENT_ID and settings.ZOOM_CLIENT_SECRET):
        raise ProviderError("Zoom is not configured (ZOOM_ACCOUNT_ID / CLIENT_ID / CLIENT_SECRET).")
    basic = base64.b64encode(f"{settings.ZOOM_CLIENT_ID}:{settings.ZOOM_CLIENT_SECRET}".encode()).decode()
    res = _http(f"https://zoom.us/oauth/token?grant_type=account_credentials&account_id={settings.ZOOM_ACCOUNT_ID}",
                {}, headers={"Authorization": f"Basic {basic}"}, form=True)
    return res["access_token"]


def create_zoom(lc):
    token = _zoom_token()
    m = _http("https://api.zoom.us/v2/users/me/meetings", {
        "topic": lc.title, "type": 2, "start_time": lc.scheduled_start.astimezone(dt_timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "duration": lc.duration_minutes, "timezone": settings.TIME_ZONE, "agenda": lc.description[:2000],
        "settings": {"join_before_host": False, "waiting_room": True, "mute_upon_entry": True, "auto_recording": "none"},
    }, headers={"Authorization": f"Bearer {token}"})
    return {"meeting_id": str(m.get("id", "")), "join_url": m.get("join_url", ""), "host_url": m.get("start_url", ""),
            "passcode": m.get("password", "")}


def delete_zoom(lc):
    if lc.meeting_id:
        _http(f"https://api.zoom.us/v2/meetings/{lc.meeting_id}", headers={"Authorization": f"Bearer {_zoom_token()}"},
              method="DELETE")


CREATORS = {"jitsi": create_jitsi, "google_meet": create_google_meet, "zoom": create_zoom}
DELETERS = {"google_meet": delete_google_meet, "zoom": delete_zoom}


def provision(lc):
    """Fill meeting fields on a LiveClass. Returns error string or ''."""
    if lc.provider == "custom":
        return "" if lc.join_url else "Provide a join URL for custom provider."
    try:
        data = CREATORS[lc.provider](lc)
    except ProviderError as e:
        return str(e)
    except Exception as e:  # network or unexpected payload
        return f"Provider error: {e}"
    for k, v in data.items():
        setattr(lc, k, v)
    return ""


def cancel(lc):
    fn = DELETERS.get(lc.provider)
    if fn:
        try:
            fn(lc)
        except Exception:
            pass


def status():
    return {
        "default": settings.LIVE_CLASS_DEFAULT_PROVIDER,
        "jitsi": {"configured": True, "domain": settings.JITSI_DOMAIN, "embed": settings.JITSI_EMBED},
        "google_meet": {"configured": bool(settings.GOOGLE_REFRESH_TOKEN and settings.GOOGLE_CLIENT_ID)},
        "zoom": {"configured": bool(settings.ZOOM_ACCOUNT_ID and settings.ZOOM_CLIENT_ID)},
    }
