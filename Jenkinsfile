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

    stage('Generate Terraform Import Commands') {
        steps {
            script {
            echo "Generating Terraform import commands for local Terraform configuration..."

            // Get VM IDs and names from Terraform outputs
            def vm_ids = sh(
                script: "terraform -chdir=terraform output -json instance_ids",
                returnStdout: true
            ).trim()

            // Convert JSON array to list
            def parsed = readJSON text: vm_ids

            parsed.eachWithIndex { id, idx ->
                def resource_name = "linode_instance.private[${idx}]"
                echo "terraform import ${resource_name} ${id}"
            }

            // Gateway VM import
            def gateway_id = sh(
                script: "terraform -chdir=terraform output -raw gateway_id",
                returnStdout: true
            ).trim()
            echo "terraform import linode_instance.gateway ${gateway_id}"
            }
        }
    }

    stage('Reapply SSH keys') {
        when {
            expression {
                // Optional: trigger only if commit message contains [INFRA]
                currentBuild.changeSets.any { cs ->
                    cs.items.any { it.msg.contains("[INFRA]") }
                }
            }
        }
        steps {
            script {
                // List of all instance IPs from Terraform output
                def ips = sh(script: 'terraform -chdir=terraform output -raw instance_ips', returnStdout: true).trim().split()

                for (ip in ips) {
                    sh "ssh-keyscan -H ${ip} >> /var/lib/jenkins/.ssh/known_hosts"
                }

                sh "chown -R jenkins:jenkins /var/lib/jenkins/.ssh/"
            }
        }
    }



    // stage('Prepare SSH known_hosts') {
    //   steps {
    //     sh '''
    //       mkdir -p ~/.ssh
    //       touch ~/.ssh/known_hosts

    //       for ip in $(terraform -chdir=terraform output -raw instance_ips); do
    //         ssh-keygen -f ~/.ssh/known_hosts -R "$ip" || true
    //       done
    //     '''
    //   }
    // }

    stage('Update Ansible Inventory') {
        steps {
            script {
            // Get the gateway public IP from Terraform output
            def gateway_ip = sh(
                script: "terraform -chdir=terraform output -raw gateway_public_ip",
                returnStdout: true
            ).trim()

            echo "Gateway IP is ${gateway_ip}"

            // Update hosts.ini dynamically
            sh """
                sed -i '/\\[gateway\\]/,+1 s/ansible_host=.*/ansible_host=${gateway_ip}/' ansible/hosts.ini
                sed -i "/\\[private:vars\\]/,+1 s/ProxyJump=root@.*/ProxyJump=root@${gateway_ip}/" ansible/hosts.ini
            """
            }
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
              -u root -vv \
              --ssh-extra-args="-o UserKnownHostsFile=/var/lib/jenkins/.ssh/known_hosts"
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
