from .lib import *

def read_audio_file(audio_file):
    """读取音频文件数据并转换为PCM格式。"""
    ffmpeg_cmd = [
        FFMPEG,
        '-i', audio_file,
        '-f', 's16le',
        '-acodec', 'pcm_s16le',
        '-ar', '16k',
        '-ac', '1',
        'pipe:']
    with subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=False) as proc:
        stdout_data, stderr_data = proc.communicate()
    pcm_data = np.frombuffer(stdout_data, dtype=np.int16)
    return pcm_data


def read_audio_bytes(audio_bytes):
    ffmpeg_cmd = [
    FFMPEG,
    '-i', 'pipe:',  
    '-f', 's16le',
    '-acodec', 'pcm_s16le',
    '-ar', '16k',
    '-ac', '1',
    'pipe:' ]
    with subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=False) as proc:
        stdout_data, stderr_data = proc.communicate(input=audio_bytes)
    pcm_data = np.frombuffer(stdout_data, dtype=np.int16)
    return pcm_data

class Timer:
    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, *args):
        self.end = time.time()
        self.interval = self.end - self.start

def audio_f2i(data, width=16):
    """将浮点数音频数据转换为整数音频数据。"""
    data = np.array(data)
    return np.int16(data * (2 ** (width - 1)))

def audio_i2f(data, width=16):
    """将整数音频数据转换为浮点数音频数据。"""
    data = np.array(data)
    return np.float32(data / (2 ** (width - 1)))

def generate_random_string(n):
    letters = string.ascii_letters + string.digits
    random_string = ''.join(random.choice(letters) for i in range(n))
    return random_string

def reshape_audio_to_BxT(audio: np.ndarray, T: int) -> np.ndarray:
    """
    将音频reshape为 B x T，长度不足T补零，超过T分块（不足一块的尾部补零）
    
    参数:
        audio: 原始音频数据，1D numpy 数组
        T: 每块的时间长度（采样点数）
    
    返回:
        reshaped_audio: shape 为 (B, T) 的 numpy 数组
    """
    L = len(audio)
    B = int(np.ceil(L / T))  # 计算所需的块数
    padded_length = B * T
    padded_audio = np.zeros(padded_length, dtype=audio.dtype)
    padded_audio[:L] = audio  # 补零
    
    reshaped_audio = padded_audio.reshape(B, T)
    return reshaped_audio

def save_wavfile(path, wave_data):
    wave_data = np.array(wave_data,dtype='int16')
    """保存音频数据为wav文件。"""
    with wave.open(path, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(16000)
        wav_file.writeframes(wave_data.tobytes())

def mkdir(path, reset=False):
    if os.path.exists(path):
        if reset:
            shutil.rmtree(path)
            print(f"Removed existing directory: {path}")
            os.makedirs(path)
    else:
        os.makedirs(path)
        print(f"Directory created: {path}")
    return path

def extract_json(content):
    # Use regex to find the JSON part within the string
    if "```json" not in content:
        json_string = content
        return json_string
    json_match = re.search(r'```json\s*(?P<content>.*?)```', content, re.DOTALL)
    if json_match:
        json_string = json_match.group("content").strip()  # 提取命名组中的内容并移除多余的空白
        return json_string
    return ""

def get_current_time():
    # 获取当前时间
    current_time = datetime.datetime.now()
    # 格式化时间，精确到秒
    formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
    return formatted_time


def get_audio_duration(file_path):
    """
    获取音频文件的时长（单位：秒）

    参数:
        file_path (str): 音频文件路径

    返回:
        float: 音频时长（秒）
        None: 获取失败时
    """
    try:
        result = subprocess.run(
            [
                FFPROBE, "-i", file_path,
                "-show_entries", "format=duration",
                "-v", "quiet",
                "-of", "csv=p=0"
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        duration_str = result.stdout.strip()
        return float(duration_str) if duration_str else None
    except Exception as e:
        print(f"获取音频时长出错: {e}")
        return None

async def fix_webm_pts(input_file: str, output_file: str):
    process = await asyncio.create_subprocess_exec(
        'ffmpeg',
        '-i', input_file,
        '-c', 'copy',
        '-fflags', '+genpts',
        output_file,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await process.communicate()

    if process.returncode == 0:
        print(f"成功修复 {input_file} 为 {output_file}")
    else:
        print(f"发生错误:\n{stderr.decode()}")

# 异步地逐步迭代同步生成器
def async_generator_wrapper(sync_gen):
    async def wrapper():
        loop = asyncio.get_running_loop()
        iterator = iter(sync_gen)

        while True:
            def get_next():
                try:
                    return next(iterator)
                except StopIteration:
                    return None  # 特别标志，说明结束了

            item = await loop.run_in_executor(None, get_next)
            if item is None:
                break
            yield item

    return wrapper()