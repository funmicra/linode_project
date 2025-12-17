pipeline {
    agent any

    environment {
        TF_IN_AUTOMATION         = "true"
        TF_INPUT                  = "false"
        ANSIBLE_HOST_KEY_CHECKING = "False"
        TF_VAR_user_password = credentials('LINODE_USER_PASSWORD')
        TF_VAR_linode_token  = credentials('LINODE_TOKEN')
        TF_VAR_ssh_keys_file = "${WORKSPACE}/terraform/ssh_key.b64"

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
            steps {
                script {
                    try {
                        sh '''
                            cd terraform
                            terraform init
                            terraform plan
                            terraform apply -auto-approve
                        '''
                    } catch (err) {
                        echo "Terraform failed, stopping pipeline until fixed."
                        currentBuild.result = 'FAILURE'
                        error("Stop pipeline")
                    }
                }
            }
        }

        stage('Prepare Inventory & SSH') {
            parallel {

                stage('Generate Inventory') {
                    steps {
                        catchError(buildResult: 'SUCCESS', stageResult: 'FAILURE') {
                            sh 'python3 ansible/inventory/hosts.py'
                        }
                    }
                }

                stage('Add Proxy to known_hosts') {
                    steps {
                        catchError(buildResult: 'SUCCESS', stageResult: 'FAILURE') {
                            script {
                                def proxy_ip = sh(
                                    script: "awk '/\\[proxy\\]/ {getline; print}' ansible/inventory/hosts.ini | tr -d '\"'",
                                    returnStdout: true
                                ).trim()
                                sh """
                                    ssh-keyscan -H ${proxy_ip} >> /var/lib/jenkins/.ssh/known_hosts || true
                                    chown jenkins:jenkins /var/lib/jenkins/.ssh/known_hosts
                                """
                            }
                        }
                    }
                }

                stage('Add Private Nodes to known_hosts') {
                    steps {
                        catchError(buildResult: 'SUCCESS', stageResult: 'FAILURE') {
                            script {
                                def proxy_ip = sh(
                                    script: "awk '/\\[proxy\\]/ {getline; print}' ansible/inventory/hosts.ini | tr -d '\"'",
                                    returnStdout: true
                                ).trim()

                                def private_ips = sh(
                                    script: 'awk \'/\\[private\\]/ {flag=1; next} /^$/ {flag=0} flag {print}\' ansible/inventory/hosts.ini | tr -d \'"\'',
                                    returnStdout: true
                                ).trim().split('\n')


                                for (ip in private_ips) {
                                    sh "ssh-keygen -R ${ip} || true"
                                    sh "ssh-keyscan -o ProxyJump=funmicra@${proxy_ip} -H ${ip} >> /var/lib/jenkins/.ssh/known_hosts || true"
                                }

                                sh "chown jenkins:jenkins /var/lib/jenkins/.ssh/known_hosts"
                            }
                        }
                    }
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
                    retry(2) {
                        sh '''
                            set -e
                            eval "$(ssh-agent -s)"
                            ssh-add "$ANSIBLE_PRIVATE_KEY"
                            ansible-playbook ansible/site.yaml -i ansible/inventory/hosts.ini -u "$ANSIBLE_USER" -vv
                        '''
                    }
                }
            }
        }

        stage('Announce Terraform Import Commands') {
            steps {
                script {
                    catchError(buildResult: 'SUCCESS', stageResult: 'FAILURE') {
                        def instance_ids = readJSON(text: sh(script: "terraform -chdir=terraform output -json instance_ids", returnStdout: true).trim())
                        def proxy_id = sh(script: "terraform -chdir=terraform output -raw proxy_id", returnStdout: true).trim()
                        def vpc_id = sh(script: "terraform -chdir=terraform output -raw vpc_id", returnStdout: true).trim()

                        instance_ids.eachWithIndex { id, idx ->
                            echo "terraform import \"linode_instance.private[${idx}]\" ${id}"
                        }

                        echo "terraform import \"linode_instance.proxy\" ${proxy_id}"
                        echo "terraform import \"linode_vpc.private\" ${vpc_id}"
                    }
                }
            }
        }

        stage('Announce SSH Commands') {
            steps {
                script {
                    catchError(buildResult: 'SUCCESS', stageResult: 'FAILURE') {
                        def proxy_ip = sh(script: "terraform -chdir=terraform output -raw proxy_public_ip", returnStdout: true).trim()
                        def private_ips_json = sh(script: "terraform -chdir=terraform output -json private_ips", returnStdout: true).trim()
                        def private_ips = readJSON text: private_ips_json

                        echo "Access your private Linodes using the following SSH commands:"
                        private_ips.eachWithIndex { ip, idx ->
                            echo "ssh -J funmicra@${proxy_ip} funmicra@${ip}   # private-${idx}"
                        }
                    }
                }
            }
        }

        stage('Clean Workspace') {
            steps {
                echo 'Cleaning Jenkins workspace...'
                deleteDir()
            }
        }
    }

    post {
        always {
            echo "Cleaning SSH agent and workspace..."
            sh 'ssh-agent -k || true'
            deleteDir()
        }
        success {
            echo 'Infrastructure provisioned and configured successfully.'
        }
        failure {
            echo 'Pipeline failed. Inspect Terraform or Ansible stage logs.'
        }
    }
}
