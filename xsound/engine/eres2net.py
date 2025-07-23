from .base import Engine
from xsound.utils import *

class Eres2net_Engine(Engine):
    def __init__(self, config):
        super().__init__(config)
        
    @staticmethod
    def init_session(config):
        from xsound.core.sv.eres2net.inference import Embedding
        session = Embedding(
            model_dir=config["model_dir"],
            inter_op_num_threads=config["inter_op_num_threads"],
            intra_op_num_threads=config["intra_op_num_threads"],
            use_gpu=config["use_gpu"]
        )
        return session

    @staticmethod
    def inference(session, input_data, config):
        from xsound.core.asr.parajet.front_end import extract_fbank_kaldi
        mel = extract_fbank_kaldi(input_data)
        return session.mel_global_feature(mel)

if __name__ == "__main__":

    from config import eres2net_config

    engine = Eres2net_Engine(eres2net_config)
    engine.start()

    with Timer() as t:
        tasks = []
        for _ in range(200):
            taskId = generate_random_string(200)
            seconds = random.randint(1, 10)
            input_data = np.zeros(int(seconds*16000),dtype='int16')
            engine.submit(taskId,input_data)
            tasks.append(taskId)
        
        for taskId in tasks:
            result = engine.get(taskId)
            print(result.shape)
    
    print(t.interval)
    engine.stop()