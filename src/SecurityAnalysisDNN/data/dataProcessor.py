import os
import logging
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
from pathlib import Path

try:
    from .customExceptions import DateAlignmentError, ValidationError
    from .utils import find_first_close_date, find_last_close_date, find_closest_date
    from .. import logger
except ImportError:
    from customExceptions import DateAlignmentError, ValidationError
    from utils import find_first_close_date, find_last_close_date, find_closest_date

    import sys
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(name)s %(levelname)s %(message)s',
                        stream=sys.stdout)
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)


class StockAnalysisDataProcessor():

    def __init__(self, symbol: str, file_path: Path, sheet_names: list = None,
                 close_col_name: str = 'Close Price') -> None:
        # Path to the excel file exported from Stock Analysis
        self.symbol = symbol
        self.file_path = file_path
        self.sheet_names = sheet_names
        self.close_col_name = close_col_name
        self.yf_stock = yf.Ticker(symbol)

        self._sheets_dict = None
        self._combined_df = None

    @property
    def sheets_dict(self) -> dict:
        if self._sheets_dict is None:
            # Reading all sheets into a dictionary of DataFrames
            self._sheets_dict = pd.read_excel(
                self.file_path, sheet_name=self.sheet_names)

            for sheet, df in self._sheets_dict.items():
                df = df.transpose()
                # Set the first row as the header
                new_header = df.iloc[0, :]
                df = df[1:]  # Take the data less the header row
                df.columns = new_header  # Set the header row as the df header
                df.index = pd.to_datetime(df.index)
                df = df.sort_index(ascending=True)
                # drop the first row
                df = df.iloc[1:]
                self._sheets_dict[sheet] = df
        return self._sheets_dict

    @property
    def combined_df(self) -> pd.DataFrame:
        if self._combined_df is None:
            self._combined_df: pd.DataFrame = pd.concat(
                self.sheets_dict.values(), axis=1)
            self._combined_df = addPrice(self._combined_df.copy(), self.yf_stock, self.close_col_name)
        return self._combined_df


def addPrice(df: pd.DataFrame, yf_stock: yf.Ticker, close_col_name: str = 'Close Price') -> pd.DataFrame:
    df.index = pd.to_datetime(df.index)

    start_date = df.index.to_list()[0] + timedelta(days=1)
    end_date = df.index.to_list()[-1] + timedelta(days=2)
    # Get historical market data
    hist_price_data = yf_stock.history(
        start=start_date, end=end_date, interval='3mo')     # quarterly
    hist_price_data.index = hist_price_data.index.tz_localize(None).normalize()
    hist_price_data.index = pd.to_datetime(hist_price_data.index)

    first_price_date = hist_price_data.index[0]
    first_close_date = find_first_close_date(hist_price_data, df)
    last_close_date = find_last_close_date(hist_price_data, df)

    if first_close_date and last_close_date:
        # Drop all indices before the found date in each DataFrame
        hist_price_data = hist_price_data[(hist_price_data.index >= first_close_date) & (
            hist_price_data.index <= last_close_date)]
        df = df[(df.index >= first_close_date) & (
            df.index <= last_close_date)]
        logger.debug("DataFrames trimmed successfully.")
    else:
        # Find the closest date in fundamentalDataDf.index to firstPriceDate
        closest_date = find_closest_date(
            first_price_date, df.index)
        # Update firstPriceDate to the closest date found
        if closest_date:
            # Setting firstPriceDate to the first day of the next month
            first_price_date = (
                closest_date + relativedelta(months=1)).replace(day=1)
            logger.debug(f"Updated firstPriceDate to the closest date: "
                         f"{first_price_date}")
        else:
            raise DateAlignmentError(
                "No date found close to the firstPriceDate.")
        # Get historical market data
        hist_price_data: pd.DataFrame = yf_stock.history(
            start=first_price_date, end=end_date, interval='3mo')     # quarterly
        hist_price_data.index = hist_price_data.index.tz_localize(
            None).normalize()
        hist_price_data.index = pd.to_datetime(hist_price_data.index)
        # Find the first close date
        first_close_date = find_first_close_date(
            hist_price_data, df)
        last_close_date = find_last_close_date(
            hist_price_data, df)
        if first_close_date and last_close_date:
            # Drop all indices before the found date in each DataFrame
            hist_price_data = hist_price_data[(hist_price_data.index >= first_close_date) & (
                hist_price_data.index <= last_close_date)]
            df = df[(df.index >= first_close_date) & (
                df.index <= last_close_date)]
            logger.debug("DataFrames trimmed successfully.")
        else:
            raise DateAlignmentError(f"No close dates within three days were found between the indices for "
                                     f"{yf_stock.ticker}.")

    if df.shape[0] != hist_price_data.shape[0]:
        logger.error(f"Could not add the Price Data for {yf_stock.ticker}: "
                     f"{df.shape[0]} != {hist_price_data.shape[0]}!")
        raise ValidationError(f"Could not add the Price Data for {yf_stock.ticker}: "
                              f"{df.shape[0]} != {hist_price_data.shape[0]}!")
    logger.info(f"{yf_stock.ticker}: start: "
                f"{df.index[0]}, end: {df.index[-1]}")
    logger.info(f"{yf_stock.ticker}: {df.shape[0]}")
    df[close_col_name] = hist_price_data['Close'].values
    return df


if __name__ == "__main__":
    dateStr = datetime.date(datetime.now()).strftime("%d_%m_%Y")
    processed_rel_path = 'src/SecurityAnalysisDNN/data/processedData'
    pre_process_rel_path = 'src/SecurityAnalysisDNN/data/rawData/StockAnalysis/blue_chip_stocks'
    folder_to_preprocess = Path(os.getcwd()) / pre_process_rel_path
    folder_to_processed = Path(os.getcwd()) / processed_rel_path

    quarterly_sheets = ['Income-Quarterly', 'Balance-Sheet-Quarterly',
                        'Cash-Flow-Quarterly', 'Ratios-Quarterly']

    for pre_processed_file_path in folder_to_preprocess.glob('*.xls*'):
        symbol = pre_processed_file_path.stem.split('-')[0].upper().replace('.', '-')
        logger.info(symbol)

        stockAnalysisDataProcessor = StockAnalysisDataProcessor(
            symbol=symbol,
            file_path=pre_processed_file_path,
            sheet_names=quarterly_sheets,
            close_col_name='Close Price')

        processed_file_path = folder_to_processed / symbol / dateStr / f'{symbol}_quarterly_{dateStr}.xlsx'
        if not processed_file_path.parent.exists():
            processed_file_path.parent.mkdir(parents=True)

        try:
            stockAnalysisDataProcessor.combined_df.to_excel(processed_file_path)
        except (DateAlignmentError, ValidationError):
            logger.exception(
                f"Could not add the price data for {symbol}")
