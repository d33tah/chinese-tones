package main

import (
	"encoding/gob"
	"github.com/gorilla/sessions"
	"html/template"
	"io/ioutil"
	"log"
	"math/rand"
	"net/http"
	"regexp"
	"strconv"
	"strings"
)

type response struct {
	Path                     string
	Answer                   string
	Placeholder              string
	PinyinWithoutTones       []string
	PinyinWithoutTonesLength int
	Score                    int
	NumQuestions             int
	Perc                     string
	Tones                    map[string]string
}

type sound struct {
	Path               string
	PinyinWithoutTones []string
	CorrectTones       string
}

var (
	key    = []byte("super-secret-key")
	store  = sessions.NewCookieStore(key)
	sounds = readSounds()
)

func delete_empty(s []string) []string {
	var r []string
	for _, str := range s {
		if str != "" {
			r = append(r, str)
		}
	}
	return r
}

func readSounds() []sound {
	var ret []sound
	files, err := ioutil.ReadDir("sounds")
	if err != nil {
		log.Fatal(err)
	}
	re_not_digit := regexp.MustCompile("[^0-9]")
	re_digit := regexp.MustCompile("[0-9_]")
	for _, f := range files {
		filename_without_extension := strings.Split(f.Name(), ".")[0]
		ret = append(ret, sound{
			Path:               f.Name(),
			PinyinWithoutTones: delete_empty(re_digit.Split(filename_without_extension, -1)),
			CorrectTones:       re_not_digit.ReplaceAllString(f.Name(), ""),
		})
	}
	log.Println(ret)
	return ret
}

func extractAnswer(r *http.Request) string {
	r.ParseForm()
	answerNo := 0
	enteredAnswer := ""
	for {
		wasResponseFound := false
		for i := 1; i < 6; i++ {
			key := "answer-" + strconv.Itoa(answerNo) + "-" + strconv.Itoa(i)
			value := r.Form.Get(key)
			if value != "" {
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

	score, ok := session.Values["score"].(int)
	if !ok {
		score = 0
	}

	enteredAnswer := extractAnswer(r)

	val := session.Values["previous_sound"]
	var previous_sound = &sound{}
	previous_sound, ok = val.(*sound)

	log.Println(previous_sound)
	answer := "Welcome to Chinese Tones"
	if ok {
		was_correct := previous_sound.CorrectTones == enteredAnswer
		if was_correct {
			score += 1
			answer = "Correct!"
		} else {
			answer = "Incorrect. You answered " + enteredAnswer + ", but the correct answer was " + previous_sound.CorrectTones
		}
	}
	randomIndex := rand.Intn(len(sounds))
	sound := sounds[randomIndex]

	m := response{
		Path:                     "/sounds/" + sound.Path,
		Answer:                   answer,
		Placeholder:              "?",
		PinyinWithoutTones:       sound.PinyinWithoutTones,
		PinyinWithoutTonesLength: 1,
		Score:                    0,
		NumQuestions:             num_questions,
		Perc:                     "0%",
		Tones: map[string]string{
			"1": "flat",
			"2": "rising",
			"3": "dipping",
			"4": "falling",
			"5": "neutral",
		},
	}

	session.Values["sound"] = sound
	session.Values["score"] = score
	session.Values["num_questions"] = num_questions + 1
	session.Save(r, w)

	log.Println(enteredAnswer)
	err := tpl.ExecuteTemplate(w, "main.html", m)
	if err != nil {
		log.Println("Can’t load template", err)
	}
}

func main() {
	fs := http.FileServer(http.Dir("./sounds"))
	gob.Register(&sound{})
	http.Handle("/sounds/", http.StripPrefix("/sounds/", fs))
	http.HandleFunc("/", home)

	log.Println("Starting")
	log.Fatal(http.ListenAndServe(":2137", nil))
}
