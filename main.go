package main

import (
	"encoding/gob"
	"fmt"
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
	Message                  string
	PinyinWithoutTones       []string
	PinyinWithoutTonesLength int
	Score                    int
	NumQuestions             int
	Perc                     string
	ToneNames                map[string]string
}

type sound struct {
	Path               string
	PinyinWithoutTones []string
	CorrectTones       string
}

var (
	key       = []byte("super-secret-key")
	store     = sessions.NewCookieStore(key)
	sounds    = readSounds()
	toneNames = map[string]string{
		"1": "flat",
		"2": "rising",
		"3": "dipping",
		"4": "falling",
		"5": "neutral",
	}
)

func deleteEmpty(s []string) []string {
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
	reNotDigit := regexp.MustCompile("[^0-9]")
	reDigit := regexp.MustCompile("[0-9_]")
	for _, f := range files {
		filenameWithoutExtension := strings.Split(f.Name(), ".")[0]
		ret = append(ret, sound{
			Path: f.Name(),
			// convert e.g. jie2guo3 into ["jie", "guo"]
			PinyinWithoutTones: deleteEmpty(
				reDigit.Split(
					filenameWithoutExtension, -1)),
			// jie2guo3.ogg becomes 23
			CorrectTones: reNotDigit.ReplaceAllString(f.Name(), ""),
		})
	}
	return ret
}

func extractAnswer(r *http.Request) string {
	r.ParseForm()
	answerNo := 0
	enteredAnswer := ""
	for {
		wasResponseFound := false
		for i := 1; i < 6; i++ {
			key := "message-" + strconv.Itoa(answerNo) + "-" + strconv.Itoa(i)
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

	numQuestions, ok := session.Values["numQuestions"].(int)
	if !ok {
		numQuestions = 0
	}

	score, ok := session.Values["score"].(int)
	if !ok {
		score = 0
	}

	enteredAnswer := extractAnswer(r)

	val := session.Values["sound"]
	var previousSound = &sound{}
	previousSound, ok = val.(*sound)

	message := "Welcome to Chinese Tones"
	if ok {
		if previousSound.CorrectTones == enteredAnswer {
			score += 1
			message = "Correct!"
		} else {
			message = fmt.Sprintf(
				"Incorrect. You messageed %s,"+
					" but the correct message was %s",
				enteredAnswer,
				previousSound.CorrectTones)
		}
	}

	randomIndex := rand.Intn(len(sounds))
	sound := sounds[randomIndex]
	perc := fmt.Sprintf("%.02f%%", 100.0*float64(score)/float64(numQuestions))
	m := response{
		Path:                     "/sounds/" + sound.Path,
		Message:                  message,
		PinyinWithoutTones:       sound.PinyinWithoutTones,
		PinyinWithoutTonesLength: 1,
		Score:                    score,
		NumQuestions:             numQuestions,
		Perc:                     perc,
		ToneNames:                toneNames,
	}

	session.Values["sound"] = sound
	session.Values["score"] = score
	session.Values["numQuestions"] = numQuestions + 1
	session.Save(r, w)

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
