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
                TF_VAR_username = credentials('LINODE_USER_USERNAME')
            }
            steps {
                sh'python3 scripts/terraform_apply.py'
            }
        }

        stage('Update Dynamic Inventory') {
            steps {
                script {
                    sh 'python3 ansible/inventory/dynamic_inventory.py'
                }
            }
        }
        
        stage('Add Proxy to known_hosts') {
            steps {
                sh 'python3 scripts/add_proxy_to_known_hosts.py'
            }
        }

        stage('Add Private Nodes to known_hosts') {
            steps {
                sh 'python3 scripts/add_private_nodes_to_known_hosts.py'
            }
        }

        stage('Announce Terraform Import Commands') {
            steps {
                withCredentials([
                    sshUserPrivateKey(
                        credentialsId: 'ANSIBLE_PRIVATE_KEY',
                        keyFileVariable: 'ANSIBLE_PRIVATE_KEY',
                        usernameVariable: 'ANSIBLE_USER'
                    )
                ]){    
                    sh 'python3 scripts/announce_tf_import_commands.py'
                }
            }
        }

        stage('Run Ansible Playbooks') {
            steps {
                sh 'python3 scripts/run_ansible_playbook.py'
            }
        }

        stage('Announce SSH Commands') {
            steps {
                sh 'python3 scripts/announce_ssh_commands.py'
            }
        }

        stage('Clean Workspace') {
            steps {
                echo 'Cleaning Jenkins workspace...'
                deleteDir()  // Jenkins Pipeline step to remove all files in the workspace
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
