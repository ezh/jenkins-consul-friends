package main

import (
	"fmt"
	"log"
	"net/http"
	"time"

	"github.com/ezh/jenkins-consul-friends/pkg/consul"
	"github.com/hashicorp/consul/api"
)

func get(consul *consul.Client) func(w http.ResponseWriter, r *http.Request) {
	return func(w http.ResponseWriter, r *http.Request) {
		for key := range r.URL.Query() {
			kv, _, err := consul.KV().Get(key, nil)
			if err != nil {
				panic(err)
			}
			if kv == nil {
				log.Println(key, "not found")
				fmt.Fprintf(w, "%s not found\n", key)
			} else {
				log.Println("get", key, "=", string(kv.Value))
				fmt.Fprintf(w, "%s\n", string(kv.Value))
			}
		}
	}
}

func set(consul *consul.Client) func(w http.ResponseWriter, r *http.Request) {
	return func(w http.ResponseWriter, r *http.Request) {
		values := r.URL.Query()
		for key := range values {
			kv := &api.KVPair{
				Key:   key,
				Value: []byte(values[key][0]),
			}
			_, err := consul.KV().Put(kv, nil)
			if err != nil {
				panic(err)
			}
			log.Println("set", key, "=", values[key][0])
		}
		fmt.Fprintf(w, "Success\n")
	}
}

func ping(w http.ResponseWriter, r *http.Request) {
	fmt.Fprintf(w, "pong\n")
}

func main() {
	consul := consul.New("jenkins-consul-friends", time.Second*5)
	consul.ServiceRegister()
	defer consul.ServiceDeregister()
	go consul.ServiceHealthLoop()
	http.HandleFunc("/get-value", get(consul))
	http.HandleFunc("/set-value", set(consul))
	http.HandleFunc("/ping", ping)
	log.Fatal(http.ListenAndServe(":9003", nil))
}
