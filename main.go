package main

import (
	"github.com/gorilla/sessions"
	"html/template"
	"log"
	"net/http"
	"strconv"
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

var (
	key   = []byte("super-secret-key")
	store = sessions.NewCookieStore(key)
)

func extractAnswer(r *http.Request) string {
	r.ParseForm()
	answerNo := 0
	enteredAnswer := ""
	for {
		wasResponseFound := false
		for i := 1; i < 6; i++ {
			key := "answer-" + strconv.Itoa(answerNo) + "-" + strconv.Itoa(i)
			wartosc := r.Form.Get(key)
			if wartosc != "" {
				wasResponseFound = true
				enteredAnswer += strconv.Itoa(i)
			}
		}
		if !wasResponseFound {
			break
		}
		answerNo += 1
	}
	return enteredAnswer
}

func home(w http.ResponseWriter, r *http.Request) {
	tpl := template.Must(template.New("main").ParseGlob(`templates/*.html`))
	session, _ := store.Get(r, "cookie-name")

	num_questions, ok := session.Values["num_questions"].(int)
	if !ok {
		num_questions = 0
	}

	m := response{
		Path:                        "/sounds/jie2.ogg",
		Answer:                      "Welcome to Chinese Tones",
		Placeholder:                 "?",
		Pinyin_without_tones:        []string{"jie"},
		Pinyin_without_tones_length: 1,
		Score:                       0,
		Num_questions:               num_questions,
		Perc:                        "0%",
		Tones: map[string]string{
			"1": "flat",
			"2": "rising",
			"3": "dipping",
			"4": "falling",
			"5": "neutral",
		},
	}

	session.Values["num_questions"] = num_questions + 1
	session.Save(r, w)

	enteredAnswer := extractAnswer(r)
	log.Println(enteredAnswer)
	err := tpl.ExecuteTemplate(w, "main.html", m)
	if err != nil {
		log.Println("Can’t load template", err)
	}
}

func main() {
	fs := http.FileServer(http.Dir("./sounds"))
	http.Handle("/sounds/", http.StripPrefix("/sounds/", fs))
	http.HandleFunc("/", home)

	log.Println("Starting")
	log.Fatal(http.ListenAndServe(":2137", nil))
}
