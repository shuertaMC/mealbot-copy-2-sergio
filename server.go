package main

import (
	"fmt"
	"net/http"
	"os"

	log "github.com/sirupsen/logrus"
)

// Middleware class
type Middleware struct {
	MiddlewareHandlers [](func(handler http.Handler) http.Handler)
}

// Apply : Create a handler where the core handler is wrapped by middleware handlers
func (mw *Middleware) Apply(
	coreHandler func(w http.ResponseWriter, r *http.Request),
) http.Handler {
	handler := http.Handler(http.HandlerFunc(coreHandler))
	for _, nextHandler := range mw.MiddlewareHandlers {
		handler = nextHandler(handler)
	}

	return handler
}

// ApplyFake :
func (mw Middleware) ApplyFake(
	coreHandler func(w http.ResponseWriter, r *http.Request),
) http.Handler {
	return http.Handler(http.HandlerFunc(coreHandler))
}

func runTestSequence(testMode bool) {
	err := createOrganization("ysc", "johnamadeo.daniswara@yale.edu")
	if err != nil {
		fmt.Println(err)
	}

	_, err = createMembersFromCSV("ysc", "./csv/test_john3.csv")
	if err != nil {
		fmt.Println(err)
		return
	}

	i := 0
	for i < 2 {
		err = addRound("ysc", fmt.Sprintf("2019-01-02 %d:55:00", i))
		if err != nil {
			fmt.Println(err)
			return
		}

		// NOTE: Do you want to actually send out emails?
		err = runPairingRound("ysc", i, testMode)
		if err != nil {
			fmt.Println(err)
			return
		}

		i++
	}
}

// main is the program entry point. It supports two CLI sub-commands and a
// default HTTP server mode:
//
//   - "pair"    – Runs the pairing scheduler once in production mode
//     (test_mode=false). Pairs members within each organisation, persists
//     the results, and sends Mailgun notification emails.
//
//   - "migrate" – Runs the one-time migration that back-fills the
//     last_round_with field for every existing pair record.
//
// When invoked without arguments the process starts an HTTP server (default
// port 8080, overridable via the PORT environment variable). The server
// applies CORS and JWT-auth middleware to every route and serves the static
// front-end from ./static for all unmatched paths.
//
// Any unrecognised argument is printed to stdout and the process returns.
func main() {
	args := os.Args
	if len(args) == 2 {
		if args[1] == "pair" {
			// runTestSequence(true)
			err := runPairingScheduler(false)
			if err != nil {
				fmt.Println(err)
			}
			return
		} else if args[1] == "migrate" {
			err := migrateToLastRoundWithForPairing()
			if err != nil {
				fmt.Println(err)
			}
			return
		} else {
			fmt.Printf("argument '%s' not recognized", args[1])
			return
		}
	}

	mw := Middleware{
		MiddlewareHandlers: [](func(handler http.Handler) http.Handler){
			GetAuthHandler,
			GetCorsHandler,
		},
	}

	serveMux := http.NewServeMux()
	serveMux.Handle("/members", mw.Apply(MembersHandler))
	serveMux.Handle("/orgs", mw.Apply(GetOrganizationsHandler))
	serveMux.Handle("/org", mw.Apply(CreateOrganizationHandler))
	serveMux.Handle("/crossmatchtrait", mw.Apply(CrossMatchTraitHandler))
	serveMux.Handle("/rounds", mw.Apply(GetRoundsHandler))
	serveMux.Handle("/round", mw.Apply(RoundHandler))
	serveMux.Handle("/pairs", mw.Apply(GetPairsHandler))
	serveMux.Handle("/", http.FileServer(http.Dir("./static")))

	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	log.Fatal(http.ListenAndServe(":"+port, serveMux))
}
