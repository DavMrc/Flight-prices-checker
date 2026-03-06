package main

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"github.com/krisukox/google-flights-api/flights"
	"golang.org/x/text/currency"
)

type priceGraphRequest struct {
	DepartureAirport   string `json:"departureAirport"`
	DestinationAirport string `json:"destinationAirport"`
	StartDate          string `json:"startDate"`
	ReturnDate         string `json:"returnDate"`
	MinDays            int    `json:"minDays"`
	MaxDays            int    `json:"maxDays"`
	Stops              int    `json:"stops"`
	Class              string `json:"class"`
}

func getPriceGraphHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var req priceGraphRequest
	if err := decodeRequest(r, &req); err != nil {
		http.Error(w, fmt.Sprintf("Error parsing parameters: %v", err), http.StatusBadRequest)
		return
	}

	if req.DepartureAirport == "" || req.DestinationAirport == "" || req.StartDate == "" || req.ReturnDate == "" {
		http.Error(w, "missing required parameters", http.StatusBadRequest)
		return
	}
	if req.MinDays <= 0 || req.MaxDays <= 0 {
		http.Error(w, "minDays and maxDays must be positive integers", http.StatusBadRequest)
		return
	}
	if req.MinDays > req.MaxDays {
		http.Error(w, "minDays must be less than or equal to maxDays", http.StatusBadRequest)
		return
	}

	startDate, err := parseDate(req.StartDate)
	if err != nil {
		http.Error(w, fmt.Sprintf("Invalid startDate: %v", err), http.StatusBadRequest)
		return
	}
	returnDate, err := parseDate(req.ReturnDate)
	if err != nil {
		http.Error(w, fmt.Sprintf("Invalid returnDate: %v", err), http.StatusBadRequest)
		return
	}
	if returnDate.Before(startDate) {
		http.Error(w, fmt.Sprintf("returnDate %s is before startDate %s", req.ReturnDate, req.StartDate), http.StatusBadRequest)
		return
	}
	if startDate.AddDate(0, 0, req.MinDays).After(returnDate) {
		http.Error(w, "startDate + minDays comes after returnDate", http.StatusBadRequest)
		return
	}
	if startDate.AddDate(0, 0, req.MaxDays).After(returnDate) {
		http.Error(w, "startDate + maxDays comes after returnDate", http.StatusBadRequest)
		return
	}

	stops, err := parseStops(req.Stops)
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	class, err := parseClass(req.Class)
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	offers, err := fetchPriceGraph(startDate, returnDate, req.DepartureAirport, req.DestinationAirport, req.MinDays, req.MaxDays, stops, class)
	if err != nil {
		http.Error(w, fmt.Sprintf("Error fetching price graph: %v", err), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(offers)
}

func fetchPriceGraph(startDate, returnDate time.Time, src, dst string, minDays, maxDays int, stops flights.Stops, class flights.Class) ([]flights.Offer, error) {
	session, err := flights.New()
	if err != nil {
		return nil, err
	}

	opts := flights.Options{
		Travelers: flights.Travelers{Adults: 1},
		Stops:     stops,
		Class:     class,
		TripType:  flights.RoundTrip,
		Currency:  currency.EUR,
	}

	var allOffers []flights.Offer
	for tripLength := minDays; tripLength <= maxDays; tripLength++ {
		for d := startDate; !d.AddDate(0, 0, tripLength).After(returnDate); d = d.AddDate(0, 0, 1) {
			offers, err := session.GetPriceGraph(
				context.Background(),
				flights.PriceGraphArgs{
					RangeStartDate: d,
					RangeEndDate:   d.AddDate(0, 0, tripLength),
					TripLength:     tripLength,
					SrcAirports:    []string{src},
					DstAirports:    []string{dst},
					Options:        opts,
				},
			)
			if err != nil {
				return nil, err
			}
			for _, o := range offers {
				if o.Price > 0 {
					allOffers = append(allOffers, o)
				}
			}
		}
	}

	return allOffers, nil
}
