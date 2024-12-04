import ctypes
import google_calendar_helper
import json


SHAHAF_HOURS = 14


def call_helper(*args) -> str:
    library = ctypes.cdll.LoadLibrary("./Shahaf.so")
    shahaf_main = library.mainC
    shahaf_main.restype = ctypes.c_void_p
    shahaf_main.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_int]
    return ctypes.string_at(shahaf_main(*args)).decode()


def get_timetable(url: str, class_code: int) -> str:
    encoded_url = url.encode()
    return call_helper(encoded_url, 0, class_code)


def get_classes(url: str) -> list[dict[str, str]]:
    encoded_url = url.encode()
    classes_json = call_helper(encoded_url, 1, 0)
    return json.loads(classes_json)


def insert_timetable_to_calendar(url: str, class_code: int) -> None:
    time_table_str = get_timetable(url, class_code)
    time_table_json: dict[str, dict] = json.loads(time_table_str)
    lesson_dict = dict(time_table_json["Lessons"])
    dates_list = list(time_table_json["Dates"].values())
    hours_dict = time_table_json["Hours"]
    for day_num in range(len(dates_list)):
        date_dict = dates_list[day_num]
        day_num += 1
        cur_day = date_dict["day"]
        cur_month = date_dict["month"]
        for lesson_num, lesson_list in lesson_dict[str(day_num)].items():
            if len(lesson_list) == 0:
                continue
            datetime_hour_start = hours_dict[lesson_num]["hourStart"]
            datetime_minute_start = hours_dict[lesson_num]["minuteStart"]
            datetime_hour_end = hours_dict[lesson_num]["hourEnd"]
            datetime_minute_end = hours_dict[lesson_num]["minuteEnd"]

            cur_lesson = lesson_list[0]
            # TEMP: Using first lesson found in lesson list TODO: Make it choosable
            lesson_name = cur_lesson["lessonName"]
            teacher = cur_lesson["teacher"]
            location = cur_lesson["location"]
            google_calendar_helper.insert_lesson(
                location,
                lesson_name,
                teacher,
                datetime_hour_start,
                datetime_minute_start,
                datetime_hour_end,
                datetime_minute_end,
                cur_day,
                cur_month,
                False,
            )
    # dates[day] = {day, month}
    # lessons[day][hournum] = {lessonName, teacher, location}
    # hour[hournum] = {hourStart, minuteStart, hourEnd, minuteEnd}
