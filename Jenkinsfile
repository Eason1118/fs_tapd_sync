
pipeline {
    agent {
        label "ansible"
    }
    options {
        timeout(time:60, ,unit:'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '200'))
    }
    parameters {
        string(name:"callback", defaultValue: '', description:"GMT回调地址")
        string(name:"wksp_id", defaultValue: '30866629', description:"项目ID")
        string(name:"doc_url", defaultValue: '', description:"文档链接")
        string(name:"tapd_type", defaultValue: 'bug', description:"类型")
        choice(name:"sync_dest", choices:['tapd', 'fs'], description:"同步")
    }

    stages {
        stage('拉取同步脚本') {
            steps {
                git branch: "develop", credentialsId: 'xxx', url: 'git@xx.git'
            }
        }
        stage('开始同步') {
            steps {
                sh """
                    pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple  >/dev/null
                    python3 main.py ${params.wksp_id} ${params.doc_url} ${params.tapd_type} ${params.sync_dest}
                """

            }
        }

	}
}