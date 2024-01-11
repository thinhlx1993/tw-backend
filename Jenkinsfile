pipeline {
    agent any
    environment {
        ApiRegistry = "registry.digitalocean.com/meetingx"
        celeryRegistry = "registry.digitalocean.com/meetingx"
        ApiImageName = ''
        celeryImageName = ''
        branchName = ''
        commitMessage = ''
    }
    stages {
        stage('Test') {
            agent {
                dockerfile {
                    filename 'Dockerfile.test'
                }
            }
            environment {
                CONFIG="DEV"
                LOG_LEVEL="INFO"
                PORT=5000
            }
            steps {
                echo "Start testing for controllers"
                script{
                    commitMessage = sh(script:"""
                    git log --format=format:%s -1
                    """, returnStdout: true).trim()
                }
                sh "nose2 -s ./tests/unit_test/v2/controllers --verbose"
            }
        }
        stage('Build') {
            steps {
                echo "Building Docker Image"
                script {
                    commitMessage = sh(script:"""
                        git log --format=format:%s -1
                    """, returnStdout: true).trim()

                    branchName = sh(script:"""
                        echo ${env.JOB_NAME} | sed 's@.*/@@'
                    """, returnStdout: true).trim()

                    ApiImageName = docker.build(ApiRegistry+":${branchName}_${env.BUILD_ID}", "-f Dockerfile.prod .")

                    celeryImageName = docker.build(celeryRegistry+":${branchName}_${env.BUILD_ID}", "-f Dockerfile.celery .")
                }
            }
        }
        stage('Push') {
            steps {
                echo "Push stage"
                script{
                    docker.withRegistry("https://"+ApiRegistry, 'ecr:ap-southeast-1:<ERC_UUID>') {
                        ApiImageName.push()
                    }

                    docker.withRegistry("https://"+celeryRegistry, 'ecr:ap-southeast-1:<ERC_UUID>') {
                        celeryImageName.push()
                    }
                }
            }
        }
        stage('Archive') {
            steps{
                sh "echo 'JOB_NAME: ${env.JOB_NAME}\nBUILD_NUMBER: ${env.BUILD_NUMBER}\nGIT_COMMIT: ${env.GIT_COMMIT}\nCOMMIT_MESSAGE: ${commitMessage}\nIMAGE_TAG: $ApiRegistry:${branchName}_${env.BUILD_ID}\nWORKER_IMAGE_TAG: $celeryRegistry:${branchName}_${env.BUILD_ID}' > build.yaml"
            }
        }
        stage('Cleanup') {
            steps {
                sh """
                    docker rmi $ApiRegistry:${branchName}_${env.BUILD_ID}
                    docker rmi $celeryRegistry:${branchName}_${env.BUILD_ID}
                """
            }
        }
    }
    post {
        always {
            slackSend(message:"Job ${env.JOB_NAME} ${env.BUILD_NUMBER} with commit: '${commitMessage}' has completed with status: ${currentBuild.currentResult} \n (<${env.BUILD_URL}|Open>)")
            archiveArtifacts artifacts:'build.yaml'
        }
    }
}
