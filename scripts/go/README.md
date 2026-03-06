# flights-api

A self-contained REST API wrapping the [google-flights-api](https://github.com/krisukox/google-flights-api) library, exposing three endpoints over HTTP.

## Build & run

```bash
# Build the image
docker build -t flights-api .

# Run on port 8080
docker run -p 8080:8080 flights-api

# Custom port
docker run -p 9000:9000 -e PORT=9000 flights-api
```

---

## Endpoints

All endpoints accept **POST** requests with either `application/json` or `application/x-www-form-urlencoded` bodies.

---

### `POST /getOffers`

Returns a list of full flight offers between two airports.

**Request body**

| Field | Type | Required | Description |
|---|---|---|---|
| `departureAirport` | string | ✓ | IATA code (e.g. `BLQ`) |
| `destinationAirport` | string | ✓ | IATA code (e.g. `LHR`) |
| `startDate` | string | ✓ | `YYYY-MM-DD` |
| `returnDate` | string | ✓ | `YYYY-MM-DD` |
| `tripType` | string | ✓ | `oneway` or `roundtrip` |
| `stops` | int | ✓ | `-1` any, `0` nonstop, `1`, `2` |
| `class` | string | | `Economy` (default), `PremiumEconomy`, `Business`, `First` |

**Example**

```bash
curl -X POST http://localhost:8080/getOffers \
  -H "Content-Type: application/json" \
  -d '{
    "departureAirport": "BLQ",
    "destinationAirport": "LHR",
    "startDate": "2025-06-01",
    "returnDate": "2025-06-10",
    "tripType": "roundtrip",
    "stops": 0,
    "class": "Economy"
  }'
```

---

### `POST /getPriceGraph`

Returns a set of round-trip offers across a date range and a range of trip lengths. Useful for finding the cheapest date combination.

**Request body**

| Field | Type | Required | Description |
|---|---|---|---|
| `departureAirport` | string | ✓ | IATA code |
| `destinationAirport` | string | ✓ | IATA code |
| `startDate` | string | ✓ | Start of the search window `YYYY-MM-DD` |
| `returnDate` | string | ✓ | End of the search window `YYYY-MM-DD` |
| `minDays` | int | ✓ | Minimum trip length in days |
| `maxDays` | int | ✓ | Maximum trip length in days |
| `stops` | int | ✓ | `-1` any, `0` nonstop, `1`, `2` |
| `class` | string | | `Economy` (default), `PremiumEconomy`, `Business`, `First` |

**Example**

```bash
curl -X POST http://localhost:8080/getPriceGraph \
  -H "Content-Type: application/json" \
  -d '{
    "departureAirport": "BLQ",
    "destinationAirport": "LHR",
    "startDate": "2025-06-01",
    "returnDate": "2025-07-31",
    "minDays": 5,
    "maxDays": 10,
    "stops": -1
  }'
```

---

### `POST /getUrl`

Returns a shareable Google Flights URL for the given search parameters.

**Request body** — same fields as `/getOffers`.

**Example**

```bash
curl -X POST http://localhost:8080/getUrl \
  -H "Content-Type: application/json" \
  -d '{
    "departureAirport": "BLQ",
    "destinationAirport": "LHR",
    "startDate": "2025-06-01",
    "returnDate": "2025-06-10",
    "tripType": "roundtrip",
    "stops": 0
  }'
```

**Response**

```json
{ "url": "https://www.google.com/travel/flights/..." }
```

---

### `GET /health`

Returns `{"status":"ok"}` — useful for container health checks.
