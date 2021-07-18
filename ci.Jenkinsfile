pipeline {
  agent { label 'localhost' }

  stages {
    stage('Build') {
      steps {
        script {
          COMMIT = GIT_COMMIT.substring(0, 7)
          COMMIT_MESSAGE = sh(script: "git show -s --pretty='%s'", returnStdout: true).trim()
        }
        echo "Build started for commit ${COMMIT} '${COMMIT_MESSAGE}'"
        sh "docker build -t jenkins-consul-friends:${COMMIT}-${env.BUILD_NUMBER} ."
      }
    }
    stage('Trigger CD') {
      steps {
        build(job: 'JenkinsConsulFriends/JenkinsConsulFriends CD', wait: false,
          parameters: [string(name: 'image_tag', value: "${COMMIT}-${env.BUILD_NUMBER}")])
      }
    }
  }
}
