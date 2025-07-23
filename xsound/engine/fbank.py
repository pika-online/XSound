from .base import Engine
from xsound.utils import *

class Fbank_Engine(Engine):
    def __init__(self, config):
        super().__init__(config)
        
    @staticmethod
    def init_session(config):
        return None

    @staticmethod
    def inference(session, input_data, config={}):
        from xsound.core.asr.parajet.front_end import extract_fbank_kaldi
        return  extract_fbank_kaldi(input_data)

if __name__ == "__main__":

    from config import fbank_config

    engine = Fbank_Engine(fbank_config)
    engine.start()

    with Timer() as t:
        tasks = []
        for _ in range(40):
            taskId = generate_random_string(20)
            input_data = np.zeros(16000,dtype='int16')
            engine.submit(taskId,input_data)
            tasks.append(taskId)
        
        for taskId in tasks:
            result = engine.get(taskId)
            print(result.shape)
    
    print(t.interval)
    engine.stop()