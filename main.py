from ib_insync import util
import customtkinter
from ib_utilities import IBKRApiConn
from account_info import GetInfo
from finn_info import FinnInfo
from common import f_type, sheet_list, columns_to_delete


#######################################
###### Search symbol information ######
#######################################
#client_info = GetInfo()
#finn = FinnInfo(client_info)
#finn.fetch_stock_info()


###############################
#### Connect to IB Gateway ####
###############################

user = customtkinter.CTkInputDialog(text="Please input your name in lowercase:", title="Who are you?")
user = user.get_input()
client = IBKRApiConn(user)
print(f"This is your user: {client.user}")
print(f"These are your associated accounts: {client.account}")
print(f"Connection port: {client.conn_port}")
print(f"Client ID: {client.client_id}")

client.ib_connect()

# input(f"{user}, Now let's disconnect. input anything.")

# client.ib_disconnect()


############################################################
#### Load file to update and get dictionary with sheets ####
############################################################

client_info = GetInfo()
sheets = client_info.define_sheets_to_update_from_local_path (client_info.request_path_to_user("Select the file path", f_type["excel"]), sheet_list)
print(f"Files to update:")
for key, values in sheets.items():
    print(key)

# Clean calculated fields
cleaned_sheets = client_info.drop_calculated_fields(sheets, columns_to_delete)


###############################
#### Get new data from API ####
###############################

# 1 Get Summary sheet
input(f"{user}, Searching for summary... Input anything to continue...")
summary = client_info.get_summary_df(client.ib, client.account)

# 2 Get Trades sheet
input(f"{user}, Searching for trading history... Input anything to continue...")
log_path = client_info.request_path_to_user("Select trading log", f_type["xml"])
print(f"Path value: {log_path}")
trades, records = client_info.get_trading_log(log_path)
print(f"Total records to processed: {records}")

# Adjust trades to update and new trades
columns_to_numeric = ['orderID', 'OrderQty', 'OrderPrice', 'FilledQty', 'AvgFillPrice', 'FillAmount', 'TotalCommission']
historic_trades = client_info.convert_columns_to_numeric(cleaned_sheets['Stock Activity'], columns_to_numeric)
if records > 0:
    trades = client_info.convert_columns_to_numeric(trades, columns_to_numeric)
final_trades = client_info.concatenate_dataframes(historic_trades, trades)
final_trades = client_info.add_trading_number(final_trades)

# 3 Get Active Orders sheet
input(f"{user} Searching for active orders. Input anything to continue...")
orders = client_info.fetch_active_orders(client.ib, client.account)

# 4 Get Positions sheet
input(f"{user} Searching for positions. Input anything to continue...")
positions = client_info.get_positions(client.ib, client.account)

# To DO
# This dict could be deleted
api_information = {
    'Summary': summary,
    'Stock Activity': final_trades,
    'Active Orders': orders,
    'Positions': positions
}

# 5 Update the dataframes orders, positions and summary
input(f"{user} Updating summary, orders and  positions dataframes. Input anything to continue...")
orders, positions = client_info.calculate_risk_exposure(api_information)
orders = client_info.mark_parent_child_orders(orders)
summary = client_info.calculate_unrealized_summary(summary, positions)

api_information = {
    'Summary': summary,
    'Stock Activity': final_trades,
    'Active Orders': orders,
    'Positions': positions
}

# 6 Print the dictionaries

# New data
for sheet, df in api_information.items():
    print(f"Saved file: {sheet} in C:/0.Repositories/")
    df.to_excel('C:/0.Repositories/' + sheet + '.xlsx' , index = False)

# Data to update
for sheet, df in cleaned_sheets.items():
    print(f"Saved file: To be updated {sheet} in C:/0.Repositories/")
    df.to_excel('C:/0.Repositories/' + 'To be updated ' + sheet + '.xlsx' , index = False)





