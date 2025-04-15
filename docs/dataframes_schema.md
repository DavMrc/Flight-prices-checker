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
| 7 | departureTime | datetime64[ns, |
| 8 | arrivalTime | datetime64[ns, |
| 9 | url | object |
| 10 | flightDuration | float64 |

#### Sample Data
|    | offerID                              |   chainID | startDate           | returnDate          |   price | departureAirport   | arrivalAirport   | departureTime             | arrivalTime               | url                                                                                                                       |   flightDuration |
|---:|:-------------------------------------|----------:|:--------------------|:--------------------|--------:|:-------------------|:-----------------|:--------------------------|:--------------------------|:--------------------------------------------------------------------------------------------------------------------------|-----------------:|
|  0 | b1e9f451-efce-4780-ae88-a04f7a896c49 |         0 | 2025-05-06 00:00:00 | 2025-05-13 00:00:00 |     168 | FNC                | MXP              | 2025-05-06 14:45:00+01:00 | 2025-05-06 19:25:00+02:00 | https://www.google.com/travel/flights/search?tfs=GiASCjIwMjUtMDUtMDYoAGoHCAESA0ZOQ3IHCAESA01YUEIBAUgBmAEC&curr=EUR&hl=und |              220 |
|  1 | 1f7cd563-de8a-4499-9688-eb1629d0a34a |         0 | 2025-04-26 00:00:00 | 2025-05-03 00:00:00 |     144 | FNC                | MXP              | 2025-04-26 14:50:00+01:00 | 2025-04-26 19:30:00+02:00 | https://www.google.com/travel/flights/search?tfs=GiASCjIwMjUtMDQtMjYoAGoHCAESA0ZOQ3IHCAESA01YUEIBAUgBmAEC&curr=EUR&hl=und |              220 |
|  2 | 5ac1428e-deb5-492f-a297-df9304fda1f2 |         0 | 2025-05-03 00:00:00 | 2025-05-10 00:00:00 |     182 | FNC                | MXP              | 2025-05-03 14:50:00+01:00 | 2025-05-03 19:30:00+02:00 | https://www.google.com/travel/flights/search?tfs=GiASCjIwMjUtMDUtMDMoAGoHCAESA0ZOQ3IHCAESA01YUEIBAUgBmAEC&curr=EUR&hl=und |              220 |
|  3 | 74c1ddf9-e05e-4daf-af63-d81907425e42 |         0 | 2025-04-29 00:00:00 | 2025-05-06 00:00:00 |     182 | FNC                | MXP              | 2025-04-29 14:45:00+01:00 | 2025-04-29 19:25:00+02:00 | https://www.google.com/travel/flights/search?tfs=GiASCjIwMjUtMDQtMjkoAGoHCAESA0ZOQ3IHCAESA01YUEIBAUgBmAEC&curr=EUR&hl=und |              220 |

---

### Merged inbound and outbound flight data
| # | Column | Dtype |
|--------|----------------|-------|
| 0 | offerID_Outbound | object |
| 1 | departureAirport_Outbound | object |
| 2 | arrivalAirport_Outbound | object |
| 3 | departureTime_Outbound | datetime64[ns, |
| 4 | arrivalTime_Outbound | datetime64[ns, |
| 5 | totalDuration_Outbound | float64 |
| 6 | offerID_Inbound | object |
| 7 | departureAirport_Inbound | object |
| 8 | arrivalAirport_Inbound | object |
| 9 | departureTime_Inbound | datetime64[ns, |
| 10 | arrivalTime_Inbound | datetime64[ns, |
| 11 | totalDuration_Inbound | float64 |
| 12 | fullPrice | int64 |

#### Sample Data
|    | offerID_Outbound                     | departureAirport_Outbound   | arrivalAirport_Outbound   | departureTime_Outbound    | arrivalTime_Outbound      |   totalDuration_Outbound | offerID_Inbound                      | departureAirport_Inbound   | arrivalAirport_Inbound   | departureTime_Inbound     | arrivalTime_Inbound       |   totalDuration_Inbound |   fullPrice |
|---:|:-------------------------------------|:----------------------------|:--------------------------|:--------------------------|:--------------------------|-------------------------:|:-------------------------------------|:---------------------------|:-------------------------|:--------------------------|:--------------------------|------------------------:|------------:|
|  0 | 49b466d2-1a58-4030-bcf6-2618c560a3dd | ['MXP']                     | ['FNC']                   | 2025-04-22 20:00:00+02:00 | 2025-04-22 23:10:00+01:00 |                      250 | 74c1ddf9-e05e-4daf-af63-d81907425e42 | ['FNC']                    | ['MXP']                  | 2025-04-29 14:45:00+01:00 | 2025-04-29 19:25:00+02:00 |                     220 |         333 |
|  1 | 643ee684-a2d6-4ef1-8735-1e96dacc33c7 | ['MXP']                     | ['FNC']                   | 2025-04-22 20:00:00+02:00 | 2025-04-22 23:10:00+01:00 |                      250 | 1f7cd563-de8a-4499-9688-eb1629d0a34a | ['FNC']                    | ['MXP']                  | 2025-04-26 14:50:00+01:00 | 2025-04-26 19:30:00+02:00 |                     220 |         295 |
|  2 | 83385f50-a119-4175-bb5f-f1473e8681e7 | ['MXP']                     | ['FNC']                   | 2025-04-29 20:00:00+02:00 | 2025-04-29 23:10:00+01:00 |                      250 | 5ac1428e-deb5-492f-a297-df9304fda1f2 | ['FNC']                    | ['MXP']                  | 2025-05-03 14:50:00+01:00 | 2025-05-03 19:30:00+02:00 |                     220 |         287 |
|  3 | d650ebc2-d2a8-42cc-b8d9-6f1019b6c283 | ['MXP']                     | ['FNC']                   | 2025-04-26 19:55:00+02:00 | 2025-04-26 23:05:00+01:00 |                      250 | 5ac1428e-deb5-492f-a297-df9304fda1f2 | ['FNC']                    | ['MXP']                  | 2025-05-03 14:50:00+01:00 | 2025-05-03 19:30:00+02:00 |                     220 |         426 |
|  4 | f0b11b1b-5378-4713-8be2-eda942069e6e | ['MXP']                     | ['FNC']                   | 2025-04-29 20:00:00+02:00 | 2025-04-29 23:10:00+01:00 |                      250 | b1e9f451-efce-4780-ae88-a04f7a896c49 | ['FNC']                    | ['MXP']                  | 2025-05-06 14:45:00+01:00 | 2025-05-06 19:25:00+02:00 |                     220 |         273 |

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

