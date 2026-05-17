pipeline {
    agent any

    options {
        timeout(time: 15, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    environment {
        VENV_DIR = "${WORKSPACE}/.venv"
        RESULTS_DIR = "${WORKSPACE}/results"
    }

    stages {

        stage('Setup Python environment') {
            steps {
                sh '''
                    python3 -m venv ${VENV_DIR}
                    ${VENV_DIR}/bin/pip install --upgrade pip
                    ${VENV_DIR}/bin/pip install -r requirements.txt
                '''
            }
        }

        stage('Start payment API') {
            steps {
                sh '''
                    mkdir -p ${RESULTS_DIR}
                    ${VENV_DIR}/bin/uvicorn api.payment_api:app \
                        --host 0.0.0.0 --port 8000 \
                        --log-level warning &
                    echo $! > /tmp/api.pid
                    sleep 3
                    curl -sf http://localhost:8000/health || (echo "API did not start" && exit 1)
                '''
            }
        }

        stage('Run Robot Framework tests') {
            steps {
                sh '''
                    ${VENV_DIR}/bin/robot \
                        --outputdir ${RESULTS_DIR} \
                        --loglevel INFO \
                        --report report.html \
                        --log log.html \
                        --output output.xml \
                        tests/suites/
                '''
            }
            post {
                always {
                    // Archive RF's own HTML report
                    publishHTML(target: [
                        allowMissing: false,
                        alwaysLinkToLastBuild: true,
                        keepAll: true,
                        reportDir: 'results',
                        reportFiles: 'report.html',
                        reportName: 'Robot Framework Report'
                    ])
                }
            }
        }

        stage('Generate QA dashboard') {
            steps {
                sh '''
                    ${VENV_DIR}/bin/python dashboard/parse_results.py \
                        ${RESULTS_DIR}/output.xml \
                        --out ${RESULTS_DIR}/dashboard.html
                '''
            }
            post {
                always {
                    publishHTML(target: [
                        allowMissing: false,
                        alwaysLinkToLastBuild: true,
                        keepAll: true,
                        reportDir: 'results',
                        reportFiles: 'dashboard.html',
                        reportName: 'QA Dashboard'
                    ])
                }
            }
        }

    }

    post {
        always {
            // Stop the API process
            sh 'kill $(cat /tmp/api.pid) 2>/dev/null || true'

            // Archive all RF artefacts
            archiveArtifacts artifacts: 'results/**', allowEmptyArchive: true

            // Native JUnit-style result parsing (via RF XML)
            script {
                if (fileExists('results/output.xml')) {
                    step([$class: 'RobotPublisher',
                        outputPath: 'results',
                        outputFileName: 'output.xml',
                        passThreshold: 90.0,
                        unstableThreshold: 75.0,
                    ])
                }
            }
        }

        success {
            echo "All tests passed. Dashboard published."
        }

        failure {
            echo "One or more tests failed. Check the QA Dashboard for details."
        }
    }
}
