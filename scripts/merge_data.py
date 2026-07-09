"""prepare the raw au fact book export into a single flat table.

reads the multi-sheet enrollment workbook, unpivots the year columns into
rows, and joins the per-major counts against the department totals.
"""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW_FILE = ROOT / "data" / "au-enrollment-2015-2025.xlsx"
OUTPUT_FILE = ROOT / "data" / "au-enrollment-merged.xlsx"


def merge() -> None:
    # load students-by-major sheet with correct header row
    df_majors = pd.read_excel(RAW_FILE, sheet_name="Students by major", header=3)
    df_majors.rename(
        columns={
            "Major College": "college",
            "Major department": "department_name",
            "Major": "major_name",
        },
        inplace=True,
    )

    # unpivot year columns into rows
    id_vars = ["college", "department_name", "major_name"]
    year_cols = [c for c in df_majors.columns if isinstance(c, str) and c.startswith("20")]
    majors = df_majors.melt(
        id_vars=id_vars,
        value_vars=year_cols,
        var_name="academic_year",
        value_name="student_count",
    )

    # load departments sheet and unpivot the same way
    df_depts = pd.read_excel(RAW_FILE, sheet_name="Departments", header=2)
    df_depts.rename(columns={"Row Labels": "department_name"}, inplace=True)
    dept_year_cols = [c for c in df_depts.columns if isinstance(c, str) and c.startswith("20")]
    depts = df_depts.melt(
        id_vars=["department_name"],
        value_vars=dept_year_cols,
        var_name="academic_year",
        value_name="department_total_students",
    )

    # join per-major counts against department totals
    unified = pd.merge(majors, depts, on=["department_name", "academic_year"], how="left")

    unified.to_excel(OUTPUT_FILE, index=False)
    print(f"success: merged data saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    merge()
