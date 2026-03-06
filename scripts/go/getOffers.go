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

type offersRequest struct {
	DepartureAirport   string `json:"departureAirport"`
	DestinationAirport string `json:"destinationAirport"`
	StartDate          string `json:"startDate"`
	ReturnDate         string `json:"returnDate"`
	TripType           string `json:"tripType"`
	Stops              int    `json:"stops"`
	Class              string `json:"class"`
}

func getOffersHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var req offersRequest
	if err := decodeRequest(r, &req); err != nil {
		http.Error(w, fmt.Sprintf("Error parsing parameters: %v", err), http.StatusBadRequest)
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
	tripType, err := parseTripType(req.TripType)
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	offers, err := fetchOffers(startDate, returnDate, req.DepartureAirport, req.DestinationAirport, stops, class, tripType)
	if err != nil {
		http.Error(w, fmt.Sprintf("Error fetching offers: %v", err), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(offers)
}

func fetchOffers(startDate, returnDate time.Time, src, dst string, stops flights.Stops, class flights.Class, tripType flights.TripType) ([]flights.FullOffer, error) {
	session, err := flights.New()
	if err != nil {
		return nil, err
	}

	offers, _, err := session.GetOffers(
		context.Background(),
		flights.Args{
			Date:        startDate,
			ReturnDate:  returnDate,
			SrcAirports: []string{src},
			DstAirports: []string{dst},
			Options: flights.Options{
				Travelers: flights.Travelers{Adults: 1},
				Stops:     stops,
				Class:     class,
				TripType:  tripType,
				Currency:  currency.EUR,
			},
		},
	)
	return offers, err
}
