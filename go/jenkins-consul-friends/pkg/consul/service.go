package consul

import (
	"log"
	"time"

	"github.com/hashicorp/consul/api"
)

// ServiceRegister is used to register a new service with
// the local agent
func (c *Client) ServiceRegister() {
	log.Println("register service ", c.ServiceName)
	agent := c.Agent()
	serviceDef := &api.AgentServiceRegistration{
		Name: c.ServiceName,
		Check: &api.AgentServiceCheck{
			TTL:                            c.ServiceHealthTTL.String(),
			DeregisterCriticalServiceAfter: c.ServiceHealthTTL.String(),
		},
	}
	err := agent.ServiceRegisterOpts(serviceDef, api.ServiceRegisterOpts{
		ReplaceExistingChecks: true,
	})
	if err != nil {
		panic(err)
	}
}

// ServiceHealthLoop runs loop pushing health beats
func (c *Client) ServiceHealthLoop() {
	ticker := time.NewTicker(c.ServiceHealthTTL / 2)
	for range ticker.C {
		c.ServiceUpdateState()
	}
}

// ServiceUpdateState updates health checker
func (c *Client) ServiceUpdateState() {
	log.Println("push health beat")
	if agentErr := c.Agent().PassTTL("service:"+c.ServiceName, ""); agentErr != nil {
		panic(agentErr)
	}
}

// ServiceDeregister
func (c *Client) ServiceDeregister() {
	log.Println("deregister service")
	c.Agent().ServiceDeregister(c.ServiceName)
}
