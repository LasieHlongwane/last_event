from pathlib import Path
import time

import gspread
from google.oauth2.service_account import Credentials


# ============================================================
# STREAMLIT
# ============================================================

try:
    import streamlit as st
except ImportError:
    st = None


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

CREDENTIALS_FILE = (
    BASE_DIR
    / "credentials"
    / "google-service-account.json"
)

SPREADSHEET_ID = (
    "1t_dik82cVKEVs3Mx9cgmW5Env8wMk_PkwLtkwVnvuzw"
)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


# ============================================================
# GOOGLE CREDENTIALS
# ============================================================

def get_credentials():
    """
    Get Google service-account credentials.

    Priority:

    1. Streamlit Cloud secrets
    2. Local JSON credentials file

    This allows the same application to work both locally
    and on Streamlit Cloud.
    """

    # --------------------------------------------------------
    # STREAMLIT CLOUD
    # --------------------------------------------------------

    if st is not None:

        try:

            if "gcp_service_account" in st.secrets:

                service_account_info = dict(
                    st.secrets["gcp_service_account"]
                )

                return Credentials.from_service_account_info(
                    service_account_info,
                    scopes=SCOPES,
                )

        except Exception as exc:

            print(
                "Unable to load Google credentials "
                f"from Streamlit secrets: {exc}"
            )

    # --------------------------------------------------------
    # LOCAL DEVELOPMENT
    # --------------------------------------------------------

    if CREDENTIALS_FILE.exists():

        return Credentials.from_service_account_file(
            str(CREDENTIALS_FILE),
            scopes=SCOPES,
        )

    # --------------------------------------------------------
    # NOTHING FOUND
    # --------------------------------------------------------

    raise FileNotFoundError(
        "\nGoogle service-account credentials were not found.\n\n"
        "For Streamlit Cloud:\n"
        "Add your Google service-account credentials to:\n"
        "Settings → Secrets\n\n"
        "For local development:\n"
        f"Place the JSON file here:\n{CREDENTIALS_FILE}\n"
    )


# ============================================================
# GOOGLE SHEETS CLIENT
# ============================================================

def get_client():
    """
    Create and return an authenticated gspread client.
    """

    credentials = get_credentials()

    return gspread.authorize(credentials)


# ============================================================
# SPREADSHEET CONNECTION
# ============================================================

def get_spreadsheet():
    """
    Connect to Google Sheets with retry support.
    """

    credentials = get_credentials()

    last_error = None

    for attempt in range(3):

        try:

            client = gspread.authorize(
                credentials
            )

            spreadsheet = client.open_by_key(
                SPREADSHEET_ID
            )

            return spreadsheet

        except Exception as error:

            last_error = error

            print(
                "Google Sheets connection attempt "
                f"{attempt + 1}/3 failed: {error}"
            )

            if attempt < 2:
                time.sleep(3)

    raise last_error


# ============================================================
# WORKSHEET ACCESS
# ============================================================

def get_sheet(sheet_name):
    """
    Return a worksheet by name.

    Example:

        get_sheet("Users")
    """

    spreadsheet = get_spreadsheet()

    try:

        return spreadsheet.worksheet(
            sheet_name
        )

    except gspread.WorksheetNotFound:

        raise ValueError(
            f"Worksheet '{sheet_name}' was not found."
        )


def get_worksheet(sheet_name):
    """
    Backwards-compatible alias for get_sheet().
    """

    return get_sheet(sheet_name)


# ============================================================
# READ DATA
# ============================================================

def get_all_records(sheet_name):
    """
    Return all records from a Google Sheet.

    Each record also contains its actual Google Sheets
    row number under:

        Row number
    """

    worksheet = get_sheet(sheet_name)

    records = worksheet.get_all_records()

    # Row 1 contains headers.
    # Therefore the first data record is row 2.
    for index, record in enumerate(
        records,
        start=2,
    ):

        record["Row number"] = index

    return records


def get_headers(sheet_name):
    """
    Return the first row of a worksheet.
    """

    worksheet = get_sheet(sheet_name)

    return worksheet.row_values(1)


# ============================================================
# APPEND RECORD
# ============================================================

def append_record(sheet_name, record):
    """
    Append one dictionary as a new row.

    Dictionary keys should correspond to the worksheet
    headers.
    """

    worksheet = get_sheet(sheet_name)

    headers = worksheet.row_values(1)

    if not headers:

        raise ValueError(
            f"Worksheet '{sheet_name}' has no headers."
        )

    row = [
        record.get(header, "")
        for header in headers
    ]

    worksheet.append_row(
        row,
        value_input_option="USER_ENTERED",
    )


# ============================================================
# UPDATE RECORD
# ============================================================

def update_record(
    sheet_name,
    row_number,
    updates,
):
    """
    Update specific columns in an existing row.

    Example:

        update_record(
            "Notification",
            87,
            {
                "Status": "Sent",
                "Sent At": "2026-08-11T10:00:00+00:00",
            }
        )
    """

    worksheet = get_sheet(sheet_name)

    headers = worksheet.row_values(1)

    for column_name, value in updates.items():

        if column_name not in headers:

            raise ValueError(
                f"Column '{column_name}' "
                f"does not exist in '{sheet_name}'."
            )

        column_number = (
            headers.index(column_name) + 1
        )

        worksheet.update_cell(
            row_number,
            column_number,
            value,
        )

    return True


# ============================================================
# UPDATE SINGLE CELL
# ============================================================

def update_cell(
    sheet_name,
    row_number,
    column_number,
    value,
):
    """
    Update one cell.

    row_number and column_number are 1-based.
    """

    worksheet = get_sheet(sheet_name)

    worksheet.update_cell(
        row_number,
        column_number,
        value,
    )


# ============================================================
# SEARCH RECORDS
# ============================================================

def find_records(
    sheet_name,
    column_name,
    value,
):
    """
    Find all records where a specific column exactly
    matches a value.
    """

    records = get_all_records(
        sheet_name
    )

    matches = []

    target_value = str(
        value
    ).strip()

    for record in records:

        record_value = str(
            record.get(
                column_name,
                "",
            )
        ).strip()

        if record_value == target_value:

            matches.append(record)

    return matches


# ============================================================
# RECORD EXISTS
# ============================================================

def record_exists(
    sheet_name,
    column_name,
    value,
):
    """
    Return True if at least one matching record exists.
    """

    matches = find_records(
        sheet_name,
        column_name,
        value,
    )

    return len(matches) > 0


# ============================================================
# CONNECTION TEST
# ============================================================

if __name__ == "__main__":

    spreadsheet = get_spreadsheet()

    print(
        "Connected successfully!"
    )

    print(
        f"Spreadsheet: {spreadsheet.title}"
    )

    print("\nSheets:")

    for worksheet in spreadsheet.worksheets():

        print(
            f"- {worksheet.title}"
        )