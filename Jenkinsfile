pipeline {
    agent any

    environment {
        TF_IN_AUTOMATION           = "true"
        TF_INPUT                    = "false"
        ANSIBLE_HOST_KEY_CHECKING   = "False"
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
            when {
                expression {
                    currentBuild.changeSets.any { cs ->
                        cs.items.any { it.msg.contains("[INFRA]") }
                    }
                }
            }
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
                    sleep 10
                '''
            }
        }

        stage('Update Dynamic Inventory') {
            steps {
                script {
                    // generate JSON inventory from Terraform outputs
                    sh '''
                        cd ansible/inventory
                        chmod +x dynamic_inventory.py
                        python3 dynamic_inventory.py > dynamic_inventory.json
                    '''
                }
            }
        }

        stage('Add Proxy to known_hosts') {
            steps {
                script {
                    // extract proxy IP
                    def proxy_ip = sh(script: "jq -r '.proxy.hosts[0]' ansible/dynamic_inventory.json", returnStdout: true).trim()

                    // add proxy IP to known_hosts
                    sh """
                        ssh-keyscan -H ${proxy_ip} >> /var/lib/jenkins/.ssh/known_hosts || true
                        chown jenkins:jenkins /var/lib/jenkins/.ssh/known_hosts
                    """
                }
            }
        }

        stage('Add Private Nodes to known_hosts') {
            steps {
                script {
                    // Get private IPs from dynamic inventory
                    def private_ips = sh(
                        script: "jq -r '.private.hosts[]' ansible/dynamic_inventory.json",
                        returnStdout: true
                    ).trim().split('\\n')

                    for (ip in private_ips) {
                        // Remove previous entry if exists
                        sh "ssh-keygen -R ${ip} || true"

                        // Add the current key using ProxyJump
                        sh "ssh-keyscan -o ProxyJump=deploy@${proxy_ip} -o StrictHostKeyChecking=no -H ${ip} >> /var/lib/jenkins/.ssh/known_hosts || true"
                    }

                    // Ensure correct permissions
                    sh "chown jenkins:jenkins /var/lib/jenkins/.ssh/known_hosts"
                }
            }
        }


        stage('Run Ansible Playbooks') {
            steps {
                withCredentials([
                    sshUserPrivateKey(
                        credentialsId: 'ANSIBLE_SSH_KEY',
                        keyFileVariable: 'ANSIBLE_PRIVATE_KEY',
                        usernameVariable: 'ANSIBLE_USER'
                    ),
                    file(
                        credentialsId: 'ansible_ssh_pub_key',
                        variable: 'ANSIBLE_PUB_KEY_FILE'
                    )
                ]) {
                    sh '''
                        SSH_KEY_CONTENT=$(cat "$ANSIBLE_PUB_KEY_FILE")
                        ansible-playbook ansible/playbook.yaml \
                            -i ansible/inventory/dynamic_inventory.py \
                            -u "$ANSIBLE_USER" \
                            --private-key "$ANSIBLE_PRIVATE_KEY" \
                            -e "ssh_pub_key=\\"$SSH_KEY_CONTENT\\"" \
                            -vv
                    '''
                }
            }
        }
    }

    post {
        success {
            echo 'Infrastructure provisioned and configured successfully.'
        }
        failure {
            echo 'Pipeline failed. Inspect Terraform or Ansible stage logs.'
        }
    }
}
