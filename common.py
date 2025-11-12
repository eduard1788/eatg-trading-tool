
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

# Columns to convert to numeric
convert_numeric = {
    "Summary": ['Net Liquidation', 'Cash Balance', 'Realized PnL', 'Unrealized PnL (manual)', 'Market Value (Equity)', 'Market Value (Cash)'],
    "Stock Activity": ['orderID', 'OrderQty', 'OrderPrice', 'FilledQty', 'AvgFillPrice', 'FillAmount', 'TotalCommission', 'cumulative_position', 'trade_number'],
    "Active Orders": ['Order ID', 'Quantity', 'Lmt Price', 'Aux Price', 'Total Liq Amount', 'parentId', 'ocaGroup', 'relation_key', 'relation_side'],
    "Positions": ['Average Cost', 'Current Price', 'Market Value', 'Unrealized PnL', 'Realized PnL', 'Cost', 'Total Liq Amount', 'Capital Exposure']
}

# API access key
API_KEY = "lU5mQZlgCeQr20UvOvPNHNASZbjGfbhz"
