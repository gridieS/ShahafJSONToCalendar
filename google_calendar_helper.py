from googleapiclient.discovery import build, Resource
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pytz
import datetime
import os.path
import pickle

SCOPES = ["https://www.googleapis.com/auth/calendar"]

SCHOOL_CALENDAR_NAME = "Shahaf School"

LESSON_UPDATED_STRING_CONCAT = "(Updated)"

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


# Create SCHOOL_CALENDAR_NAME calendar if it doesnt exist
def create_school_calendar():
    calendar = {
        "summary": SCHOOL_CALENDAR_NAME,
        "timeZone": primary_calendar_timezone,
    }
    return service.calendars().insert(body=calendar).execute()


if school_calendar is None:
    school_calendar = create_school_calendar()


def remove_event(event_id: str) -> None:
    service.events().delete(
        calendarId=school_calendar["id"], eventId=event_id
    ).execute()


def is_lesson_updated(lesson_name: str) -> bool:
    if LESSON_UPDATED_STRING_CONCAT in lesson_name:
        return True
    return False


def get_day_lessons(
    day: int, month: int
) -> list[dict]:  # "str" being the event summary
    day_start = datetime.datetime.now(pytz.timezone(primary_calendar_timezone)).replace(
        microsecond=0,
        second=0,
        minute=0,
        hour=0,
        day=day,
        month=month,
    )
    day_end = day_start + datetime.timedelta(days=1)
    result = (
        service.events()
        .list(
            calendarId=school_calendar["id"],
            timeMin=day_start.isoformat(),
            timeMax=day_end.isoformat(),
            timeZone=primary_calendar_timezone,
        )
        .execute()
    )["items"]

    return result


# Returns lesson dictionary if true
def lesson_exists_at(start_datetime: datetime.datetime) -> dict | bool:
    for event in get_day_lessons(start_datetime.day, start_datetime.month):
        if event["start"]["dateTime"] == start_datetime.isoformat():
            return event

    return False


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
    lesson_update: bool = False,
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

    if lesson_dict := lesson_exists_at(start_datetime):
        if lesson_dict["summary"] == lesson_name:  # Same lesson
            return

        if lesson_update:
            remove_event(lesson_dict["id"])
        else:
            if not is_lesson_updated(lesson_dict["summary"]):
                remove_event(lesson_dict["id"])
            else:
                return

    end_datetime = datetime.datetime(
        int(now.year),
        int(month),
        int(day),
        int(end_time_hour),
        int(end_time_minutes),
        0,
    )
    day_code = (start_datetime.strftime("%A")[:2]).upper()

    if not lesson_update:
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
    else:
        event = {
            "summary": f"{lesson_name} {LESSON_UPDATED_STRING_CONCAT}",
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
        }

    service.events().insert(calendarId=school_calendar["id"], body=event).execute()
