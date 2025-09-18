from pathlib import Path
from typing import Iterable

import pandas as pd


def write_comparison_xlsx(rows: Iterable[dict], out_path: str) -> str:
    df = pd.DataFrame(rows)
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(p, index=False)
    return str(p)
