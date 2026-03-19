package main

import (
	"bytes"
	"encoding/json"
	"io"
	"log"
	"net/http"
	"os"
)

// responseRecorder captures the response body so we can log a sample of it.
type responseRecorder struct {
	http.ResponseWriter
	buf *bytes.Buffer
}

func (rr *responseRecorder) Write(b []byte) (int, error) {
	rr.buf.Write(b)
	return rr.ResponseWriter.Write(b)
}

// loggingMiddleware logs the raw request body and a sample of the first 5
// elements of the JSON array response. Non-array responses are logged as-is.
func loggingMiddleware(route string, next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		// Read and restore the request body.
		body, err := io.ReadAll(r.Body)
		if err != nil {
			log.Printf("[%s] failed to read request body: %v", route, err)
		} else {
			r.Body = io.NopCloser(bytes.NewReader(body))
			log.Printf("[%s] request payload: %s", route, body)
		}

		// Wrap the ResponseWriter to capture the response.
		rec := &responseRecorder{ResponseWriter: w, buf: &bytes.Buffer{}}
		next(rec, r)

		// Try to parse the response as a JSON array and sample the first 5 elements.
		var items []json.RawMessage
		if err := json.Unmarshal(rec.buf.Bytes(), &items); err == nil {
			sample := items
			if len(sample) > 5 {
				sample = sample[:5]
			}
			b, _ := json.MarshalIndent(sample, "", "  ")
			log.Printf("[%s] response — total: %d, sample (first %d):\n%s", route, len(items), len(sample), b)
		} else {
			// Scalar response (e.g. getUrl returns an object, not an array).
			log.Printf("[%s] response: %s", route, rec.buf.String())
		}
	}
}

func main() {
	mux := http.NewServeMux()

	mux.HandleFunc("/getOffers", loggingMiddleware("getOffers", getOffersHandler))
	mux.HandleFunc("/getPriceGraph", loggingMiddleware("getPriceGraph", getPriceGraphHandler))
	mux.HandleFunc("/getUrl", loggingMiddleware("getUrl", getUrlHandler))

	mux.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte(`{"status":"ok"}`))
	})

	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	log.Printf("Server listening on :%s", port)
	if err := http.ListenAndServe(":"+port, mux); err != nil {
		log.Fatalf("Server failed: %v", err)
	}
}
