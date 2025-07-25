from xsound.utils import *
from xsound.engine.eres2net import Eres2net_Engine
from xsound.engine.translator import Translator
from xsound.engine.whisper import *
from .cluster import *
from .base import Diarization,sentence_structure

class Noxus(Diarization):
    def __init__(self,
                sv_engine, 
                trans_engine,
                asr_engine:Whisper_Engine):
        super().__init__(sv_engine, trans_engine)
        self.asr_engine = asr_engine

    def _thread_sentence(self, audio_data, hotwords):
        print(f"_thread_sentence [start]")
        taskId = generate_random_string(20)
        hotwords = " ".join(hotwords)
        self.asr_engine.submit(taskId,audio_data,config={"hotwords":hotwords})
        count = 0
        while True:
            item = self.asr_engine.get(taskId)
            if item in [FLAG_END,FLAG_ERROR]:
                break
            print(item)
            sentence = copy.deepcopy(sentence_structure)
            sentence["id"] = f"{count}_{generate_random_string(5)}";count += 1
            sentence["text"] = item["text"]
            sentence["start"] = "%.3f"%item["start"]
            sentence["end"] = "%.3f"%item["end"]
            self.sentence_generator.put(sentence)
            
        self.sentence_generator.put(None)
        print(f"_thread_sentence [end]")
    
from config import *
async def main():


    asr_engine = Whisper_Engine(whisper_config)
    sv_engine = Eres2net_Engine(eres2net_config)
    trans_engine = Translator(llm_config)
    asr_engine.start()
    sv_engine.start()

    audio_file = 'test1.wav'
    dz = Noxus(
        sv_engine=sv_engine,
        trans_engine=trans_engine,
        asr_engine=asr_engine,
    )
    response = async_generator_wrapper(dz(audio_file,use_sv=False,trans_language=""))
    async for line in response:
        print(line)


    asr_engine.stop()
    sv_engine.stop

if __name__ == "__main__":
    asyncio.run(main())
    