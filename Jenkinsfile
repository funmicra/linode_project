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
                TF_VAR_ssh_keys_file = "${WORKSPACE}/terraform/ssh_key.b64"
                TF_VAR_user_password = credentials('LINODE_USER_PASSWORD')
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
                    sh '''
                        cd ansible/inventory
                        python3 dynamic_inventory.py 
                    '''
                }
            }
        }



        stage('Add Proxy to known_hosts') {
            steps {
                script {
                    // extract proxy IP
                    def proxy_ip = sh(script: "jq -r '.proxy.hosts[0]' ansible/inventory/dynamic_inventory.json", returnStdout: true).trim()

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
                    // Get the proxy IP inside this block
                    def proxy_ip = sh(
                        script: "jq -r '.proxy.hosts[0]' ansible/inventory/dynamic_inventory.json",
                        returnStdout: true
                    ).trim()

                    // Get private IPs
                    def private_ips = sh(
                        script: "jq -r '.private.hosts[]' ansible/inventory/dynamic_inventory.json",
                        returnStdout: true
                    ).trim().split('\\n')

                    for (ip in private_ips) {
                        // Remove old entry
                        sh "ssh-keygen -R ${ip} || true"

                        // Add key with ProxyJump
                        sh "ssh-keyscan -o ProxyJump=funmicra@${proxy_ip} -H ${ip} >> /var/lib/jenkins/.ssh/known_hosts || true"
                    }

                    // Fix permissions
                    sh "chown jenkins:jenkins /var/lib/jenkins/.ssh/known_hosts"
                }
            }
        }

        stage('Run Ansible Playbooks') {
            steps {
                withCredentials([
                    sshUserPrivateKey(
                        credentialsId: 'ANSIBLE_PRIVATE_KEY',
                        keyFileVariable: 'ANSIBLE_PRIVATE_KEY',
                        usernameVariable: 'ANSIBLE_USER'
                    )
                ]) {
                    sh '''
                        set -e

                        # Start SSH agent
                        eval "$(ssh-agent -s)"

                        # Add private key
                        ssh-add "$ANSIBLE_PRIVATE_KEY"

                        # Read proxy IP from inventory
                        PROXY_IP=$(awk '/\\[proxy\\]/ {getline; print}' ansible/inventory/hosts.ini | tr -d '"')

                        # Add proxy to known_hosts (avoid SSH prompt)
                        ssh-keyscan -H "$PROXY_IP" >> /var/lib/jenkins/.ssh/known_hosts || true

                        # Run playbook with ProxyJump using the same private key
                        ansible-playbook ansible/site.yaml \
                            -i ansible/inventory/hosts.ini \
                            -u "$ANSIBLE_USER" \
                            -vv
                    '''
                }
            }
        }



        stage('Announce Terraform Import Commands') {
            steps {
                script {
                    def instance_ids = readJSON(text: sh(script: "terraform -chdir=terraform output -json instance_ids", returnStdout: true).trim())
                    def proxy_id = sh(script: "terraform -chdir=terraform output -raw proxy_id", returnStdout: true).trim()
                    def vpc_id = sh(script: "terraform -chdir=terraform output -raw vpc_id", returnStdout: true).trim()

                    // Private instances
                    instance_ids.eachWithIndex { id, idx ->
                        echo "terraform import \"linode_instance.private[${idx}]\" ${id}"
                    }

                    // Proxy
                    echo "terraform import \"linode_instance.proxy\" ${proxy_id}"

                    // VPC
                    echo "terraform import \"linode_vpc.private\" ${vpc_id}"
                }
            }
        }

        stage('Announce SSH Commands') {
            steps {
                script {
                    // Get proxy IP
                    def proxy_ip = sh(script: "terraform -chdir=terraform output -raw proxy_public_ip", returnStdout: true).trim()

                    // Get private IPs as JSON and parse them
                    def private_ips_json = sh(script: "terraform -chdir=terraform output -json private_ips", returnStdout: true).trim()
                    def private_ips = readJSON text: private_ips_json

                    echo "Access your private Linodes using the following SSH commands:"
                    private_ips.eachWithIndex { ip, idx ->
                        echo "ssh -J funmicra@${proxy_ip} funmicra@${ip}   # private-${idx}"
                    }
                }
            }
        }

        // stage('Clean Workspace') {
        //     steps {
        //         echo 'Cleaning Jenkins workspace...'
        //         deleteDir()  // Jenkins Pipeline step to remove all files in the workspace
        //     }
        // }
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
