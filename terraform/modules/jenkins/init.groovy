import com.cloudbees.hudson.plugins.folder.*
import com.cloudbees.hudson.plugins.folder.computed.PeriodicFolderTrigger
import hudson.util.PersistedList
import jenkins.branch.*
import jenkins.branch.buildstrategies.basic.*
import jenkins.model.Jenkins
import jenkins.plugins.git.*
import jenkins.plugins.git.traits.*
import org.jenkinsci.plugins.workflow.multibranch.*

instance = Jenkins.instance

def createMultibranchScm(folder, name, repo, credentialsId, jobScript) {
  WorkflowMultiBranchProject job
  item = folder.getItem(name)
  if ( item != null ) {
    return item
  }
  job = folder.createProject(WorkflowMultiBranchProject, name)

  job.projectFactory.scriptPath = jobScript

  // Add git repo
  String id = null
  String remote = repo
  String includes = '*'
  String excludes = ''
  boolean ignoreOnPushNotifications = false
  GitSCMSource gitSCMSource = new GitSCMSource(id, remote, credentialsId, includes, excludes, ignoreOnPushNotifications)
  gitSCMSource.traits.add(new CleanBeforeCheckoutTrait())
  gitSCMSource.traits.add(new CleanAfterCheckoutTrait())
  gitSCMSource.traits.add(new LocalBranchTrait())
  BranchSource branchSource = new BranchSource(gitSCMSource)

  PersistedList sources = job.sourcesList
  sources.clear()
  sources.add(branchSource)
  job
}

if (instance.getItem('JenkinsConsulFriends') == null) {
  println('=== Initialize the JenkinsConsulFriends folder')
  def folder = instance.createProject(Folder, 'JenkinsConsulFriends')
  folder.description = 'Jenkins & Consul & Friends jobs'

  ci_job = createMultibranchScm(folder, 'CI',
    'https://github.com/ezh/jenkins-consul-friends.git', null, 'ci.Jenkinsfile')
  ci_job.description = 'Build Jenkins & Consul & Friends microservice'
  ci_job.displayName = 'JenkinsConsulFriends CI'
  ci_job.with {
    newInterval = new PeriodicFolderTrigger('1m')
    addTrigger(newInterval)
    sourcesList.each {
      namedBranch = new NamedBranchBuildStrategyImpl([
              new NamedBranchBuildStrategyImpl.ExactNameFilter('main', false)
            ])
      strategyList = [namedBranch] as List<BranchBuildStrategy>
      it.setBuildStrategies(strategyList)
    }
  }
  ci_job.save()

  cd_job = createMultibranchScm(folder, 'CD',
    'https://github.com/ezh/jenkins-consul-friends.git', null, 'cd.Jenkinsfile')
  cd_job.description = 'Deploy Jenkins & Consul & Friends microservice'
  cd_job.displayName = 'JenkinsConsulFriends CD'
  cd_job.save()
}

instance.save()
