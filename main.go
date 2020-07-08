package main

import (
	"html/template"
	"log"
	"net/http"
	"os"

	"github.com/gorilla/mux"
)

func Home() http.HandlerFunc {
	tpl, err := template.New("main").ParseGlob(`templates/*.html`)
	if err != nil {
		logger := log.New(os.Stdout, "rentweb: ", log.LstdFlags)
		logger.Fatal(err)
	}

    m := map[string]string{
        "answer": "hello",
    }
	return func(w http.ResponseWriter, r *http.Request) {
		tpl.ExecuteTemplate(w, "main.html", m)
	}
}

func main() {
	logger := log.New(os.Stdout, "rentweb: ", log.LstdFlags)
	r := mux.NewRouter()
	r.HandleFunc("/", Home())
	logger.Fatal(http.ListenAndServe(":2137", r))
}
