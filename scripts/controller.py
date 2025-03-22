import pathlib
import requests
import google.auth.transport.requests
import google.oauth2.id_token
import os
import json
import uuid
import pandas as pd
import threading
import logging
import concurrent.futures
from typing import List
from my_enums import TripType


class FlightsController:
    def __init__(self):
        logging.info("Initializing FlightsController...")
        self.CURR_PATH = pathlib.Path(__file__)
        self.PRJ_ROOT = self.CURR_PATH.parent.parent

        # GCP Cloud Function auth credential
        credential_path = self.PRJ_ROOT / "data/cloud_functions.json"
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credential_path.resolve().as_posix()

        # GCP Cloud Function endpoints
        self.endpoints: dict = json.load(open(self.PRJ_ROOT / "data/endpoints.json", "r"))

        # Load the airports data
        self.airports = pd.read_csv(self.PRJ_ROOT / "data/airports.csv")
        self.airports = self.airports[["iata_code", "name"]]
        self.airports = self.airports[self.airports["iata_code"].notna()
                                    & (self.airports["iata_code"] != "")]
        self.airports.reset_index(drop=True, inplace=True)

        # Dictionary to store the authorization tokens
        self.auth_tokens = {}
        
    def authenticate_endpoints_with_threads(self):
        threads = []
        for endpoint, url in self.endpoints.items():
            thread = threading.Thread(target=self.__auth_to_gcp, args=(endpoint, url), name=endpoint)
            threads.append(thread)
            thread.start()
            logging.info(f"Authenticating to {thread.name}...")
        
        for thread in threads:
            thread.join()
            logging.info(f"Successfully authenticated to {thread.name}")

    def __auth_to_gcp(self, endpoint: str, function_url: str):
        """
        Authenticates to the provided GCP Cloud Function
        """
        auth_req = google.auth.transport.requests.Request()
        id_token = google.oauth2.id_token.fetch_id_token(auth_req, function_url)
        self.auth_tokens[endpoint] = "Bearer " + id_token

    def get_airports_json(self) -> List[dict]:
        """
        Returns the airports data as a list of dictionaries like so:
        ```
        {
            "index": 0,
            "iata_code": "AAA",
            "name": "Anaa Airport"
        }
        ```
        """
        ls = []
        for i, row in self.airports.iterrows():
            ls.append({
                "index": i,
                "iata_code": row["iata_code"],
                "name": row["name"]
            })

        return ls

    def get_price_graph(self, params: dict) -> pd.DataFrame:
        logging.info(f"API Request for getPriceGraph\n{params}")
        response = requests.post(
            url=self.endpoints["getPriceGraph"],
            data=params,
            headers={
                "Authorization": self.auth_tokens["getPriceGraph"]
            }
        )

        if response.status_code != 200:
            raise Exception(f"Error {response.status_code}: {response.content.decode('utf-8')}")

        data = json.loads(response.content)
        priceChart_df = pd.json_normalize(data)

        priceChart_df["StartDate"] = priceChart_df["StartDate"].str[:10]
        priceChart_df["ReturnDate"] = priceChart_df["ReturnDate"].str[:10]
        priceChart_df.rename({
            "StartDate": "startDate",
            "ReturnDate": "returnDate"
        }, axis=1, inplace=True)

        priceChart_df.sort_values(["startDate", "returnDate"], inplace=True)
        priceChart_df.reset_index(inplace=True, drop=True)

        if params["maxPrice"]:
            priceChart_df = priceChart_df[priceChart_df["Price"] <= params["maxPrice"]]
        
        priceChart_df[["startDate", "returnDate"]] = priceChart_df[["startDate", "returnDate"]].apply(pd.to_datetime)
        
        return priceChart_df

    def get_offers(self, reference_df: pd.DataFrame, params:dict, trip_type: TripType) -> pd.DataFrame:
        """
        Takes advantage of `futures` to invoke `_get_offer_df()` in parallel
        """
        getOffersToken = self.auth_tokens["getOffers"]

        # Setting parameters and columns
        departureAirport = None
        destinationAirport = None
        if trip_type == TripType.INBOUND:
            reference_df['fakeReturnDate'] = reference_df['returnDate'] + pd.to_timedelta(7, unit='d')
            reference_df = reference_df.loc[:, ['returnDate', 'fakeReturnDate']]
            reference_df.drop_duplicates(inplace=True, ignore_index=True)
            reference_df.sort_values(['returnDate', 'fakeReturnDate'], inplace=True)
            reference_df.reset_index(drop=True, inplace=True)
            reference_df.rename({
                'returnDate': 'startDate',
                'fakeReturnDate': 'returnDate'
            }, axis=1, inplace=True)

            departureAirport = params["destinationAirport"]
            destinationAirport = params["departureAirport"]
        else:
            reference_df.drop_duplicates(["startDate", "returnDate"], inplace=True, ignore_index=True)
            departureAirport = params["departureAirport"]
            destinationAirport = params["destinationAirport"]

        # Process requests
        responses = []
        with concurrent.futures.ProcessPoolExecutor(max_workers=10) as executor:
            futures = []
            for row in reference_df.itertuples():
                request_data = {
                    "startDate": row.startDate.strftime("%Y-%m-%d"),
                    "returnDate": row.returnDate.strftime("%Y-%m-%d"),
                    "departureAirport": departureAirport,
                    "destinationAirport": destinationAirport,
                    "tripType": "oneway"
                }
                future = executor.submit(self._get_offer_df, request_data, getOffersToken)
                futures.append(future)
            
            for future in concurrent.futures.as_completed(futures):
                data = future.result()
                responses.append(data)
        
        df = pd.concat(responses)

        # Data prep
        df.drop_duplicates(['chainID', 'startDate', 'returnDate', 'price',
                            'departureAirport','arrivalAirport','departureTime','arrivalTime']
                            , inplace=True, ignore_index=True)
        df[["startDate", "returnDate", "departureTime", "arrivalTime"]] = \
            df[["startDate", "returnDate", "departureTime", "arrivalTime"]].apply(pd.to_datetime)
        
        df["flightDuration"] = (df["arrivalTime"] - df["departureTime"]).dt.total_seconds() // 60
        # Preliminary filter: if the price of even a single one-way route
        # exceeds maxPrice, the whole combination will as well
        df = df[df["price"] <= params["maxPrice"]]
        df.reset_index(drop=True, inplace=True)

        return df

    def _get_offer_df(self, request_data:dict, getOffersToken:str) -> pd.DataFrame :
        """
        Perform a POST request towards GCP Cloud functions and retrieve a
        `pandas.DataFrame` containing flight offers

        Parameters:
        - `request_data`: the content to pass to the GCP function
        - `getOffersToken`: the bearer token for the GCP function to pass in the `Authorization` header
        """
        response = requests.post(
            url=self.endpoints["getOffers"],
            headers={
                "Authorization": getOffersToken
            },
            data=request_data
        )
        if response.status_code != 200:
            raise Exception(f"Error {response.status_code}: {response.content.decode('utf-8')}")

        raw_response = json.loads(response.content)

        offers = [val for val in raw_response]  # Unnest
        flights = []
        for o in offers:
            offer_id = str(uuid.uuid4())
            start_date = o['StartDate'][:10]
            return_date = o['ReturnDate'][:10]
            price = o['Price']
            flights_list = o['Flight']

            for ix, f in enumerate(flights_list):
                dep_airport = f['DepAirportCode']
                arr_airport = f['ArrAirportCode']
                dep_time = f['DepTime'][:16]
                arr_time = f['ArrTime'][:16]

                flights.append({
                    "offerID": offer_id,
                    "chainID": ix,
                    "startDate": start_date,
                    "returnDate": return_date,
                    "price": price,
                    "departureAirport": dep_airport,
                    "arrivalAirport": arr_airport,
                    "departureTime": dep_time,
                    "arrivalTime": arr_time
                })
        
        return pd.DataFrame(flights)

    def merge_offers(self, outb_df: pd.DataFrame, inb_df: pd.DataFrame, params:dict, filter=True) -> pd.DataFrame:
        def group(df) -> pd.DataFrame:
            grouped = df\
                .groupby(['offerID', 'startDate', 'returnDate'])\
                .agg({
                    'chainID': 'count',
                    'price': 'first',
                    'departureTime': 'first',
                    'arrivalTime': 'last',
                    'departureAirport': list,
                    'arrivalAirport': list
                })
            grouped.reset_index(inplace=True)
            grouped["layovers"] = grouped["chainID"] - 1
            grouped["totalDuration"] = pd.to_timedelta(grouped["arrivalTime"] - grouped["departureTime"])

            # grouped.drop("chainID", axis=1, inplace=True)
            return grouped
        
        outb_df = group(outb_df)
        inb_df = group(inb_df)

        full_offers = pd.merge(
            outb_df,
            inb_df,
            left_on="returnDate",
            right_on="startDate",
            suffixes=('_Outbound', '_Inbound')
        )
        
        full_offers["fullPrice"] = full_offers["price_Outbound"] + full_offers["price_Inbound"]
        full_offers["fullDuration"] = (full_offers["totalDuration_Outbound"] + full_offers["totalDuration_Inbound"])\
                                        .dt.total_seconds() // 60

        full_offers = full_offers[[
            # Outbound
            "offerID_Outbound",
            "departureAirport_Outbound",
            "arrivalAirport_Outbound",
            "departureTime_Outbound",
            "arrivalTime_Outbound",
            # Inbound
            "offerID_Inbound",
            "departureAirport_Inbound",
            "arrivalAirport_Inbound",
            "departureTime_Inbound",
            "arrivalTime_Inbound",
            # Total duration and price
            "fullPrice",
            "fullDuration"
        ]]

        if filter:
            # By full price
            full_offers = full_offers[
                full_offers["fullPrice"] <= params["maxPrice"]
            ]

            # By full duration
            full_offers = full_offers[
                full_offers["fullDuration"] <= params["maxDuration"]
            ]

        full_offers.reset_index(drop=True, inplace=True)
        return full_offers
