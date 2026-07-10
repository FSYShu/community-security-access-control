// 社区安防门禁系统 - Jenkins Pipeline
// 支持 CI/CD 自动化构建、测试、部署

pipeline {
    agent any

    environment {
        // 项目配置
        PROJECT_NAME = 'community-security-access-control'
        // Docker 镜像仓库
        DOCKER_REGISTRY = credentials('docker-registry-url')
        // 部署服务器
        DEPLOY_HOST = credentials('deploy-host')
        // 数据库配置
        DB_HOST = credentials('db-host')
        DB_PASSWORD = credentials('db-password')
        // JWT 密钥
        JWT_SECRET = credentials('jwt-secret-key')
    }

    stages {
        stage('代码检出') {
            steps {
                echo '==> 检出代码...'
                checkout scm
            }
        }

        stage('前端构建') {
            steps {
                echo '==> 构建前端项目...'
                dir('frontend') {
                    sh 'node --version'
                    sh 'npm --version'
                    sh 'npm ci'
                    sh 'npm run lint'
                    sh 'npm run build'
                }
            }
        }

        stage('后端测试') {
            steps {
                echo '==> 运行后端测试...'
                dir('backend') {
                    sh 'python3 -m venv venv'
                    sh '. venv/bin/activate && pip install -r requirements.txt'
                    sh '. venv/bin/activate && python -m pytest tests/ -v --cov=app --cov-report=xml'
                }
            }
        }

        stage('构建 Docker 镜像') {
            steps {
                echo '==> 构建 Docker 镜像...'
                // 前端镜像
                sh "docker build -f Dockerfile.frontend -t ${DOCKER_REGISTRY}/${PROJECT_NAME}-frontend:${BUILD_NUMBER} ."
                sh "docker tag ${DOCKER_REGISTRY}/${PROJECT_NAME}-frontend:${BUILD_NUMBER} ${DOCKER_REGISTRY}/${PROJECT_NAME}-frontend:latest"

                // 后端镜像
                sh "docker build -f Dockerfile.backend -t ${DOCKER_REGISTRY}/${PROJECT_NAME}-backend:${BUILD_NUMBER} ."
                sh "docker tag ${DOCKER_REGISTRY}/${PROJECT_NAME}-backend:${BUILD_NUMBER} ${DOCKER_REGISTRY}/${PROJECT_NAME}-backend:latest"
            }
        }

        stage('推送镜像') {
            steps {
                echo '==> 推送 Docker 镜像到仓库...'
                sh "docker push ${DOCKER_REGISTRY}/${PROJECT_NAME}-frontend:${BUILD_NUMBER}"
                sh "docker push ${DOCKER_REGISTRY}/${PROJECT_NAME}-frontend:latest"
                sh "docker push ${DOCKER_REGISTRY}/${PROJECT_NAME}-backend:${BUILD_NUMBER}"
                sh "docker push ${DOCKER_REGISTRY}/${PROJECT_NAME}-backend:latest"
            }
        }

        stage('部署') {
            when {
                branch 'main'
            }
            steps {
                echo '==> 部署到生产环境...'
                sh """
                    ssh deploy@${DEPLOY_HOST} << 'EOF'
                    cd /opt/${PROJECT_NAME}
                    docker-compose pull
                    docker-compose up -d
                    docker-compose ps
                    EOF
                """
            }
        }
    }

    post {
        always {
            echo '==> 清理工作空间...'
            // 清理悬空镜像
            sh 'docker image prune -f'
        }
        success {
            echo '==> 构建成功！'
        }
        failure {
            echo '==> 构建失败，请检查日志！'
        }
    }
}