import pandas as pd
from common import API_KEY
import requests
import time
from common import f_type, sheet_list, columns_to_delete


class FinnInfo:
    """
    This class has been crated to establish connection to Yahoo Finance
    Get financial information for stocks and other securities
    """

    def __init__(self, getinfo_obj):
        self.api_key = API_KEY
        self.input_excel = getinfo_obj.request_path_to_user("Select stock list file", f_type["excel"])
        self.output_excel = getinfo_obj.request_path_to_user("Select path to save stock information", f_type["excel"])
        self.sleep_time = 1

    def fetch_stock_info(self):
        """
        Reads stock tickers from an Excel file and fetches their company info
        (sector, industry, market cap, etc.) using the FMP /stable/profile API.

        Parameters
        ----------
        input_excel : str
            Path to Excel file containing a column named 'symbol' or 'ticker'
        output_excel : str
            Path to save the resulting Excel file with company info
        api_key : str
            Your FinancialModelingPrep API key
        sleep_time : int or float, optional
            Seconds to wait between API calls to avoid rate limits (default = 1)
        """

        # === STEP 1: Read the tickers from Excel ===
        df = pd.read_excel(self.input_excel)

        # Columns that indicate data presence (can be adjusted)
        key_cols = ["price", "marketCap", "beta", "lastDividend", "range", "change", "changePercentage", "volume",
                    "averageVolume", "companyName", "currency"]

        key_cols = [col for col in key_cols if col in df.columns]
        if not key_cols:
            raise ValueError("None of the key data columns found in DataFrame")

        search_symbols = []
        no_search = []

        for _, row in df.iterrows():
            symbol = str(row['symbol']).strip()

            # Count how many key columns are non-empty
            non_empty = sum(
                pd.notna(row[col]) and str(row[col]).strip() not in ["", "NaN", "nan"]
                for col in key_cols
            )

            # Heuristic: if at least half of the key fields have data, it's valid
            if non_empty >= len(key_cols) / 2:
                no_search.append(symbol)
            else:
                search_symbols.append(symbol)

        search_symbols = list(set(search_symbols))

        # delete the empty symbols
        df.drop(df[df["symbol"].isin(search_symbols)].index, inplace=True)

        print(f"📘 Found {len(search_symbols)} tickers to process.\n")
        print("Information will be fetch for the following tickers:")
        for s in search_symbols:
            print(f"symbol: {s}")

        # === STEP 2: Fetch data for each symbol ===
        all_data = []
        for i, symbol in enumerate(search_symbols, start=1):
            print(f"[{i}/{len(search_symbols)}] Fetching {symbol} ...")
            url = f"https://financialmodelingprep.com/stable/profile?symbol={symbol}&apikey={self.api_key}"

            try:
                response = requests.get(url)
                response.raise_for_status()
                data = response.json()

                if isinstance(data, list) and len(data) > 0:
                    all_data.append(data[0])
                else:
                    print(f"⚠️ No data found for {symbol}")
            except requests.exceptions.RequestException as e:
                print(f"Error fetching {symbol}: {e}")

            time.sleep(self.sleep_time)

        # === STEP 3: Save to Excel ===
        if all_data:
            df_out = pd.DataFrame(all_data)
            df_combined = pd.concat([df, df_out])
            df_combined.to_excel(self.output_excel, index=False)
            print(f"\n✅ Done! Info saved to {self.output_excel}")
        else:
            print("\n⚠️ No data fetched — please check API key or endpoint.")
