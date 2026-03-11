import os
import requests
import json
import uuid
import logging
import datetime
import concurrent.futures
import pandas as pd
from helpers import get_project_root
from typing import List
from my_enums import TripType


PRJ_ROOT = get_project_root()


class FlightsController:
    def __init__(self):
        logging.info("Initializing FlightsController...")

        # GCP Cloud Function endpoints
        base_url = os.environ.get("API_BASE_URL", "http://localhost:8080")
        self.endpoints = {
            "getOffers": f"{base_url}/getOffers",
            "getPriceGraph": f"{base_url}/getPriceGraph",
            "getUrl": f"{base_url}/getUrl"
        }

        # Load the airports data
        self.airports = pd.read_csv(PRJ_ROOT / "data/airports.csv")
        # Filter
        airport_types = ["small_airport", "medium_airport", "large_airport"]
        self.airports = self.airports[self.airports["iata_code"].notna()
                                    & (self.airports["iata_code"] != "")
                                    & self.airports["type"].isin(airport_types)]

        # Lat and lon
        self.airports[["lat", "lon"]] = self.airports["coordinates"].str\
            .split(", ", expand=True)\
            .astype(float)\
            .rename({0: "lat", 1: "lon"}, axis=1)

        # Select fields
        self.airports = self.airports[["iata_code", "name", "lat", "lon"]]

        # Sort and reindex
        self.airports.sort_values("iata_code", inplace=True)
        self.airports.reset_index(drop=True, inplace=True)

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
                "name": row["name"],
                "lat": row["lat"],
                "lon": row["lon"]
            })

        return ls

    # --- Price graph ---
    def get_price_graph(self, params: dict) -> pd.DataFrame:
        logging.info(f"API Request for getPriceGraph\n{params}")
        response = requests.post(
            url=self.endpoints["getPriceGraph"],
            json=params
        )

        if response.status_code != 200:
            raise Exception(f"Error {response.status_code}: {response.content.decode('utf-8')}")

        data = json.loads(response.content)
        if not data:
            return pd.DataFrame(columns=["startDate", "returnDate", "Price", "Days"])

        priceChart_df = pd.json_normalize(data)
        priceChart_df["StartDate"] = priceChart_df["StartDate"].str[:10]
        priceChart_df["ReturnDate"] = priceChart_df["ReturnDate"].str[:10]
        priceChart_df.rename({
            "StartDate": "startDate",
            "ReturnDate": "returnDate"
        }, axis=1, inplace=True)

        priceChart_df.sort_values(["startDate", "returnDate"], inplace=True)
        priceChart_df.reset_index(inplace=True, drop=True)
        priceChart_df[["startDate", "returnDate"]] = priceChart_df[["startDate", "returnDate"]].apply(pd.to_datetime)
        priceChart_df["Days"] = (priceChart_df["returnDate"] - priceChart_df["startDate"]).dt.days
        priceChart_df.drop_duplicates(inplace=True)

        return priceChart_df

    def filter_price_graph(self, price_graph_df: pd.DataFrame, params: dict) -> pd.DataFrame:
        if "maxPrice" in params and params["maxPrice"] > 0:
            price_graph_df = price_graph_df[
                price_graph_df["Price"] <= params["maxPrice"]
            ]

        return price_graph_df

    # --- Offers ---
    def get_offers(self, reference_df: pd.DataFrame, params: dict, trip_type: TripType) -> pd.DataFrame:
        """
        Takes advantage of `futures` to invoke `_get_offer_df()` in parallel
        """
        logging.info(f"API Request for {trip_type} getOffers\n{params}")

        # Setting parameters and columns
        departureAirport = None
        destinationAirport = None

        if trip_type == TripType.INBOUND:
            reference_df = reference_df.copy()  # Ensure we're working with a copy to avoid warnings
            reference_df['fakeReturnDate'] = reference_df['returnDate'] + pd.to_timedelta(7, unit='d')
            reference_df = reference_df[['returnDate', 'fakeReturnDate']].drop_duplicates(ignore_index=True)
            reference_df = reference_df.sort_values(['returnDate', 'fakeReturnDate']).reset_index(drop=True)
            reference_df = reference_df.rename(columns={'returnDate': 'startDate', 'fakeReturnDate': 'returnDate'})

            departureAirport = params["destinationAirport"]
            destinationAirport = params["departureAirport"]
        else:
            reference_df = reference_df[['startDate', 'returnDate']].copy()  # Same as above
            reference_df = reference_df.drop_duplicates(subset=['startDate', 'returnDate'], ignore_index=True)

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
                future = executor.submit(self._get_offer_df, request_data)
                futures.append(future)
            
            for future in concurrent.futures.as_completed(futures):
                data = future.result()
                responses.append(data)
        
        df = pd.concat(responses)

        # Data prep
        df.drop_duplicates(['chainID', 'startDate', 'returnDate', 'price',
                            'departureAirport','arrivalAirport','departureTime','arrivalTime']
                            , inplace=True, ignore_index=True)
        df[["startDate", "returnDate"]] = df[["startDate", "returnDate"]].apply(pd.to_datetime)
        df[["departureTime", "arrivalTime"]] = df[["departureTime", "arrivalTime"]].apply(
            lambda x: pd.to_datetime(x, format="%Y-%m-%dT%H:%M:%S%z")
        )
        
        df["flightDuration"] = (df["arrivalTime"] - df["departureTime"]).dt.total_seconds() // 60
        # Preliminary filter: if the price of even a single one-way route
        # exceeds maxPrice, the whole combination will as well
        df = df[df["price"] <= params["maxPrice"]]
        df.reset_index(drop=True, inplace=True)

        return df

    def _get_offer_df(self, request_data:dict) -> pd.DataFrame :
        """
        Perform a POST request towards GCP Cloud functions and retrieve a
        `pandas.DataFrame` containing flight offers

        Parameters:
        - `request_data`: the content to pass to the GCP function
        - `getOffersToken`: the bearer token for the GCP function to pass in the `Authorization` header
        """
        response = requests.post(
            url=self.endpoints["getOffers"],
            json=request_data
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
                dep_time = f['DepTime']
                arr_time = f['ArrTime']

                # Offer URL
                offer_url_response = requests.post(
                    url=self.endpoints["getUrl"],
                    json=request_data
                )
                if response.status_code != 200:
                    raise Exception(f"Error {response.status_code}: {response.content.decode('utf-8')}")
                
                url = json.loads(offer_url_response.content)["url"]

                flights.append({
                    "offerID": offer_id,
                    "chainID": ix,
                    "startDate": start_date,
                    "returnDate": return_date,
                    "price": price,
                    "departureAirport": dep_airport,
                    "arrivalAirport": arr_airport,
                    "departureTime": dep_time,
                    "arrivalTime": arr_time,
                    "url": url
                })
        
        return pd.DataFrame(flights)

    def merge_offers(self, outb_df: pd.DataFrame, inb_df: pd.DataFrame) -> pd.DataFrame:
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
            grouped["totalDuration"] = pd.to_timedelta(
                grouped["arrivalTime"] - grouped["departureTime"]
            ).dt.total_seconds() // 60

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

        full_offers = full_offers[[
            # Outbound
            "offerID_Outbound",
            "departureAirport_Outbound",
            "arrivalAirport_Outbound",
            "departureTime_Outbound",
            "arrivalTime_Outbound",
            "totalDuration_Outbound",
            # Inbound
            "offerID_Inbound",
            "departureAirport_Inbound",
            "arrivalAirport_Inbound",
            "departureTime_Inbound",
            "arrivalTime_Inbound",
            "totalDuration_Inbound",
            # Total price
            "fullPrice",
        ]]

        full_offers.reset_index(drop=True, inplace=True)
        return full_offers

    def filter_merged_offers(self, merged_df: pd.DataFrame, params: dict) -> pd.DataFrame:
        """
        Filters merged offers based on `params["maxPrice"]` and `params["maxDuration"]`.

        If key is present, can also filter on `"selected_heatmap_point"`
        """
        # By full price
        if params["maxPrice"] > 0:
            merged_df = merged_df[
                merged_df["fullPrice"] <= params["maxPrice"]
            ]

        # By full duration
        if params["maxDuration"] > -1:
            merged_df = merged_df[
                (merged_df["totalDuration_Inbound"] <= params["maxDuration"]) &
                (merged_df["totalDuration_Outbound"] <= params["maxDuration"])
            ]
        
        # By heatmap selection point
        if "selected_heatmap_point" in params:
            dep_date = datetime.date.fromisoformat(params["selected_heatmap_point"]["Departure Date"])
            ret_date = datetime.date.fromisoformat(params["selected_heatmap_point"]["Return Date"])

            merged_df = merged_df[
                (merged_df["departureTime_Outbound"].dt.date == dep_date) &
                (merged_df["departureTime_Inbound"].dt.date == ret_date)
            ]

        return merged_df

    def _filter_merged_df_on_max_duration(self, max_duration: int, merged_df: pd.DataFrame) -> pd.DataFrame:
        merged_df = merged_df[
            (merged_df['totalDuration_Inbound'] <= max_duration) &
            (merged_df['totalDuration_Outbound'] <= max_duration)
        ]        
        return merged_df

    def _concat_offers_duration(self, merged_df: pd.DataFrame) -> pd.Series:
        inb_duration_minutes = merged_df["totalDuration_Inbound"]
        outb_duration_minutes = merged_df["totalDuration_Outbound"]
        return pd.concat([inb_duration_minutes, outb_duration_minutes])

    # --- Charts ---
    def flight_duration_barchart(self, merged_df: pd.DataFrame) -> pd.DataFrame:
        combined_durations = self._concat_offers_duration(merged_df)

        # Create bins of 2 hours (120 minutes)
        bin_size_in_minutes = 120
        bins = range(0, int(combined_durations.max())+bin_size_in_minutes, bin_size_in_minutes)

        # Calculate the count of flights in each bin
        duration_counts = pd.cut(combined_durations, bins=bins).value_counts().sort_index()

        duration_colname = 'Flight Duration'
        count_colname = 'Count'
        duration_df = pd.DataFrame({
            duration_colname: [f'{interval.left //60}-{interval.right //60}h' for interval in duration_counts.index],
            count_colname: duration_counts.values,
        })

        return duration_df

    def flight_count_heatmap(self, merged_df: pd.DataFrame) -> pd.DataFrame:
        df = merged_df[["departureTime_Outbound",  "departureTime_Inbound",
                "offerID_Inbound", "offerID_Outbound", "fullPrice"]].copy()
        # Keep only the date part
        df[["departureTime_Outbound", "departureTime_Inbound"]] = df[["departureTime_Outbound", "departureTime_Inbound"]]\
                                                                .apply(lambda x: x.dt.date)

        # Group by dates and count rows
        heatmap_data = df.groupby(['departureTime_Outbound', 'departureTime_Inbound']).size()\
                    .reset_index(name='Number of Flights')

        # --- Scaffold data ---
        # 
        # Add all possible combinations between the minimum departure date and the
        # maximum return date, imputing 0 number of flights. This ensures the
        # heatmaps plots correctely a box for every cell value

        # Find the overall min and max dates
        min_date = min(heatmap_data['departureTime_Outbound'].min(), heatmap_data['departureTime_Inbound'].min())
        max_date = max(heatmap_data['departureTime_Outbound'].max(), heatmap_data['departureTime_Inbound'].max())

        # Create a complete date range
        full_range = pd.date_range(start=min_date, end=max_date)
        # Generate all possible combinations of departureTime_Outbound and full_range
        all_combinations = pd.DataFrame(
            [(outb.date(), inb.date()) for outb in full_range for inb in full_range],
            columns=['departureTime_Outbound', 'departureTime_Inbound']
        )

        # Merge with existing heatmap_data to retain existing values
        heatmap_data = all_combinations.merge(
            heatmap_data,
            on=['departureTime_Outbound', 'departureTime_Inbound'],
            how='left'
        )
        # Fill missing 'Number of Flights' with 0
        heatmap_data.fillna({"Number of Flights": 0}, inplace=True)

        # Cast dates to datetime
        heatmap_data[["departureTime_Outbound", "departureTime_Inbound"]] = \
            heatmap_data[["departureTime_Outbound", "departureTime_Inbound"]].apply(pd.to_datetime)
        
        # Calculate the difference in days between departure and return dates
        heatmap_data["Days"] = (
            heatmap_data["departureTime_Inbound"] - heatmap_data["departureTime_Outbound"]
        ).dt.days + 1

        # Format dates into strings of format "%a %d %b"
        heatmap_data[["departureTime_Outbound_fmt", "departureTime_Inbound_fmt"]] = \
            heatmap_data[["departureTime_Outbound", "departureTime_Inbound"]].apply(lambda x: x.dt.strftime("%a %d %b"))
        
        # Format dates themselves
        heatmap_data[["departureTime_Outbound", "departureTime_Inbound"]] = \
            heatmap_data[["departureTime_Outbound", "departureTime_Inbound"]].apply(lambda x: x.dt.strftime("%Y-%m-%d"))

        # Renames columns
        outb_date_colname = "Departure Date"
        inb_date_colname = "Return Date"
        heatmap_data.rename({
            "departureTime_Outbound": outb_date_colname,
            "departureTime_Inbound": inb_date_colname,
            "departureTime_Outbound_fmt": f"{outb_date_colname}_fmt",
            "departureTime_Inbound_fmt": f"{inb_date_colname}_fmt",
        }, axis=1, inplace=True)

        return heatmap_data
