import pathlib
import requests
import google.auth.transport.requests
import google.oauth2.id_token
import os
import json
import concurrent.futures
import pandas as pd
import threading
from typing import List, Literal


class FlightsController:
    def __init__(self):
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
        
        # Dictionary to store the authorization tokens
        self.auth_tokens = {}

        # Authenticate to all endpoints using threads
        self.__authenticate_endpoints_with_threads()
        
    def __authenticate_endpoints_with_threads(self):
        threads = []
        for endpoint, url in self.endpoints.items():
            thread = threading.Thread(target=self.__auth_to_gcp, args=(endpoint, url))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()

    def __auth_to_gcp(self, endpoint: str, function_url: str):
        """
        Authenticates to the provided GCP Cloud Function
        """
        auth_req = google.auth.transport.requests.Request()
        id_token = google.oauth2.id_token.fetch_id_token(auth_req, function_url)
        self.auth_tokens[endpoint] = "Bearer " + id_token

    def get_iata_codes_list(self) -> List[str]:
        iata_codes_list = self.airports["iata_code"].tolist()
        iata_codes_list.sort()

        return iata_codes_list

    def get_airport_names_list(self) -> List[str]:
        airport_names_list = self.airports["name"].tolist()
        airport_names_list.sort()

        return airport_names_list

    def get_airports_json(self, key: Literal['name', 'iata_code']='name') -> dict:
        if key == "name":
            value = "iata_code"
        else:
            value = "name"

        records = self.airports.to_dict(orient='records')
        return {record[key]: record[value] for record in records}

    def get_airports_tuples_list(self) -> List[tuple]:
        records = self.airports.to_dict(orient='records')
        return [(record["iata_code"], record["name"]) for record in records]

    def get_price_graph(self, params: dict) -> pd.DataFrame:
        response = requests.post(
            url=self.endpoints["getPriceGraph"],
            data=params,
            headers={
                "Authorization": self.auth_tokens["getPriceGraph"]
            }
        )

        if response.status_code == 200:
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
            
            return priceChart_df
        else:
            raise Exception(f"Error {response.status_code}: {response.content.decode('utf-8')}")
