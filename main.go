package main

import (
	"html/template"
	"log"
	"net/http"
)

type response struct {
	Path                        string
	Answer                      string
	Placeholder                 string
	Pinyin_without_tones        []string
	Pinyin_without_tones_length int
	Score                       int
	Num_questions               int
	Perc                        string
	Tones                       map[string]string
}

func home() http.HandlerFunc {
	tpl := template.Must(template.New("main").ParseGlob(`templates/*.html`))

	m := response{
		Path:                        "/sounds/jie2.ogg",
		Answer:                      "Welcome to Chinese Tones",
		Placeholder:                 "?",
		Pinyin_without_tones:        []string{"jie"},
		Pinyin_without_tones_length: 1,
		Score:                       0,
		Num_questions:               0,
		Perc:                        "0%",
		Tones: map[string]string{
			"1": "flat",
			"2": "rising",
			"3": "dipping",
			"4": "falling",
			"5": "neutral",
		},
	}
	return func(w http.ResponseWriter, r *http.Request) {
		err := tpl.ExecuteTemplate(w, "main.html", m)
		if err != nil {
			log.Println("Can’t load template", err)
		}
	}
}

func main() {
	fs := http.FileServer(http.Dir("./sounds"))
	http.Handle("/sounds/", http.StripPrefix("/sounds/", fs))
	http.HandleFunc("/", home())

	log.Println("Starting")
	log.Fatal(http.ListenAndServe(":2137", nil))
}
