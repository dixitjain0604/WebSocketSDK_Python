from typing import Optional

def format_hh_mm(minutes : int) -> str:
    return f"{minutes // 60 :02d}:{minutes % 60 :02d}"

def parse_hh_mm(text : str) -> Optional[int]:
    try:
        h, m = text.split(':')
        return int(h) * 60 + int(m)
    except ValueError:
        return None
