import requests
import time
from datetime import datetime
from typing import Optional


class NSEService:

    BASE_URL = "https://www.nseindia.com"

    OPTION_CHAIN_URL = (
        "https://www.nseindia.com/api/option-chain-v3"
    )

    def __init__(self):

        self.session = requests.Session()

        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/151.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.nseindia.com/option-chain",
            "Connection": "keep-alive",
            "DNT": "1",
        })

        self.last_request_time = 0

    # -------------------------------------------------------
    # CREATE NSE SESSION
    # -------------------------------------------------------

    def create_session(self):

        try:

            response = self.session.get(
                self.BASE_URL,
                timeout=10
            )

            response.raise_for_status()

            time.sleep(1)

            response = self.session.get(
                self.BASE_URL + "/option-chain",
                timeout=10
            )

            response.raise_for_status()

            return True

        except Exception as e:

            print("NSE session error:", e)

            return False

    # -------------------------------------------------------
    # GET OPTION CHAIN
    # -------------------------------------------------------

    def get_option_chain(
        self,
        symbol: str = "NIFTY",
        expiry: Optional[str] = None
    ):

        params = {
            "type": "Indices",
            "symbol": symbol
        }

        if expiry:
            params["expiry"] = expiry

        try:

            # Rate limiting
            current_time = time.time()

            if current_time - self.last_request_time < 2:

                time.sleep(
                    2 - (current_time - self.last_request_time)
                )

            self.last_request_time = time.time()

            response = self.session.get(
                self.OPTION_CHAIN_URL,
                params=params,
                timeout=15
            )

            # NSE may return 401/403 if session expired
            if response.status_code in [401, 403]:

                print(
                    "NSE session expired. Creating new session..."
                )

                self.create_session()

                response = self.session.get(
                    self.OPTION_CHAIN_URL,
                    params=params,
                    timeout=15
                )

            response.raise_for_status()

            return response.json()

        except Exception as e:

            print("NSE option chain error:", e)

            # Try once more with fresh session
            try:

                self.create_session()

                response = self.session.get(
                    self.OPTION_CHAIN_URL,
                    params=params,
                    timeout=15
                )

                response.raise_for_status()

                return response.json()

            except Exception as retry_error:

                print(
                    "NSE retry failed:",
                    retry_error
                )

                raise

    # -------------------------------------------------------
    # GET AVAILABLE EXPIRIES
    # -------------------------------------------------------

    def get_expiries(self, symbol="NIFTY"):

        data = self.get_option_chain(
            symbol=symbol
        )

        expiries = data.get(
            "records",
            {}
        ).get(
            "expiryDates",
            []
        )

        return expiries

    # -------------------------------------------------------
    # GET NEAREST EXPIRY
    # -------------------------------------------------------

    def get_nearest_expiry(self, symbol="NIFTY"):

        expiries = self.get_expiries(
            symbol
        )

        if not expiries:

            raise Exception(
                f"No expiry dates found for {symbol}"
            )

        today = datetime.now().date()

        valid_expiries = []

        for expiry in expiries:

            try:

                expiry_date = datetime.strptime(
                    expiry,
                    "%d-%b-%Y"
                ).date()

                if expiry_date >= today:

                    valid_expiries.append(
                        (
                            expiry_date,
                            expiry
                        )
                    )

            except ValueError:

                continue

        if not valid_expiries:

            raise Exception(
                f"No future expiry found for {symbol}"
            )

        valid_expiries.sort(
            key=lambda x: x[0]
        )

        return valid_expiries[0][1]


# Global service instance
nse_service = NSEService()

