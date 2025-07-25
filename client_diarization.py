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
    assert not trans_language or trans_language in languages

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
    
    uri = f"ws://{base_path}/ws/diarization/"  # WebSocket 接口地址
    file_path = "test1.wav"  # 替换为你的音频文件路径
    uid = "kS0LTpA2ip"


    # 启动异步识别任务
    asyncio.run(diarization(
        uri=uri,
        file_path=file_path,
        filename=os.path.basename(file_path),
        use_sv=False,
        uid=uid,
        engine='whisper',
        trans_language=""
    ))
