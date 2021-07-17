pipeline {
  agent { label 'localhost' }
  parameters {
    string(name: 'image_tag', description: 'docker image tag')
  }

  stages {
    stage('Build') {
      steps {
        echo "Deploy started for Docker image tag:${params.image_tag}"
        sh 'docker stop jenkins-consul-friends || echo No such container: jenkins-consul-friends'
        sh 'docker run --rm -d -e CONSUL_HTTP_ADDR=jenkins_consul_friends_consul_client:8500 ' +
          '-p 9003:9003 --network jenkins-consul-friends --name jenkins-consul-friends ' +
          'jenkins-consul-friends:' + params.image_tag
      }
    }
  }
}
