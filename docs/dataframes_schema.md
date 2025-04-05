## Dataframes Schema

Documentation automatically generated from [`scripts/generate_dataframe_schemas.py`](/scripts/generate_dataframe_schemas.py)

### Inbound / Outbound flight data
| # | Column | Dtype |
|--------|----------------|-------|
| 0 | offerID | object |
| 1 | chainID | int64 |
| 2 | startDate | datetime64[ns] |
| 3 | returnDate | datetime64[ns] |
| 4 | price | int64 |
| 5 | departureAirport | object |
| 6 | arrivalAirport | object |
| 7 | departureTime | datetime64[ns] |
| 8 | arrivalTime | datetime64[ns] |
| 9 | flightDuration | float64 |

#### Sample Data
|    | offerID                              |   chainID | startDate           | returnDate          |   price | departureAirport   | arrivalAirport   | departureTime       | arrivalTime         |   flightDuration |
|---:|:-------------------------------------|----------:|:--------------------|:--------------------|--------:|:-------------------|:-----------------|:--------------------|:--------------------|-----------------:|
|  0 | cf39a95f-525b-46c4-822e-02f545ad4967 |         0 | 2025-04-12 00:00:00 | 2025-04-19 00:00:00 |      76 | FNC                | MXP              | 2025-04-12 14:50:00 | 2025-04-12 19:30:00 |              280 |
|  1 | 10aa65be-a1ae-4878-b04e-e22c530fd3a1 |         0 | 2025-04-12 00:00:00 | 2025-04-19 00:00:00 |     111 | FNC                | LIS              | 2025-04-12 04:05:00 | 2025-04-12 05:50:00 |              105 |
|  2 | 10aa65be-a1ae-4878-b04e-e22c530fd3a1 |         1 | 2025-04-12 00:00:00 | 2025-04-19 00:00:00 |     111 | LIS                | MXP              | 2025-04-12 07:15:00 | 2025-04-12 11:00:00 |              225 |
|  3 | 680dd969-7d79-4aea-9026-d88b342123a3 |         0 | 2025-04-12 00:00:00 | 2025-04-19 00:00:00 |     163 | FNC                | LIS              | 2025-04-12 12:35:00 | 2025-04-12 14:20:00 |              105 |
|  4 | 680dd969-7d79-4aea-9026-d88b342123a3 |         1 | 2025-04-12 00:00:00 | 2025-04-19 00:00:00 |     163 | LIS                | MXP              | 2025-04-12 15:30:00 | 2025-04-12 19:15:00 |              225 |

---

### Merged inbound and outbound flight data
| # | Column | Dtype |
|--------|----------------|-------|
| 0 | offerID_Outbound | object |
| 1 | departureAirport_Outbound | object |
| 2 | arrivalAirport_Outbound | object |
| 3 | departureTime_Outbound | datetime64[ns] |
| 4 | arrivalTime_Outbound | datetime64[ns] |
| 5 | totalDuration_Outbound | float64 |
| 6 | offerID_Inbound | object |
| 7 | departureAirport_Inbound | object |
| 8 | arrivalAirport_Inbound | object |
| 9 | departureTime_Inbound | datetime64[ns] |
| 10 | arrivalTime_Inbound | datetime64[ns] |
| 11 | totalDuration_Inbound | float64 |
| 12 | fullPrice | int64 |

#### Sample Data
|    | offerID_Outbound                     | departureAirport_Outbound   | arrivalAirport_Outbound   | departureTime_Outbound   | arrivalTime_Outbound   |   totalDuration_Outbound | offerID_Inbound                      | departureAirport_Inbound   | arrivalAirport_Inbound   | departureTime_Inbound   | arrivalTime_Inbound   |   totalDuration_Inbound |   fullPrice |
|---:|:-------------------------------------|:----------------------------|:--------------------------|:-------------------------|:-----------------------|-------------------------:|:-------------------------------------|:---------------------------|:-------------------------|:------------------------|:----------------------|------------------------:|------------:|
|  0 | 00032d29-07c7-4ca7-ae7f-af7e8fc68725 | ['MXP', 'DUS']              | ['DUS', 'FNC']            | 2025-04-09 18:50:00      | 2025-04-10 09:30:00    |                      880 | 0a53de7d-c7b3-4a78-85c1-a73c40f94865 | ['FNC', 'LIS']             | ['LIS', 'MXP']           | 2025-04-15 06:25:00     | 2025-04-15 16:25:00   |                     600 |         304 |
|  1 | 00032d29-07c7-4ca7-ae7f-af7e8fc68725 | ['MXP', 'DUS']              | ['DUS', 'FNC']            | 2025-04-09 18:50:00      | 2025-04-10 09:30:00    |                      880 | 18358ac5-cb87-4b42-935b-30d44220d3c5 | ['FNC', 'LIS']             | ['LIS', 'MXP']           | 2025-04-15 17:40:00     | 2025-04-16 00:45:00   |                     425 |         339 |
|  2 | 00032d29-07c7-4ca7-ae7f-af7e8fc68725 | ['MXP', 'DUS']              | ['DUS', 'FNC']            | 2025-04-09 18:50:00      | 2025-04-10 09:30:00    |                      880 | 3a4e93bd-ed47-482a-bc17-01674eecd19e | ['FNC', 'OPO']             | ['OPO', 'MXP']           | 2025-04-15 14:35:00     | 2025-04-15 21:00:00   |                     385 |         312 |
|  3 | 00032d29-07c7-4ca7-ae7f-af7e8fc68725 | ['MXP', 'DUS']              | ['DUS', 'FNC']            | 2025-04-09 18:50:00      | 2025-04-10 09:30:00    |                      880 | 3dc2c355-2181-4239-855f-a95fd3b1de73 | ['FNC', 'PRG']             | ['PRG', 'MXP']           | 2025-04-15 15:15:00     | 2025-04-15 23:05:00   |                     470 |         337 |
|  4 | 00032d29-07c7-4ca7-ae7f-af7e8fc68725 | ['MXP', 'DUS']              | ['DUS', 'FNC']            | 2025-04-09 18:50:00      | 2025-04-10 09:30:00    |                      880 | 52a03d07-9a51-47a1-8c10-632a3720beee | ['FNC', 'LIS']             | ['LIS', 'MXP']           | 2025-04-15 09:30:00     | 2025-04-15 17:30:00   |                     480 |         316 |

---

### Gantt chart data
| # | Column | Dtype |
|--------|----------------|-------|
| 0 | startDate | datetime64[ns] |
| 1 | returnDate | datetime64[ns] |
| 2 | Price | int64 |

#### Sample Data
|    | startDate           | returnDate          |   Price |
|---:|:--------------------|:--------------------|--------:|
|  0 | 2025-04-14 00:00:00 | 2025-04-16 00:00:00 |     369 |
|  1 | 2025-04-14 00:00:00 | 2025-04-17 00:00:00 |     359 |
|  2 | 2025-04-15 00:00:00 | 2025-04-17 00:00:00 |     215 |
|  3 | 2025-04-15 00:00:00 | 2025-04-18 00:00:00 |     215 |
|  4 | 2025-04-16 00:00:00 | 2025-04-18 00:00:00 |     317 |

---

### Heatmap chart data
| # | Column | Dtype |
|--------|----------------|-------|
| 0 | Departure | Date |
| 1 | Return | Date |
| 2 | Number | of |
| 3 | Departure | Date_fmt |
| 4 | Return | Date_fmt |

#### Sample Data
|    | Departure Date   | Return Date   |   Number of Flights | Departure Date_fmt   | Return Date_fmt   |
|---:|:-----------------|:--------------|--------------------:|:---------------------|:------------------|
|  0 | 2025-04-07       | 2025-04-07    |                   0 | Mon 07 Apr           | Mon 07 Apr        |
|  1 | 2025-04-07       | 2025-04-08    |                   0 | Mon 07 Apr           | Tue 08 Apr        |
|  2 | 2025-04-07       | 2025-04-09    |                   0 | Mon 07 Apr           | Wed 09 Apr        |
|  3 | 2025-04-07       | 2025-04-10    |                   0 | Mon 07 Apr           | Thu 10 Apr        |
|  4 | 2025-04-07       | 2025-04-11    |                 110 | Mon 07 Apr           | Fri 11 Apr        |

---

### Flight duration binned data
| # | Column | Dtype |
|--------|----------------|-------|
| 0 | Flight | Duration |
| 1 | Count | int64 |
| 2 | Bin | category |

#### Sample Data
|    | Flight Duration   |   Count | Bin        |
|---:|:------------------|--------:|:-----------|
|  0 | 0-2h              |       0 | (0, 120]   |
|  1 | 2-4h              |       7 | (120, 240] |
|  2 | 4-6h              |     105 | (240, 360] |
|  3 | 6-8h              |     196 | (360, 480] |
|  4 | 8-10h             |     125 | (480, 600] |

---

