pipeline {
  agent any

  environment {
    TF_IN_AUTOMATION = "true"
    TF_INPUT         = "false"
    LINODE_TOKEN     = credentials('LINODE_TOKEN')
    ANSIBLE_HOST_KEY_CHECKING = "False"
  }

  stages {

    stage('Checkout') {
      steps {
        checkout scm
      }
    }

    stage('Terraform Init') {
      steps {
        dir('terraform') {
          sh '''
            terraform init \
              -backend=true \
              -upgrade
          '''
        }
      }
    }

    stage('Terraform Validate') {
      steps {
        dir('terraform') {
          sh 'terraform validate'
        }
      }
    }

    stage('Terraform Plan') {
      steps {
        dir('terraform') {
          sh '''
            terraform plan
          '''
        }
      }
    }

    stage('Terraform Apply') {
      steps {
        dir('terraform') {
          sh 'terraform apply -auto-approve'
        }
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
      steps {
        withCredentials([
          sshUserPrivateKey(
            credentialsId: 'ANSIBLE_SSH_KEY',
            keyFileVariable: 'SSH_KEY'
          )
        ]) {
          sh '''
            ansible-playbook \
              -i ansible/inventory.ini \
              ansible/site.yml \
              --private-key "$SSH_KEY" \
              -u root
          '''
        }
      }
    }
  }

  post {
    success {
      echo 'Infrastructure provisioned and configured successfully. Value delivered.'
    }
    failure {
      echo 'Pipeline failed. Root cause analysis required.'
    }
  }
}
