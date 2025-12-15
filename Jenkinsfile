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
                '''
            }
        }

        stage('Generate Terraform Import Commands') {
            steps {
                script {
                    echo "Generating Terraform import commands..."
                    def vm_ids = sh(
                        script: "terraform -chdir=terraform output -json instance_ids",
                        returnStdout: true
                    ).trim()

                    def parsed = readJSON text: vm_ids
                    parsed.eachWithIndex { id, idx ->
                        def resource_name = "linode_instance.private[${idx}]"
                        echo "terraform import ${resource_name} ${id}"
                    }

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
                    currentBuild.changeSets.any { cs ->
                        cs.items.any { it.msg.contains("[INFRA]") }
                    }
                }
            }
            steps {
                script {
                    def ips = sh(
                        script: 'terraform -chdir=terraform output -raw instance_ips',
                        returnStdout: true
                    ).trim().split("\\s+")

                    for (ip in ips) {
                        sh "ssh-keyscan -H ${ip} >> /var/lib/jenkins/.ssh/known_hosts"
                    }

                    sh "chown -R jenkins:jenkins /var/lib/jenkins/.ssh/"
                }
            }
        }

        stage('Update Ansible Inventory') {
            steps {
                script {
                    def gateway_ip = sh(
                        script: "terraform -chdir=terraform output -raw gateway_public_ip",
                        returnStdout: true
                    ).trim()

                    echo "Gateway IP is ${gateway_ip}"

                    sh """
                        sed -i '/\\[gateway\\]/,+1 s/ansible_host=.*/ansible_host=${gateway_ip}/' ansible/hosts.ini
                        sed -i "/\\[private:vars\\]/,+1 s/ProxyJump=root@.*/ProxyJump=root@${gateway_ip}/" ansible/hosts.ini
                    """

                    env.GATEWAY_IP = gateway_ip
                }
            }
        }

        stage('Ansible') {
            steps {
                sshagent(['ANSIBLE_SSH_KEY']) {
                    script {
                        // Extract public key from Jenkins SSH credential
                        def pubKey = sh(script: "ssh-add -L | head -n1", returnStdout: true).trim().replaceAll("\n","")
                        sh """
                        ansible-playbook -i ansible/hosts.ini ansible/playbook.yaml \
                        -u root -vv \
                        -e "ssh_extra_args='-o StrictHostKeyChecking=no -J root@${GATEWAY_IP}'" \
                        -e ssh_pub_key=\"\$(cat ${PUBKEY_FILE})\"
                        """
                    }
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
