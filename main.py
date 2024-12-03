import datetime
import os
import ctypes

# import google_calendar_helper


def call_helper(*args) -> str:
    library = ctypes.cdll.LoadLibrary("./Shahaf.so")
    shahaf_main = library.mainC
    shahaf_main.restype = ctypes.c_void_p
    shahaf_main.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_int]
    return ctypes.string_at(shahaf_main(*args)).decode()


def get_timetable(url: str, class_code: int) -> str:
    encoded_url = url.encode()
    return call_helper(encoded_url, 0, class_code)


def get_classes(url: str) -> str:
    encoded_url = url.encode()
    return call_helper(encoded_url, 1, 1)


def main():
    print(get_timetable("https://ruppin.iscool.co.il", 126))


if __name__ == "__main__":
    main()
