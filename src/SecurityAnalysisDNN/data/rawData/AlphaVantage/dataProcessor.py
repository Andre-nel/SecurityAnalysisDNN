from pathlib import Path


class AlphaVantageDataProcessor():

    def __init__(self, file_path: Path) -> None:
        # Path to the excel file exported from Alpha Vantage
        self.file_path = file_path

    # todo
