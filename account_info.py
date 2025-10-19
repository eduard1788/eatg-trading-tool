from tkinter import Tk, filedialog
from ib_insync import util
import pandas as pd
from common import f_type, sheet_list
from datetime import datetime


class GetInfo:
    """
    This class has been created for performing the following tasks:
    - Retrieve the summary trading page for IBKR accounts: This is achieved by leveraging functions: get_summary_df and get_summary_info (internal).
        input arguments --> An ib connection instance; a list containing all associated accounts.
        output --> the DataFrame showing the summary trading information per each account.
    -
    """
    def __init__(self):
        pass

    def request_path_to_user (self, message, file_type):
        root = Tk()
        root.withdraw()
        root.call('wm', 'attributes', '.', '-topmost', True)
        file_path = filedialog.askopenfilename(title=message,
                                                filetypes=file_type)
        return file_path

    def define_sheets_to_update_from_local_path (self, path, sheet_list):
        try:
            load_sheets = pd.read_excel(path, sheet_name=sheet_list, dtype=str)
            sheets_file_update = {}
            for sheet in sheet_list:
                df_sheet = load_sheets[sheet]
                sheets_file_update[sheet] = df_sheet
            return sheets_file_update
        except Exception as error:
            print(f"Exception occurred while loading sheets to update: {error}")
            raise

    def get_summary_df(self, ib_connection, account_list):
        # Allow delayed market data
        ib_connection.reqMarketDataType(3)

        # Fetch all account(s) value(s)
        account_values = util.df(ib_connection.accountValues())

        #  Prepare list to hold per-account results
        all_account_data = []

        # Calculate Summary per account number
        for account in account_list:
            account_data = {}
            account_data ={
                'Date': datetime.now().strftime('%Y-%m-%d'),
                'Account': account,
                'Net Liquidation': self._get_summary_info('NetLiquidation', account_values, account),
                'Cash Balance': self._get_summary_info('TotalCashValue', account_values, account),
                'Realized PnL': self._get_summary_info('RealizedPnL', account_values, account),
                'Unrealized PnL (manual)': '',
                'Market Value (Equity)': self._get_summary_info('EquityWithLoanValue', account_values, account),
                'Market Value (Cash)': self._get_summary_info('TotalCashValue', account_values, account)
            }

            all_account_data.append(account_data)

        # Final concatenated DataFrame
        summary_df = pd.DataFrame(all_account_data)
        return summary_df

    def _get_summary_info(self, tag, account_values, account_id):
        row = account_values.loc[(account_values['tag'] == tag) & (account_values['account'] == account_id)]
        return row['value'].values[0] if not row.empty else None

    def get_trading_log(self):
        pass



#client = GetInfo()
# TESTING request_path_to_user
# TESTING define_sheets_to_update

#updates = client.define_sheets_to_update_from_local_path(client.request_path_to_user("hello", f_type["excel"]), sheet_list)

#for key, value in updates.items():
#    value.to_excel('C:/0.Repositories/' + key + '.xlsx' , index = False)

# print(path)


