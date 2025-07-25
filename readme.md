<!---
Copyright 2025 Funsound语音团队. All rights reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
-->
# Xsound: 语音日志服务搭建

<p align="center">
  <img src="img/icon.png" alt="Xsound Icon" width="200"/>
</p>

<p align="center">
    <a href="https://github.com/huggingface/transformers/blob/main/LICENSE"><img alt="GitHub" src="https://img.shields.io/github/license/huggingface/transformers.svg?color=blue"></a>
    <a href="https://funsound.cn"><img alt="Documentation" src="https://img.shields.io/website/http/huggingface.co/docs/transformers/index.svg?down_color=red&down_message=offline&up_message=online"></a>
</p>


## 功能

- 支持离线文件实时句子生成，支持热词，时间戳，角色，多语言翻译
- 引入 paraformer-onnx-gpu (parajet，2000x速度) 大幅提升推理速度
- 基于生成生产-消费者范式构建 模型并发吞吐引擎
- 基于fastapi & 异步设计，支持多路并发请求

## 安装

1. create conda env
```shell
conda create -n xsound python=3.10
conda activate xsound
```

2. install faster whisper (先装！！！因为其依赖onnxruntime-cpu会覆盖gpu版本)
```shell
pip install faster-whisper
```

3. install onnxruntime-gpu
```shell
conda install -c nvidia cuda-runtime=12.4 cudnn=9.1 -y
pip install --force-reinstall onnxruntime-gpu==1.22
```

3. install necessary packages
```shell
pip install -r xsound/requirements.txt
```

## 使用

服务端设计（暂不开放）
- server.py 用户登录，语音转写接口设计
- database.py 用户数据库设计


启动服务

```shell
uvicorn server:app --host 0.0.0.0 --port 9031
```

客户端转写请参考：
- client.sh 通用http接口
- client.py 实时流式返回结果

