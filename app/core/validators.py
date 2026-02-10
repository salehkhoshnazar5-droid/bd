import re
from typing import Optional


_PERSIAN_DIGITS = "۰۱۲۳۴۵۶۷۸۹"
_ARABIC_DIGITS = "٠١٢٣٤٥٦٧٨٩"
_DIGIT_TRANSLATION = str.maketrans(
    {**{ord(d): str(i) for i, d in enumerate(_PERSIAN_DIGITS)},
     **{ord(d): str(i) for i, d in enumerate(_ARABIC_DIGITS)}}
)


def normalize_digits(value: Optional[str]) -> Optional[str]:
    if value is None:
        return value
    return re.sub(r"\s+", "", value.strip().translate(_DIGIT_TRANSLATION))


def validate_student_number(value: Optional[str]) -> Optional[str]:
    if value is None:
        return value
    value = normalize_digits(value)
    if not re.fullmatch(r"\d{9}", value):
        raise ValueError("شماره دانشجویی باید ۹ رقم باشد")
    return value


def validate_phone_number(value: Optional[str]) -> Optional[str]:
    if value is None:
        return value
    value = normalize_digits(value)
    if not re.fullmatch(r"09\d{9}", value):
        raise ValueError("شماره تماس باید با ۰۹ شروع شده و ۱۱ رقم باشد")
    return value


def validate_national_code(value: Optional[str]) -> Optional[str]:
    if value is None:
        return value
    value = normalize_digits(value)
    if not re.fullmatch(r"\d{10}", value):
        raise ValueError("کد ملی باید ۱۰ رقم باشد")
    if len(set(value)) == 1:
        raise ValueError("کد ملی معتبر نیست")
    checksum = sum(int(value[i]) * (10 - i) for i in range(9)) % 11
    check_digit = int(value[9])
    if (checksum < 2 and check_digit != checksum) or (checksum >= 2 and check_digit + checksum != 11):
        raise ValueError("کد ملی معتبر نیست")
    return value