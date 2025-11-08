from tkinter import Tk, filedialog
from ib_insync import util
import pandas as pd
from common import f_type, sheet_list
from datetime import datetime
import xml.etree.ElementTree as ET
from typing import List, Optional
import numpy as np


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

    def convert_columns_to_numeric(self, df: pd.DataFrame, cols: List[str], inplace: bool = False, errors: str = "coerce", downcast: Optional[str] = None) -> pd.DataFrame:
        if not inplace:
            df = df.copy()
        for col in cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors=errors, downcast=downcast)
        return df

    def _eliminate_df_duplicates(self, df):
        df = df.drop_duplicates()
        return df

    def concatenate_and_prepare_df_to_print(self, df1, sheet_name, df2):
        concatenated_dfs = pd.concat([df1[sheet_name], df2], ignore_index=True)
        final_df = self._eliminate_df_duplicates(concatenated_dfs)
        return final_df

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

    def drop_calculated_fields(self, sheets_file_update, columns_to_delete):
        for sheet, dataframe in sheets_file_update.items():
            if len(columns_to_delete[sheet]) > 0:
                new_df = sheets_file_update[sheet].drop(columns=columns_to_delete[sheet])
                sheets_file_update[sheet] = new_df
        return sheets_file_update

    def calculate_unrealized_summary(self,summary, positions):
        positions_grouped = (positions.groupby(["Date", "Account"], as_index=False)["Unrealized PnL"].sum().rename(columns={"Unrealized PnL": "Unrealized PnL_sum"}))
        summary = summary.merge(positions_grouped, on=["Date", "Account"], how="left")
        summary["Unrealized PnL (manual)"] = summary["Unrealized PnL (manual)"].fillna(summary["Unrealized PnL_sum"])
        summary["Unrealized PnL (manual)"] = (summary["Unrealized PnL (manual)"].replace("", np.nan).fillna(summary["Unrealized PnL_sum"]))
        summary = summary.drop(columns=["Unrealized PnL_sum"])
        return summary

    def calculate_trade_number(self, trading_log):
        trading_log = self.convert_columns_to_numeric(trading_log, ['OrderQty'])
        trading_log_new = trading_log.sort_values(["symbol", "OrderDate", "orderID"]).reset_index(drop=True)

        # Initialize new columns
        trading_log_new["cumulative_position"] = 0
        trading_log_new["trade_number"] = 0

        trade_counters = {}  # symbol -> current trade number
        positions = {}  # symbol -> running cumulative position

        # Iterate over rows
        for i, row in trading_log_new.iterrows():
            sym = row["symbol"]
            qty = row["OrderQty"]

            # Initialize if first time we see this symbol
            if sym not in positions:
                positions[sym] = 0
                trade_counters[sym] = 1

            # Update position
            positions[sym] += qty
            trading_log_new.at[i, "cumulative_position"] = positions[sym]
            trading_log_new.at[i, "trade_number"] = trade_counters[sym]

            # If the position returns to 0, increment trade counter for next round
            if positions[sym] == 0:
                trade_counters[sym] += 1
        return trading_log_new

    def _get_summary_info(self, tag, account_values, account_id):
        row = account_values.loc[(account_values['tag'] == tag) & (account_values['account'] == account_id)]
        return row['value'].values[0] if not row.empty else None

    def get_dummy_trading_log(self):
        # Define the column names
        columns = [
            "AccountId",
            "symbol",
            "orderID",
            "OrderDate",
            "OrderQty",
            "OrderPrice",
            "FilledQty",
            "AvgFillPrice",
            "FillAmount",
            "TotalCommission",
            "cumulative_position",
            "trade_number"
        ]
        # Create an empty DataFrame
        return pd.DataFrame(columns=columns)

    def add_trading_number(self, trading_log):
        trading_log["OrderQty"] = pd.to_numeric(trading_log["OrderQty"], errors="coerce")
        trading_log = trading_log.sort_values(["symbol", "OrderDate", "orderID"]).reset_index(drop=True)

        # Initialize new columns
        trading_log["cumulative_position"] = 0
        trading_log["trade_number"] = 0

        trade_counters = {}  # symbol -> current trade number
        positions = {}  # symbol -> running cumulative position

        # Iterate over rows
        for i, row in trading_log.iterrows():
            sym = row["symbol"]
            qty = row["OrderQty"]

            # Initialize if first time we see this symbol
            if sym not in positions:
                positions[sym] = 0
                trade_counters[sym] = 1

            # Update position
            positions[sym] += qty
            trading_log.at[i, "cumulative_position"] = positions[sym]
            trading_log.at[i, "trade_number"] = trade_counters[sym]

            # If the position returns to 0, increment trade counter for next round
            if positions[sym] == 0:
                trade_counters[sym] += 1

        return trading_log

    # 4 Summary
    def get_summary_df(self, ib_connection, account_list):
        try:
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
        except Exception as error:
            print(f"Exception occurred while loading sheets to update: {error}")
            raise

    # 1 Stock Activity
    def get_trading_log(self, path):
        try:
            if path:
                file_xml = ET.parse(path)
                root = file_xml.getroot()

                # Extract records
                records = []
                for stmt in root.findall('.//FlexStatement'):
                    account_id = stmt.get('accountId')
                    confirms = stmt.find('TradeConfirms')
                    if confirms is None:
                        continue
                    for elem in confirms:
                        record = {'AccountId': account_id, 'RecordType': elem.tag}
                        # Copy every attribute on the element
                        record.update(elem.attrib)
                        records.append(record)

                # Build DataFrame
                df = pd.DataFrame(records)

                # Convert numeric fields
                numeric_cols = ['quantity', 'price', 'amount', 'netCash', 'commission']
                for col in numeric_cols:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')

                # Parse date fields
                df['dateTime'] = pd.to_datetime(df['dateTime'].str.replace(';', ' '), errors='coerce')
                df['orderTime'] = pd.to_datetime(df['orderTime'].str.replace(';', ' '), errors='coerce')

                # Split by record type
                df_summary = df[df.RecordType == 'SymbolSummary']  # one row per symbol summary
                df_orders = df[df.RecordType == 'Order']  # the parent orders
                df_fills = df[df.RecordType == 'TradeConfirm']  # the individual fills

                # Consolidate fills per orderID + symbol
                fills_agg = (
                    df_fills
                    .groupby(['orderID', 'symbol'])
                    .agg(
                        FilledQty=('quantity', 'sum'),
                        FillAmount=('amount', 'sum'),
                        TotalCommission=('commission', 'sum'),
                        # Also compute a weighted avg fill price:
                        AvgFillPrice=('price', lambda x: (x * df_fills.loc[x.index, 'quantity']).sum() / x.sum())
                    )
                    .reset_index()
                )

                # Merge orders and fills summary
                all_trades = (
                    df_orders
                    .merge(fills_agg, on=['orderID', 'symbol'], how='left')
                    .assign(
                        OrderQty=lambda d: d['quantity'],
                        OrderPrice=lambda d: d['price']
                    )
                    .rename(columns={
                        'tradeDate': 'OrderDate',
                        'trafficType': 'TransactionType'
                    })
                        # select/rename the columns you care about
                    [['AccountId', 'symbol', 'orderID', 'OrderDate', 'OrderQty', 'OrderPrice',
                      'FilledQty', 'AvgFillPrice', 'FillAmount', 'TotalCommission']]
                )
                all_trades['orderID'] = pd.to_numeric(all_trades['orderID'], errors='coerce')
                total_processed_records = len(all_trades)
                return all_trades, total_processed_records
            else:
                print(f"No path provided. No trading log will be processed.")
                # Call function for dummy df
                all_trades = self.get_dummy_trading_log()
                # Return dummy df and zero as records to update
                total_processed_records = 0
                return all_trades, total_processed_records
        except Exception as error:
            print(f"There has been a problem while trying to parse the provided path: {path}")
            print(f"Please validate the file: {error}")
            raise

    def _calculate_risk_exposure(self, orders, positions):
        orders['multi'] = np.where(
            orders['Action'] == "SELL",  # condition
            1,  # value if True
            -1  # value if False
        )
        orders['Total Liq Amount'] = ((orders['Quantity'] * orders['Aux Price'])) * orders[
            'multi']
        positions['Action'] = np.where(
            positions['Quantity'] > 0,  # condition
            'SELL',  # value if True
            'BUY'  # value if False
        )
        orders.drop(columns='multi', inplace=True)
        positions['Order Type'] = 'STP'
        positions['Cost'] = positions['Quantity'] * positions['Average Cost']
        keys_to_merge = ['Date', 'Account', 'Symbol', 'Action', 'Order Type']
        total_amount_stploss = orders.groupby(keys_to_merge)['Total Liq Amount'].sum().reset_index()
        concat_position = positions.merge(total_amount_stploss, on=keys_to_merge, how='left')
        concat_position['Capital Exposure'] = concat_position['Total Liq Amount'] - concat_position['Cost']

        return positions, orders

    def mark_parent_child_orders(self, df: pd.DataFrame, key_cols: List[str] = ["Date", "Symbol", "Action", "Order Type"], order_id_col: str = "Order ID", parent_id_col: str = "parentId", oca_col: str = "ocaGroup", relation_key_col: str = "relation_key", relation_side_col: str = "relation_side") -> pd.DataFrame:
        """
        Returns a copy of df with two new columns:
        - relation_key: blank for unrelated orders, otherwise Date_Symbol_Action_OrderType for the group
        - relation_side: 'parent' / 'child' / '' for unrelated
        Detects relations via parentId (preferred) and also by ocaGroup when present.
        """
        df = df.copy()
        # Normalise id columns
        if order_id_col in df.columns:
            df[order_id_col] = pd.to_numeric(df[order_id_col], errors="coerce")
        else:
            df[order_id_col] = pd.NA

        if parent_id_col in df.columns:
            df[parent_id_col] = pd.to_numeric(df[parent_id_col], errors="coerce").fillna(0).astype(int)
        else:
            df[parent_id_col] = 0

        # Prepare output columns
        df[relation_key_col] = ""
        df[relation_side_col] = ""

        # Helper to build key from a row
        def build_key_row(r):
            parts = [str(r.get(c, "")) for c in key_cols]
            return "_".join(parts)

        # 1) Mark parent/child using parentId
        children = df[df[parent_id_col] > 0]
        for idx, child in children.iterrows():
            pid = int(child[parent_id_col])
            parents = df[df[order_id_col] == pid]
            if parents.empty:
                # no parent found in this snapshot
                continue
            parent_idx = parents.index[0]
            key = build_key_row(df.loc[parent_idx])
            # set key for both parent and child (do not overwrite if already set)
            if not df.at[parent_idx, relation_key_col]:
                df.at[parent_idx, relation_key_col] = key
                df.at[parent_idx, relation_side_col] = "parent"
            df.at[idx, relation_key_col] = key
            df.at[idx, relation_side_col] = "child"

        # 2) Also consider ocaGroup (orders sharing same non-empty ocaGroup -> related)
        if oca_col in df.columns:
            grouped = df.groupby(oca_col)
            for group_key, g in grouped:
                if pd.isna(group_key) or group_key == "":
                    continue
                if len(g) <= 1:
                    continue
                # use first row as representative to build key
                rep = g.iloc[0]
                key = build_key_row(rep)
                for i, _ in g.iterrows():
                    # only set if not already set by parentId logic
                    if not df.at[i, relation_key_col]:
                        df.at[i, relation_key_col] = key
                    # set side based on parentId presence
                    if df.at[i, parent_id_col] and df.at[i, parent_id_col] > 0:
                        df.at[i, relation_side_col] = "child"
                    elif df.at[i, relation_side_col] == "":
                        df.at[i, relation_side_col] = "parent"

        # Keep blanks for unrelated orders (already "")
        return df

    # 2 Active Orders
    def fetch_active_orders(self, ib_connection, account_list):
        # Prepare current date once
        today = datetime.now().strftime('%Y-%m-%d')

        # Fetch all open orders
        open_orders = ib_connection.reqAllOpenOrders()

        # Container for all records
        order_records = []

        # Loop through each account
        for account_id in account_list:
            for order in open_orders:
                order_obj = order.order

                # Filter by account
                if order_obj.account != account_id:
                    continue

                contract = order.contract

                order_records.append({
                    'Date': today,
                    'Account': account_id,
                    'Order ID': order_obj.orderId,
                    'parentId': getattr(order_obj, 'parentId', 0),
                    'ocaGroup': getattr(order_obj, 'ocaGroup', None),
                    'Symbol': contract.symbol,
                    'Action': order_obj.action,
                    'Order Type': order_obj.orderType,
                    'Quantity': order_obj.totalQuantity,
                    'Lmt Price': order_obj.lmtPrice,
                    'Aux Price': order_obj.auxPrice,
                    'TIF': order_obj.tif,
                    'Transmit': order_obj.transmit,
                    'Status': order.orderStatus.status
                })

        # Create final DataFrame
        df_orders = pd.DataFrame(order_records)
        df_orders['Order ID'] = pd.to_numeric(df_orders['Order ID'], errors='coerce')
        df_orders['parentId'] = pd.to_numeric(df_orders['parentId'], errors='coerce').fillna(0).astype(int)

        # children = rows where parentId > 0
        children = df_orders[df_orders['parentId'] > 0]
        # join to get parent info
        parent_child = children.merge(
            df_orders[['Order ID', 'Symbol', 'Account', 'Status']].rename(columns={
                'Order ID': 'parentOrderId', 'Symbol': 'parentSymbol', 'Account': 'parentAccount',
                'Status': 'parentStatus'
            }),
            left_on='parentId', right_on='parentOrderId', how='left'
        )

        return df_orders

    # 3 Positions
    def get_positions(self, ib_connection, account_list):
        # Use delayed market data
        ib_connection.reqMarketDataType(3)

        # Today's date
        today = datetime.now().strftime('%Y-%m-%d')

        # Store all position records here
        position_records = []

        # Loop through each account
        for account_id in account_list:
            positions = ib_connection.positions(account=account_id)

            for pos in positions:
                contract = pos.contract
                quantity = pos.position
                avg_cost = pos.avgCost

                # Fetch snapshot price
                ib_connection.qualifyContracts(contract)
                ticker = ib_connection.reqMktData(contract, snapshot=True)
                ib_connection.sleep(1.0)  # Respect pacing limits

                # Handle missing/delayed data safely
                price = (
                        getattr(ticker, 'last', None)
                        or getattr(ticker, 'close', None)
                        or getattr(ticker, 'delayedLast', None)
                        or getattr(ticker, 'delayedClose', None)
                        or 0.0
                )

                market_value = price * quantity
                unrealized_pnl = (price - avg_cost) * quantity
                realized_pnl = None  # Not exposed in positions API

                position_records.append({
                    'Date': today,
                    'Account': account_id,
                    'Symbol': contract.symbol,
                    'Quantity': quantity,
                    'Average Cost': avg_cost,
                    'Current Price': price,
                    'Market Value': market_value,
                    'Unrealized PnL': unrealized_pnl,
                    'Realized PnL': realized_pnl,
                    'Currency': contract.currency
                })
            # Create final DataFrame
            df_positions = pd.DataFrame(position_records)
        return df_positions

    def calculate_risk_exposure(self, sheets):
        orders = sheets['Active Orders']
        position = sheets['Positions']
        orders['multi'] = np.where(
            orders['Action'] == "SELL",  # condition
            1,  # value if True
            -1  # value if False
        )
        orders['Total Liq Amount'] = ((orders['Quantity'] * orders['Aux Price'])) * orders['multi']
        position['Action'] = np.where(
            position['Quantity'] > 0,  # condition
            'SELL',  # value if True
            'BUY'  # value if False
        )
        orders.drop(columns='multi', inplace=True)
        position['Order Type'] = 'STP'
        position['Cost'] = position['Quantity'] * position['Average Cost']
        keys_to_merge = ['Date', 'Account', 'Symbol', 'Action', 'Order Type']
        total_amount_stploss = orders.groupby(keys_to_merge)['Total Liq Amount'].sum().reset_index()
        position = position.merge(total_amount_stploss, on=keys_to_merge, how='left')
        position['Capital Exposure'] = position['Total Liq Amount'] - position['Cost']

        return orders, position

    def concatenate_dataframes(self, dataframe_1, dataframe_2):
        df = pd.concat([dataframe_1, dataframe_2], ignore_index=True).drop_duplicates()
        return df


#client = GetInfo()
# TESTING request_path_to_user
# TESTING define_sheets_to_update

#updates = client.define_sheets_to_update_from_local_path(client.request_path_to_user("hello", f_type["excel"]), sheet_list)

#for key, value in updates.items():
#    value.to_excel('C:/0.Repositories/' + key + '.xlsx' , index = False)

# print(path)


