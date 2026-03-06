package main

import (
	"encoding/json"
	"fmt"
	"net/http"
	"strconv"
	"time"

	"github.com/krisukox/google-flights-api/flights"
)

// parseStops maps an integer to a flights.Stops value.
func parseStops(val int) (flights.Stops, error) {
	switch val {
	case -1:
		return flights.AnyStops, nil
	case 0:
		return flights.Nonstop, nil
	case 1:
		return flights.Stop1, nil
	case 2:
		return flights.Stop2, nil
	default:
		return 0, fmt.Errorf("invalid stops value: %d (must be -1, 0, 1, or 2)", val)
	}
}

// parseClass maps a string to a flights.Class value.
func parseClass(val string) (flights.Class, error) {
	switch val {
	case "", "Economy":
		return flights.Economy, nil
	case "PremiumEconomy":
		return flights.PremiumEconomy, nil
	case "Business":
		return flights.Business, nil
	case "First":
		return flights.First, nil
	default:
		return 0, fmt.Errorf("invalid class value: %s (must be Economy, PremiumEconomy, Business, or First)", val)
	}
}

// parseTripType maps a string to a flights.TripType value.
func parseTripType(val string) (flights.TripType, error) {
	switch val {
	case "oneway":
		return flights.OneWay, nil
	case "roundtrip":
		return flights.RoundTrip, nil
	default:
		return 0, fmt.Errorf("invalid tripType: %s (must be oneway or roundtrip)", val)
	}
}

// parseDate parses a date string in YYYY-MM-DD format.
func parseDate(val string) (time.Time, error) {
	return time.Parse("2006-01-02", val)
}

// decodeRequest decodes JSON or form-encoded request bodies into dst.
func decodeRequest(r *http.Request, dst interface{}) error {
	switch r.Header.Get("Content-Type") {
	case "application/json":
		if err := json.NewDecoder(r.Body).Decode(dst); err != nil {
			return fmt.Errorf("invalid request body: %v", err)
		}
	case "application/x-www-form-urlencoded":
		if err := r.ParseForm(); err != nil {
			return fmt.Errorf("error parsing form data: %v", err)
		}
		if err := fillFromForm(r, dst); err != nil {
			return err
		}
	default:
		return fmt.Errorf("unsupported Content-Type (use application/json or application/x-www-form-urlencoded)")
	}
	return nil
}

// fillFromForm populates a struct from form values via a type switch.
func fillFromForm(r *http.Request, dst interface{}) error {
	switch p := dst.(type) {
	case *offersRequest:
		p.DepartureAirport = r.FormValue("departureAirport")
		p.DestinationAirport = r.FormValue("destinationAirport")
		p.StartDate = r.FormValue("startDate")
		p.ReturnDate = r.FormValue("returnDate")
		p.TripType = r.FormValue("tripType")
		p.Stops, _ = strconv.Atoi(r.FormValue("stops"))
		p.Class = r.FormValue("class")
	case *priceGraphRequest:
		p.DepartureAirport = r.FormValue("departureAirport")
		p.DestinationAirport = r.FormValue("destinationAirport")
		p.StartDate = r.FormValue("startDate")
		p.ReturnDate = r.FormValue("returnDate")
		p.MinDays, _ = strconv.Atoi(r.FormValue("minDays"))
		p.MaxDays, _ = strconv.Atoi(r.FormValue("maxDays"))
		p.Stops, _ = strconv.Atoi(r.FormValue("stops"))
		p.Class = r.FormValue("class")
	case *urlRequest:
		p.DepartureAirport = r.FormValue("departureAirport")
		p.DestinationAirport = r.FormValue("destinationAirport")
		p.StartDate = r.FormValue("startDate")
		p.ReturnDate = r.FormValue("returnDate")
		p.TripType = r.FormValue("tripType")
		p.Stops, _ = strconv.Atoi(r.FormValue("stops"))
		p.Class = r.FormValue("class")
	default:
		return fmt.Errorf("unknown request type")
	}
	return nil
}
