SR = 16000


fbank_config = {
    "engine": "mt", # mt: 多线程， mp: 多进程
    "num_workers": 4, # 后台worker数目
    "stream": False,
    "instance":{}
}

parajet_config = {
        "engine": "mt", # mt: 多线程， mp: 多进程
        "num_workers": 4, # 后台worker数目
        "batch_wait_seconds": 0.1, # 聚合等待时间，越小响应越快，但也会降低推理效率
        # 模型初始化配置
        "instance":{
            "model_dir": "models/asr/parajet",
            "intra_op_num_threads": 1,
            "inter_op_num_threads": 1,
            "use_gpu": True,
            "feed_fixed_shape": [20,30*SR]
        }

    }

ct_transformer_config = {
    "engine": "mt", # mt: 多线程， mp: 多进程
    "num_workers": 4, # 后台worker数目
    "stream": False,
    "instance":{
            "model_dir": "models/punc/sherpa-onnx-punct-ct-transformer-zh-en-vocab272727-2024-04-12",
            "intra_op_num_threads": 1,
            "inter_op_num_threads": 1,
            "use_gpu": True,
        }
}

eres2net_config = {
    "engine": "mt", # mt: 多线程， mp: 多进程
    "num_workers": 4, # 后台worker数目
    "stream": False,
    "instance":{
            "model_dir": "models/sv/speech_eres2net_large_sv_zh-cn_3dspeaker_16k_onnx",
            "intra_op_num_threads": 1,
            "inter_op_num_threads": 1,
            "use_gpu": True,
        }
}


whisper_config = {
    "engine": "mp", # mt: 多线程， mp: 多进程
    "num_workers": 2, # 后台worker数目
    "stream": True,
    "instance":{
            "model_dir": "models/asr/faster-whisper-large-v3",
            "device": "cuda",
            "compute_type": "float16"
        }
}

llm_config = {
    "url": "http://47.117.188.50:9001/v1/chat/completions",
    "api_key": "not empty",
    "model_id": "Qwen/Qwen2.5-72B-Instruct"
}