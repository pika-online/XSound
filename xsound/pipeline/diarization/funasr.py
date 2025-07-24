
from xsound.utils import *
from xsound.engine.fbank import Fbank_Engine
from xsound.engine.parajet import Paraformer_Engine
from xsound.engine.ct_transformer import PuncCT_Engine
from xsound.engine.eres2net import Eres2net_Engine
from xsound.engine.translator import Translator
from xsound.engine.base import batch_inference_generator
from .base import Diarization,sentence_structure




def split_by_pause(tokens, timestamps, delta):
    """
    根据停顿时间将 tokens 切分成多个子句

    参数:
        tokens: 字符串列表
        timestamps: 每个 token 的时间戳 [[start, end], ...]
        delta: 停顿时间阈值（秒）

    返回:
        子句列表，每个子句包含 tokens 和 timestamps
    """
    clauses = []
    current_clause_tokens = []
    current_clause_timestamps = []

    for i in range(len(tokens)):
        if i > 0:
            pause = timestamps[i][0] - timestamps[i - 1][1]
            if pause > delta:
                clauses.append((current_clause_tokens, current_clause_timestamps))
                current_clause_tokens = []
                current_clause_timestamps = []
        
        current_clause_tokens.append(tokens[i])
        current_clause_timestamps.append(timestamps[i])
    
    if current_clause_tokens:
        clauses.append((current_clause_tokens, current_clause_timestamps))
    
    return clauses


def separate_punc_level_1(cache, id2punc, valid_punc_start_id=2):
    """
    基于标点ID进行一级断句

    参数:
        cache: 临时存储对齐信息（tokens, timestamps, puncs）
        id2punc: punc id 到字符的映射
        valid_punc_start_id: 有效标点起始 id

    返回:
        断句结果、更新后的 cache
    """
    sentence_num = np.sum([i >= valid_punc_start_id for i in cache["alignment"]['puncs']])
    sentences = []

    if sentence_num > 1:
        for _ in range(sentence_num - 1):
            tokens, timestamps, punc = [], [], None
            while True:
                token = cache["alignment"]["tokens"].pop(0)
                timestamp = cache["alignment"]["timestamps"].pop(0)
                punc_id = cache["alignment"]["puncs"].pop(0)
                tokens.append(token)
                timestamps.append(timestamp)
                if punc_id >= valid_punc_start_id:
                    punc = id2punc[punc_id]
                    sentences.append([tokens, timestamps, punc])
                    break
    return sentences, cache


def separate_pause_level_2(tokens, timestamps, punc, pause_seconds):
    """
    在一级标点切分基础上，进一步按停顿切分句子

    参数:
        tokens: 词列表
        timestamps: 对应时间戳
        punc: 所属标点
        pause_seconds: 停顿时间阈值（秒）

    返回:
        标准格式句子列表
    """
    splits = split_by_pause(tokens, timestamps, delta=pause_seconds)
    sentences = []
    for i, item in enumerate(splits):
        sentence = copy.deepcopy(sentence_structure)
        punc2 = punc if i == len(item) - 1 else ","
        sentence["text"] = "".join(item[0]) + punc2
        sentence["start"] = "%.3f"%item[1][0][0]
        sentence["end"] = "%.3f"%item[1][-1][-1]
        sentences.append(sentence)
    return sentences



class Demacia(Diarization):
    def __init__(self,
                sv_engine:Eres2net_Engine,
                trans_engine:Translator,
                asr_engine:Paraformer_Engine,
                punc_engine:PuncCT_Engine,):
        super().__init__(sv_engine, trans_engine)
        self.asr_engine = asr_engine
        self.punc_engine = punc_engine

        self.sr = 16000
        self.window_sconds = 30
        self.pause_seconds = 5
        self.id2punc = {
                    0:"<unk>",
                    1:"_",
                    2:"，",
                    3:"。",
                    4:"？",
                    5:"、"
                }
        

    def _thread_sentence(self, audio_data, hotwords):
        hotwords = " ".join(hotwords)
        window_size = self.window_sconds * self.sr
        windows = reshape_audio_to_BxT(audio_data, window_size)

        G = batch_inference_generator(self.asr_engine,windows,configs=[{'hotwords':hotwords} for _ in range(len(windows))])
        
        cache = {
            "alignment": {
                "tokens": [],
                "timestamps": [],
                "puncs": [],
            },
            "fbank_buffer":[]
        }
        i = 0
        count = 0
        for item in G:
            progress = i * self.window_sconds;i += 1
            for token, timestamp in item["asr"]:
                timestamp[0] += progress
                timestamp[1] += progress
            
            # 窗结果
            fbank,asr = item["fbank"],item["asr"]

            # 保存对齐
            for token, timestamp in asr:
                cache["alignment"]['tokens'].append(token)
                cache["alignment"]['timestamps'].append(timestamp)

            # 标点断句
            asr_text = " ".join(cache["alignment"]['tokens'])
            if asr_text:
                ###########################################
                taskId = generate_random_string(20)
                self.punc_engine.submit(taskId,asr_text)
                punc_result = self.punc_engine.get(taskId)[1]
                ###########################################
                cache["alignment"]["puncs"] = punc_result

                # 一级分裂：标点
                sentences1, cache = separate_punc_level_1(cache, self.id2punc)

                # 二级分裂：停顿
                sentences2 = []
                for tokens, token_timestamps, punc in sentences1:
                    sentences2.extend(separate_pause_level_2(tokens, token_timestamps, punc, self.pause_seconds))

                # 句子后处理
                for item in sentences2:
                    sentence = copy.deepcopy(sentence_structure)
                    sentence["id"] = f"{count}_{generate_random_string(5)}";count += 1
                    sentence["text"] = item["text"]
                    sentence["start"] = item["start"]
                    sentence["end"] = item["end"]
                    self.sentence_generator.put(sentence)


        if cache["alignment"]["tokens"]:
            tokens, token_timestamps, punc = cache["alignment"]["tokens"], cache["alignment"]["timestamps"], "。"
            sentences2 = separate_pause_level_2(tokens, token_timestamps, punc, self.pause_seconds)
            # 句子后处理
            for item in sentences2:
                sentence = copy.deepcopy(sentence_structure)
                sentence["id"] = f"{count}_{generate_random_string(5)}";count += 1
                sentence["text"] = item["text"]
                sentence["start"] = item["start"]
                sentence["end"] = item["end"]
                self.sentence_generator.put(sentence)
        self.sentence_generator.put(None)


    
if __name__ == "__main__":

    from config import *

    fbank_engine = Fbank_Engine(fbank_config)
    asr_engine = Paraformer_Engine(parajet_config,fbank_engine=fbank_engine)
    punc_engine = PuncCT_Engine(ct_transformer_config)
    sv_engine = Eres2net_Engine(eres2net_config)
    trans_engine = Translator(llm_config)
    fbank_engine.start()
    asr_engine.start()
    punc_engine.start()
    sv_engine.start()

    audio_file = 'examples/test.wav'
    dz = Demacia(
        sv_engine=sv_engine,
        trans_engine=trans_engine,
        asr_engine=asr_engine,
        punc_engine=punc_engine,
    )
    response = dz(audio_file,use_sv=True,trans_language="English")
    for line in response:
        print(line)
        pass

    fbank_engine.stop()
    asr_engine.stop()
    punc_engine.stop()
    sv_engine.stop



    