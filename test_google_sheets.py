import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

credentials = Credentials.from_service_account_file(
    "credentials/google-service-account.json",
    scopes=SCOPES,
)

client = gspread.authorize(credentials)

SPREADSHEET_ID = "1t_dik82cVKEVs3Mx9cgmW5Env8wMk_PkwLtkwVnvuzw"

spreadsheet = client.open_by_key(SPREADSHEET_ID)

print("Connected successfully!")
print("Spreadsheet:", spreadsheet.title)

print("\nSheets:")

for worksheet in spreadsheet.worksheets():
    print("-", worksheet.title)