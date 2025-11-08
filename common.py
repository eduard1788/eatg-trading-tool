
# User accounts
accounts = {"eduardo":{"acc": ["U3297495", "U4572134"], "conn_port": [4001], "client_id": [1]}, "daniela":{"acc": ["U7514316"], "conn_port": [4001], "client_id": [1]}, "eduardo_paper":{"acc": ["DU1717711"], "conn_port": [4001], "client_id": [1]}, "daniela_paper":{"acc": ["DU2883726"], "conn_port": [4001], "client_id": [1]}}

# File types
f_type = {"excel": [("Excel files", "*.xlsx *.xls")], "xml": [("XML files", "*.xml")], "all": [("All files", "*.*")]}

# Sheets for report update
sheet_list = ['Summary', 'Stock Activity', 'Active Orders', 'Positions']

# Columns to delete upon update
columns_to_delete = {
    "Summary": [],
    "Stock Activity": ["cumulative_position", "trade_number"],
    "Active Orders": [],
    "Positions": []
}

# API access key
API_KEY = "lU5mQZlgCeQr20UvOvPNHNASZbjGfbhz"
