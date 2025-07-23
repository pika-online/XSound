from xsound.engine.fbank import Fbank_Engine
from xsound.engine.eres2net import Eres2net_Engine
from xsound.engine.translator import Translator
from xsound.utils import *
from .cluster import sv_cluster
import threading, queue, json

# 句子结构模板
sentence_structure = {
    "id": None,
    "text": "",
    "start": "",
    "end": "",
    "progress":0.,
}

class Diarization:
    def __init__(self, sv_engine: Eres2net_Engine, trans_engine: Translator):
        """
        初始化Diarization对象
        :param sv_engine: 说话人识别引擎
        :param trans_engine: 翻译引擎
        """
        self.sv_engine = sv_engine
        self.trans_engine = trans_engine
        self.sr = 16000  # 采样率

        # 线程通信队列
        self.sentence_generator = queue.Queue()  # 用于传递ASR识别结果
        self.trans_inputs = queue.Queue()        # 翻译输入队列
        self.trans_outputs = queue.Queue()       # 翻译输出队列

    def _trans_batch_decode(self, sentences, trans_language):
        """
        批量翻译句子
        :param sentences: 包含文本的句子列表
        :param trans_language: 翻译目标语言
        :return: id -> 翻译结果 的映射
        """
        texts = {str(i): sentence["text"] for i, sentence in enumerate(sentences)}
        trans_result = self.trans_engine.translate(None, trans_language, texts)
        trans_result = json.loads(extract_json(trans_result))
        trans_result = {sentence["id"]: text for sentence, text in zip(sentences, trans_result.values())}
        return trans_result

    def _thread_sentence(self, audio_data, hotwords):
        """
        句子线程（占位，未实现）
        :param audio_data: 音频数据
        :param hotwords: 热词
        """
        pass

    def _thread_trans(self, trans_language):
        """
        翻译线程，批量处理翻译任务
        :param trans_language: 目标语言
        """
        record = []
        batch_size = 5
        while True:
            sentence = self.trans_inputs.get()
            if sentence is None:
                break
            record.append(sentence)
            if len(record) > batch_size:
                sentences = record[:batch_size]
                record = record[batch_size:]
                trans_result = self._trans_batch_decode(sentences, trans_language)
                self.trans_outputs.put(trans_result)

        # 剩余未处理的句子
        if len(record):
            trans_result = self._trans_batch_decode(record, trans_language)
            self.trans_outputs.put(trans_result)

        self.trans_outputs.put(None)
        print("完成翻译")

    def __call__(self,
                 audio_file: str,
                 hotwords: list = [],
                 use_sv: bool = False,
                 trans_language: str = ""):
        """
        启动语音分段、识别、翻译与说话人聚类流程
        :param audio_file: 输入音频文件路径
        :param hotwords: ASR 热词
        :param use_sv: 是否启用说话人识别
        :param trans_language: 目标翻译语言（为空则不翻译）
        :yield: ("sentence", 句子)、("trans", 翻译结果)、("roles", 聚类角色)
        """
        # 加载音频数据
        audio_data = read_audio_file(audio_file)
        audio_seconds = len(audio_data)/self.sr

        # 启动句子线程
        sent_t = threading.Thread(target=self._thread_sentence, args=(audio_data, hotwords,), daemon=True)
        sent_t.start()

        # 启动翻译线程（如果启用）
        if trans_language:
            trans_t = threading.Thread(target=self._thread_trans, args=(trans_language,), daemon=True)
            trans_t.start()

        sv_task = []  # 存储需要做说话人识别的任务

        # 主处理循环，从ASR线程中获取句子
        while True:
            sentence = self.sentence_generator.get()
            self.trans_inputs.put(sentence)
            if sentence is None:
                break

            cur_time = float(sentence["end"])
            sentence["progress"] = round(cur_time/audio_seconds,3)
            yield ("sentence", sentence)

            # 提交说话人识别任务
            if use_sv:
                s, e = int(float(sentence["start"]) * self.sr), int(float(sentence["end"]) * self.sr)
                segment = audio_data[s:e]
                taskId = generate_random_string(20)
                self.sv_engine.submit(taskId, segment)
                sv_task.append((sentence["id"], taskId))

            # 返回翻译结果（若有）
            if trans_language:
                try:
                    sentence = self.trans_outputs.get(timeout=0.1)
                    yield ("trans", sentence)
                except:
                    continue

        # 等待ASR线程结束
        sent_t.join()

        # 获取说话人识别结果并聚类
        if use_sv:
            embeddings = {}
            for sentenceId, taskId in sv_task:
                embeddings[sentenceId] = self.sv_engine.get(taskId)
            roles = sv_cluster(embeddings)
            yield ("roles", roles)

        # 等待翻译线程结束，继续取出剩余的翻译结果
        if trans_language:
            trans_t.join()
            while not self.trans_outputs.empty():
                sentence = self.trans_outputs.get()
                if sentence is not None:
                    yield ("trans", sentence)
