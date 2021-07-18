pipelineJob('JenkinsConsulFriends/JenkinsConsulFriends CD') {
  description 'Deployment job for devops-webapp-demo'
  parameters {
    stringParam('image_tag', '')
  }
  definition {
    cpsScm {
      scm {
        git {
          remote {
            url('https://github.com/ezh/jenkins-consul-friends.git')
          }
          branch('*/main')
        }
        scriptPath('cd.Jenkinsfile')
      }
      lightweight()
    }
  }
}
