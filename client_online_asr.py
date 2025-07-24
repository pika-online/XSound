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
