package consul

import (
	"time"

	"github.com/hashicorp/consul/api"
)

type Client struct {
	*api.Client
	ServiceName      string
	ServiceHealthTTL time.Duration
}

func New(name string, ttl time.Duration) *Client {
	var err error

	newClient := Client{
		ServiceName:      name,
		ServiceHealthTTL: ttl,
	}
	newClient.Client, err = api.NewClient(api.DefaultConfig())
	if err != nil {
		panic(err)
	}
	return &newClient
}
