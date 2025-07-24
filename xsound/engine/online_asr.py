from xsound.utils import *
import websockets
import soundfile as sf 


class AsyncFunasrWebsocketRecognizer:
    def __init__(
        self,
        host="localhost",
        port="10098",
        is_ssl=True,
        chunk_size="0,10,5",
        chunk_interval=10,
        mode="offline",
        hotwords=None,
        wav_name="default"
    ):
        self.host = host
        self.port = port
        self.is_ssl = is_ssl
        self.uri = f"ws://{host}:{port}"
        self.chunk_size = [int(x) for x in chunk_size.split(",")]
        self.chunk_interval = chunk_interval
        self.mode = mode
        self.wav_name = wav_name
        self.websocket = None
        self.step = self.chunk_size[1] * 960  # 每个 chunk 对应的采样点数
        self.task_transit = None
        self.msg_queue = asyncio.Queue()
        self.abort = False
        self.hotwords = hotwords or {}
        self.chunk = b''

    async def connect(self):
        print(f"Connecting to: {self.uri}")
        self.websocket = await websockets.connect(self.uri)

        init_message = {
            "mode": self.mode,
            "chunk_size": self.chunk_size,
            "encoder_chunk_look_back": 4,
            "decoder_chunk_look_back": 1,
            "chunk_interval": self.chunk_interval,
            "wav_name": self.wav_name,
            "is_speaking": True,
            "hotwords": json.dumps(self.hotwords)
        }
        await self.websocket.send(json.dumps(init_message))
        print("Sent init JSON:", init_message)

    
    def transit(self,messager=None):
        self.task_transit = asyncio.create_task(self._backend_transit(messager))


    async def close(self):
        if self.task_transit:
            self.task_transit.cancel()
        if self.websocket:
            await self.websocket.close()
        print("WebSocket closed")

    async def _backend_transit(self,messager=None):
        try:
            async for message in self.websocket:
                content = json.loads(message)
                # print(content)
                if messager:
                    await messager(content)
        except websockets.exceptions.ConnectionClosed:
            print("WebSocket closed")

    async def read_sample(self, samples: bytes):
        try:
            if samples:
                self.chunk += samples
                if len(self.chunk) >= 2 * self.step:
                    data = self.chunk[:2 * self.step]
                    self.chunk = self.chunk[2 * self.step:]
                    await self.websocket.send(data)
            else:
                await self.farewell()
        except websockets.exceptions.ConnectionClosed:
            print("Funasr-WebSocket连接已关闭")

    async def farewell(self):
        self.chunk = self.chunk.ljust(2 * self.step, b'\x00')
        await self.websocket.send(self.chunk)
        await self.websocket.send(json.dumps({"is_speaking": False}))
        self.abort = True

async def main():
    file_path = 'examples/test.wav'
    recognizer = AsyncFunasrWebsocketRecognizer(
        host='localhost',
        port=10095,
        is_ssl=False,
        chunk_size="0,10,5",
        chunk_interval=10,
        mode='2pass',
        wav_name="test_async",
        hotwords={'魔塔': 60}
    )

    async def messager(content):
        print(content)

    await recognizer.connect()
    print("\n--- Start ---\n")
    recognizer.transit(messager)

    with sf.SoundFile(file_path, mode="r") as audio_file:
        while True:
            audio_frames = audio_file.read(1600, dtype="int16").tobytes()
            await recognizer.read_sample(audio_frames)
            if not audio_frames:
                break
            await asyncio.sleep(0.02)

    await asyncio.sleep(2)
    await recognizer.close()
    print("\n--- Finished ---\n")


if __name__ == "__main__":
    asyncio.run(main()) 