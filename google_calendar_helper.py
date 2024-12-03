from googleapiclient.discovery import build, Resource
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import datetime
import os.path
import pickle

SCOPES = ["https://www.googleapis.com/auth/calendar"]

SCHOOL_CALENDAR_NAME = "School"


# OAuth validation
creds = None

if os.path.exists("token.pickle"):
    with open("token.pickle", "rb") as token:
        creds = pickle.load(token)

if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
        creds = flow.run_local_server(port=0)

    with open("token.pickle", "wb") as token:
        pickle.dump(creds, token)

service = build("calendar", "v3", credentials=creds)

calendar_list = service.calendarList().list().execute().get("items", [])

school_calendar = None
for calendar in calendar_list:
    if calendar["summary"] == SCHOOL_CALENDAR_NAME:
        school_calendar = calendar

primary_calendar = service.calendars().get(calendarId="primary").execute()
primary_calendar_timezone = primary_calendar["timeZone"]

# Create 'School' calendar if it doesnt exist
if school_calendar is None:
    calendar = {
        "summary": SCHOOL_CALENDAR_NAME,
        "timeZone": primary_calendar_timezone,
    }
    school_calendar = service.calendars().insert(body=calendar).execute()


def insert_lesson(
    location: str,
    lesson_name: str,
    teacher: str,
    start_time_hour: str,
    start_time_minutes: str,
    end_time_hour: str,
    end_time_minutes: str,
    day: str,
    month: str,
):
    now = datetime.datetime.now()
    start_datetime = datetime.datetime(
        int(now.year),
        int(month),
        int(day),
        int(start_time_hour),
        int(start_time_minutes),
        0,
    )
    end_datetime = datetime.datetime(
        int(now.year),
        int(month),
        int(day),
        int(end_time_hour),
        int(end_time_minutes),
        0,
    )
    day_code = (start_datetime.strftime("%A")[:2]).upper()

    event = {
        "summary": lesson_name,
        "location": location,
        "description": f"Teacher: {teacher}",
        "start": {
            "dateTime": start_datetime.isoformat(),
            "timeZone": primary_calendar_timezone,
        },
        "end": {
            "dateTime": end_datetime.isoformat(),
            "timeZone": primary_calendar_timezone,
        },
        "recurrence": [
            f"RRULE:FREQ=WEEKLY;BYDAY={day_code}"
        ],  # Get the first two capitalized letters of the day
    }
    created_event = (
        service.events().insert(calendarId=school_calendar["id"], body=event).execute()
    )
    print(f"Created event: {created_event['id']}")
