pipeline {
    agent any

    options {
        skipDefaultCheckout(true)
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '20', artifactNumToKeepStr: '10'))
    }

    parameters {
        choice(
            name: 'PROMOTE_TO',
            choices: ['TEST', 'QA', 'PREPROD', 'PROD'],
            description: 'Hasta qué ambiente SIMULADO se permite promover (por defecto solo TEST)'
        )
    }

    environment {
        LAB_REPOSITORY = '/opt/devops-lab/nexus-sim'
        LAB_ENVIRONMENTS = '/opt/devops-lab/environments'
    }

    stages {
        stage('01 - GitHub: checkout') {
            steps {
                checkout scm
                sh 'git log -1 --oneline'
                script {
                    def shortSha = sh(script: 'git rev-parse --short=12 HEAD', returnStdout: true).trim()
                    env.RELEASE_VERSION = "${env.BUILD_NUMBER}-${shortSha}"
                    echo "Version del artefacto: ${env.RELEASE_VERSION}"
                    echo "Rama: ${env.BRANCH_NAME}; PR: ${env.CHANGE_ID ?: 'no'}"
                }
            }
        }

        stage('02 - Pruebas unitarias') {
            steps {
                sh 'python3 -m tools.run_tests'
            }
            post {
                always {
                    junit testResults: 'reports/tests.xml', allowEmptyResults: true
                }
            }
        }

        stage('03 - IBM DBB: build SIMULADO') {
            steps {
                sh '''
                  python3 -m tools.dbb \
                    --source fuentes/cobol \
                    --copybooks fuentes/copybooks \
                    --output dist/programas.tar.gz \
                    --commit "$(git rev-parse HEAD)"
                '''
            }
        }

        stage('04 - SonarQube: quality gate SIMULADO') {
            steps {
                sh '''
                  python3 -m tools.sonar \
                    --source fuentes \
                    --report reports/quality.json
                '''
            }
        }

        stage('05 - Nexus: publicar SIMULADO') {
            when { branch 'main' }
            steps {
                sh '''
                  python3 -m tools.nexus publish \
                    --repository "$LAB_REPOSITORY" \
                    --artifact dist/programas.tar.gz \
                    --name demo-cobol \
                    --version "$RELEASE_VERSION"
                '''
            }
        }

        stage('06 - Wazi Deploy: TEST SIMULADO') {
            when { branch 'main' }
            steps {
                sh '''
                  python3 -m tools.wazi deploy \
                    --repository "$LAB_REPOSITORY" \
                    --environments "$LAB_ENVIRONMENTS" \
                    --name demo-cobol --version "$RELEASE_VERSION" --target TEST
                  python3 -m tools.smoke_test --environments "$LAB_ENVIRONMENTS" \
                    --target TEST --version "$RELEASE_VERSION"
                '''
            }
        }

        stage('07 - Aprobar QA') {
            when {
                allOf {
                    branch 'main'
                    expression { ['QA', 'PREPROD', 'PROD'].contains(params.PROMOTE_TO) }
                }
            }
            steps {
                input message: "¿Promover ${env.RELEASE_VERSION} a QA simulado?", ok: 'Aprobar QA'
            }
        }

        stage('08 - Wazi Deploy: QA SIMULADO') {
            when {
                allOf {
                    branch 'main'
                    expression { ['QA', 'PREPROD', 'PROD'].contains(params.PROMOTE_TO) }
                }
            }
            steps {
                sh '''
                  python3 -m tools.wazi deploy \
                    --repository "$LAB_REPOSITORY" \
                    --environments "$LAB_ENVIRONMENTS" \
                    --name demo-cobol --version "$RELEASE_VERSION" --target QA
                  python3 -m tools.smoke_test --environments "$LAB_ENVIRONMENTS" \
                    --target QA --version "$RELEASE_VERSION"
                '''
            }
        }

        stage('09 - Aprobar PREPROD') {
            when {
                allOf {
                    branch 'main'
                    expression { ['PREPROD', 'PROD'].contains(params.PROMOTE_TO) }
                }
            }
            steps {
                input message: "¿Promover ${env.RELEASE_VERSION} a PREPROD simulado?", ok: 'Aprobar PREPROD'
            }
        }

        stage('10 - Wazi Deploy: PREPROD SIMULADO') {
            when {
                allOf {
                    branch 'main'
                    expression { ['PREPROD', 'PROD'].contains(params.PROMOTE_TO) }
                }
            }
            steps {
                sh '''
                  python3 -m tools.wazi deploy \
                    --repository "$LAB_REPOSITORY" \
                    --environments "$LAB_ENVIRONMENTS" \
                    --name demo-cobol --version "$RELEASE_VERSION" --target PREPROD
                  python3 -m tools.smoke_test --environments "$LAB_ENVIRONMENTS" \
                    --target PREPROD --version "$RELEASE_VERSION"
                '''
            }
        }

        stage('11 - Aprobar PROD') {
            when {
                allOf {
                    branch 'main'
                    expression { params.PROMOTE_TO == 'PROD' }
                }
            }
            steps {
                input message: "¿Promover ${env.RELEASE_VERSION} a PROD simulado?", ok: 'Aprobar PROD'
            }
        }

        stage('12 - Wazi Deploy: PROD SIMULADO') {
            when {
                allOf {
                    branch 'main'
                    expression { params.PROMOTE_TO == 'PROD' }
                }
            }
            steps {
                sh '''
                  python3 -m tools.wazi deploy \
                    --repository "$LAB_REPOSITORY" \
                    --environments "$LAB_ENVIRONMENTS" \
                    --name demo-cobol --version "$RELEASE_VERSION" --target PROD
                  python3 -m tools.smoke_test --environments "$LAB_ENVIRONMENTS" \
                    --target PROD --version "$RELEASE_VERSION"
                '''
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'dist/**,reports/**', fingerprint: true, allowEmptyArchive: true
        }
        success { echo 'Pipeline completado correctamente.' }
        failure { echo 'Pipeline fallido: revisar Console Output y reportes.' }
    }
}
