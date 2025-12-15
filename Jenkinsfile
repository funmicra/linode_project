pipeline {
  agent any

  environment {
    TF_IN_AUTOMATION = "true"
    TF_INPUT        = "false"
    ANSIBLE_HOST_KEY_CHECKING = "False"
  }

  stages {

    stage('Checkout') {
      steps {
        git(
          url: 'https://github.com/funmicra/linode_project.git',
          branch: 'master'
        )
      }
    }

    stage('Terraform Apply') {
      environment {
        TF_VAR_linode_token  = credentials('LINODE_TOKEN')
        TF_VAR_ssh_keys_file = "${WORKSPACE}/terraform/ssh.keys"
      }
      steps {
        sh '''
          cd terraform
          terraform init
          terraform plan
          terraform apply -auto-approve
        '''
      }
    }

    stage('Prepare SSH known_hosts') {
      steps {
        sh '''
          mkdir -p ~/.ssh
          touch ~/.ssh/known_hosts

          for ip in $(terraform -chdir=terraform output -raw instance_ips); do
            ssh-keygen -f ~/.ssh/known_hosts -R "$ip" || true
          done
        '''
      }
    }

    stage('Ansible Configure') {
      environment {
        ANSIBLE_HOST_KEY_CHECKING = "False"
      }
      steps {
        withCredentials([
          sshUserPrivateKey(
            credentialsId: 'ANSIBLE_SSH_KEY',
            keyFileVariable: 'SSH_KEY'
          )
        ]) {
          sh '''
            ansible-playbook \
              -i ansible/hosts.ini \
              ansible/playbook.yaml \
              --private-key "$SSH_KEY" \
              -u root
          '''
        }
      }
    }
  }

  post {
    success {
      echo 'Infrastructure provisioned and configured successfully. End-to-end delivery complete.'
    }
    failure {
      echo 'Pipeline failed. Inspect Terraform or Ansible stage logs.'
    }
  }
}
