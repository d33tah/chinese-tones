package main

import (
	"html/template"
	"log"
	"net/http"
	"os"
)

func Home() http.HandlerFunc {
	tpl, err := template.New("main").ParseGlob(`templates/*.html`)
	if err != nil {
		log.Fatal(err)
	}

	m := map[string]interface{}{
		"path":                        "/sounds/jie2.ogg",
		"answer":                      "Welcome to Chinese Tones",
		"placeholder":                 "?",
		"pinyin_without_tones":        []string{"jie"},
		"pinyin_without_tones_length": 1,
		"score":                       0,
		"num_questions":               0,
		"perc":                        "0%",
		"tones": map[string]string{
			"1": "flat",
			"2": "rising",
			"3": "dipping",
			"4": "falling",
			"5": "neutral",
		},
	}
	return func(w http.ResponseWriter, r *http.Request) {
		err = tpl.ExecuteTemplate(w, "main.html", m)
		if err != nil {
			log.Println("Can’t load template", err)
		}
	}
}

func main() {
	logger := log.New(os.Stdout, "rentweb: ", log.LstdFlags)

	fs := http.FileServer(http.Dir("./sounds"))
	http.Handle("/sounds/", http.StripPrefix("/sounds/", fs))
	http.HandleFunc("/", Home())

	log.Println("Starting")
	logger.Fatal(http.ListenAndServe(":2137", nil))
}
