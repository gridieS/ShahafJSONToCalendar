import ctypes
import google_calendar_helper
import json
from os import path
import platform


SHAHAF_HOURS = 14
LIBRARY_DIRECTORY_NAME = "ShahafToJSONLibraries"
WIN_LIBRARY_NAME = "win.dll"
ARM_LIBRARY_NAME = "arm.so"
X86_LIBRARY_NAME = "x86.so"

WINDOWS_SYSTEM = "Windows"
X86_ARCH = "x86"
ARM_ARCH = "arm"


def call_helper(*args) -> str:
    if platform.system() == WINDOWS_SYSTEM:
        library_name = WIN_LIBRARY_NAME
    else:
        arch = platform.architecture()
        if X86_ARCH in platform.machine().lower():
            library_name = X86_LIBRARY_NAME
        elif ARM_ARCH in platform.machine().lower():
            library_name = ARM_LIBRARY_NAME
        else:
            raise Exception(f"Unknown arch {arch}.")

    library = ctypes.cdll.LoadLibrary(path.join(LIBRARY_DIRECTORY_NAME, library_name))
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
        if lesson_dict.get(str(day_num)) == None:
            continue
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
            )
    # dates[day] = {day, month}
    # lessons[day][hournum] = {lessonName, teacher, location}
    # hour[hournum] = {hourStart, minuteStart, hourEnd, minuteEnd}
