
# 🎧 XSound AI语音接口文档

## 0. 服务地址

address="https://funsound.cn/xsound"
<!-- address="http://40.162.42.130:9031" -->

## 1. 账号注册登录

### 1.1 账号注册
- 邮箱注册
```shell
curl -X POST $address/register/ -F "account=test_account@gmail.com" -F "account_type=email" -F "password=123456" 
```
- 验证邮箱
```shell
curl -X POST $address/register/ -F "account=test_account@gmail.com" -F "account_type=email" -F "password=123456" -F "code=4140"
```

### 1.2 账号登录
登陆后获得账号uid，uid是ai服务的必要参数
```shell
curl -X POST $address/login/ -F "account=test_account@gmail.com"  -F "password=12345678" 
```
返回示例:
```shell
{"status":"success","msg":"254JVMnWdh","result":{},"completed":null,"stream":false}
```

### 1.3 修改密码
```shell
curl -X POST $address/change-password/ -F "account=coolephemeroptera@gmail.com"  -F "old_password=123456" -F "new_password=12345678"  
```

### 1.4 查询余额
```shell
curl -X GET $address/get_account/?uid=${uid}  
```
返回示例:
```shell
{"status":"success","msg":"","result":{"account":"test_account@gmail.com","vip":false,"quota":7200},"completed":null,"stream":false}
```


## 2. 一句话 ASR
- 适用于段音频快速识别
- 必填字段：uid, file
- 可选字段: 热词hotwords
```shell
curl -X POST $address/oneshot_asr/ \
-F "uid=${uid}" \
-F "file=@examples/short.mp3" \
-F "hotwords=[\"阿里巴巴\",\"心森招聘\"]"
```

## 3. 一句话 TTS
- 快速合成输入文本语音，输出格式mp3
- 必填字段：uid, text
- 可选字段: 音色tts_style(1,2,3,4)
```shell
curl -X POST $address/oneshot_tts/ \
-F "uid=${uid}" \
-F "text=欢迎使用语音合成" \
-F "tts_style=1" \
-o tts.mp3
```

## 4. 实时语音识别 （websocket）
- 实时音频块上传，实时识别结果返回
- 必填字段：uid, 可选字段：hotwords
- 交互代码参考附录A

## 5. 语音日志 
- 长音频语音日志转写，流式返回
- 必填字段：uid, file
- 可选字段: 引擎engine (funasr，whisper); 热词hotwords; 开启角色识别use_sv; 语言翻译trans_language

获取支持的翻译语言
```shell
curl -X GET $address/get_languages/?uid=${uid} 
```
转写请求
```shell
curl -X POST $address/diarization/ \
-F "uid=${uid}" \
-F "file=@examples/test.wav" \
-F "hotwords=[\"阿里巴巴\",\"心森招聘\"]"
-F "engine=funasr" \
-F "use_sv=true" \
-F "trans_language=English" 
```
返回示例:
```shell
{"status": "success", "msg": "diarization", "result": ["sentence", {"id": "0_s0ZNK", "text": "嗯,", "start": "5.410", "end": "5.710", "progress": 0.072}], "completed": null, "stream": true}
{"status": "success", "msg": "diarization", "result": ["sentence", {"id": "1_FVCHI", "text": "那么今天我们就简单的进行一下那个新生招聘的嗯讨论吧,", "start": "5.710", "end": "12.010", "progress": 0.152}], "completed": null, "stream": true}
(实时翻译){"status": "success", "msg": "diarization", "result": ["trans", {"0_s0ZNK": "Well,", "1_FVCHI": "today we'll briefly discuss the recruitment of new members,", "2_RbIbK": "since the new students will be arriving soon,", "3_H8ye8": "and our club needs to recruit some new members,", "4_Sh1Vu": "so let's discuss how we're going to conduct the recruitment today,"}], "completed": null, "stream": true}
 ...
{"status": "success", "msg": "diarization", "result": ["sentence", {"id": "31_fs5Bo", "text": "我们可以在演播厅底下,", "start": "69.950", "end": "72.350", "progress": 0.916}], "completed": null, "stream": true}
(最后角色识别){"status": "success", "msg": "diarization", "result": ["roles", {"0_s0ZNK": 2, "1_FVCHI": 0, "2_RbIbK": 0, "3_H8ye8": 0, "4_Sh1Vu": 0, "5_XfrAR": 2,...}], "completed": null, "stream": true}
{"status": "success", "msg": "bill", "result": {"audio_seconds": 79, "infer_cost_seconds": 9.283, "infer_speed": 8.51, "balance_before": 7200, "balance_now": 6924, "fee_base": 79, "fee_sv": 39, "fee_trans": 158, "fee_all": 276}, "completed": true, "stream": true}

```

## 6. 语音日志 （websocket）
- 长音频语音日志转写，流式上传，流式返回
- 必填字段：uid, file
- 可选字段: 引擎engine (funasr，whisper); 热词hotwords; 开启角色识别use_sv; 语言翻译trans_language
- 交互代码参考附录B


## 附录

A. 在线语音识别（python）
```python
import asyncio
import websockets
import json
import soundfile as sf

async def send_audio(websocket, audio_path):
    with sf.SoundFile(audio_path, mode="r") as audio_file:
        while True:
            audio_frames = audio_file.read(1600, dtype="int16").tobytes()
            await websocket.send(audio_frames)
            if not audio_frames:
                break
            await asyncio.sleep(0.08)
        # 发送空帧表示结束
        await websocket.send(b"")
    print("传输完毕")

async def receive_result(websocket):
    try:
        while True:
            response = await websocket.recv()
            print("Recognition Result:", response)
    except websockets.exceptions.ConnectionClosed:
        print("Connection closed by server.")

async def main():
    uri = "ws://localhost:9031/ws/2pass/"
    audio_file = "examples/test.wav"
    uid = "kS0LTpA2ip"
    hotwords = ["阿里巴巴"]

    async with websockets.connect(uri) as websocket:
        # 构造初始 JSON 消息
        init_message = {
            "uid": uid,
            "hotwords": hotwords
        }
        await websocket.send(json.dumps(init_message))

        # 并发运行发送和接收任务
        await asyncio.gather(
            send_audio(websocket, audio_file),
            receive_result(websocket)
        )

# 启动主程序
asyncio.run(main())

```

B. 语音日志（python）
```python
import asyncio
import websockets
import json
import os
import requests

base_path = "localhost:9031"

# 清屏函数（根据系统平台设置）
def clear():
    os.system('clear')  # Windows 用户改为 'cls'

# 进度条显示函数
def string_progress(val):
    n = int(val * 20)
    return "#" * n + f"({val * 100:.1f}%)"


# WebSocket 异步识别任务
async def diarization(
    uri,
    file_path,
    filename="sample.wav",
    uid="test_user",
    engine="whisper",
    hotwords=[],
    use_sv=False,
    trans_language="English",
):
    # 校验目标语言合法性
    response = requests.get(f"http://{base_path}/get_languages/")
    languages = response.json()['result']
    print(f"可翻译语言: {languages}")
    assert trans_language in languages

    async with websockets.connect(uri) as websocket:
        # S0: 发送初始化配置
        init_config = {
            "filename": filename,
            "uid": uid,
            "engine": engine,
            "hotwords": hotwords,
            "use_sv": use_sv,
            "trans_language": trans_language
        }
        await websocket.send(json.dumps(init_config))

        # S1: 等待服务端返回鉴权或初始化确认
        json_data = json.loads(await websocket.recv())
        print("S1:", json_data)
        if json_data.get("status") != "success":
            return  # 初始化失败则退出

        # S2: 分块上传音频数据（最大512KB每块）
        chunk_size = 512 * 1024
        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                await websocket.send(chunk)

                # 等待每块上传的确认响应
                json_data = json.loads(await websocket.recv())
                print("S2:", json_data)
                if json_data.get("status") != "success":
                    return

        # 上传完毕，发送空字节表示结束
        await websocket.send(b"")
        json_data = json.loads(await websocket.recv())
        print("S2:", json_data)
        if json_data.get("status") != "success":
            return

        # S3: 接收并解析实时语音日志（Diarization）结果
        progress = 0.0
        table = {}

        while True:
            json_data = json.loads(await websocket.recv())
            status = json_data["status"]
            msg = json_data["msg"]
            result = json_data["result"]
            completed = json_data["completed"]

            if status == "error":
                print(f"发生错误: {msg}")
                break

            # 根据消息类型处理识别内容
            if msg == "diarization":
                tag, content = result

                # 原始语音内容
                if tag == "sentence":
                    id = content["id"]
                    start = content["start"]
                    end = content["end"]
                    text = content["text"]
                    progress = content["progress"]
                    table[id] = {
                        "id": id,
                        "start": start,
                        "end": end,
                        "text": text,
                        "role": None,
                        "trans": ""
                    }

                # 翻译内容
                if tag == "trans":
                    for id in content:
                        table[id]["trans"] = content[id]

                # 说话人角色标签
                if tag == "roles":
                    for id in content:
                        table[id]["role"] = content[id]

                # 实时刷新控制台输出
                clear()
                print(string_progress(progress))
                print("-" * 100)
                for id in table:
                    print(f"id: {id} | time: {table[id]['start']} - {table[id]['end']} | role: {table[id]['role']}")
                    print(f"text: {table[id]['text']}")
                    print(f"trans: {table[id]['trans']}")
                    print("-" * 50)

            # 显示服务账单（如使用时长或计费）
            if msg == "bill":
                print(f"账单: {result}")

            # 完成标志
            if completed:
                print("识别完毕")
                break

# 主函数入口
if __name__ == "__main__":
    
    uri = f"wss://{base_path}/ws/diarization/"  # WebSocket 接口地址
    file_path = "test.wav"  # 替换为你的音频文件路径
    uid = "kS0LTpA2ip"


    # 启动异步识别任务
    asyncio.run(diarization(
        uri=uri,
        file_path=file_path,
        filename=os.path.basename(file_path),
        use_sv=True,
        uid=uid,
        engine='funasr'  # 可替换为 whisper 等其他引擎
    ))

```
