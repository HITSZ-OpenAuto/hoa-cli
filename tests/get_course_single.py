from pathlib import Path

from hoa_majors.config import DEFAULT_DATA_DIR
from hoa_majors.core.fetcher import fetch_courses_by_fah
from hoa_majors.core.parser import normalize_course
from hoa_majors.core.writer import write_toml


def main():
    root = DEFAULT_DATA_DIR / "SCHOOL_MAJORS"
    fah = "42C248B0D4A01B24E0630B18F80A7AD4"

    print(f"Fetching courses for FAH: {fah}")
    raw_courses = fetch_courses_by_fah(fah)
    normalized = [normalize_course(item) for item in raw_courses]
    data = {"courses": normalized}

    output_path = root / f"test_{fah}.toml"
    write_toml(output_path, data)
    print(f"✔ Saved to {output_path}")


if __name__ == "__main__":
    main()
