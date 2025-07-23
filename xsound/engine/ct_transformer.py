from .base import Engine
from xsound.utils import *

class PuncCT_Engine(Engine):
    def __init__(self, config):
        super().__init__(config)
        
    @staticmethod
    def init_session(config):
        from xsound.core.punc.ct_transformer.inference import CT_Transformer
        session = CT_Transformer(
            model_dir=config["model_dir"],
            inter_op_num_threads=config["inter_op_num_threads"],
            intra_op_num_threads=config["intra_op_num_threads"],
            use_gpu=config["use_gpu"]
        )
        return session

    @staticmethod
    def inference(session, input_data, config):
        return  session(input_data)
    
if __name__ == "__main__":

    from config import ct_transformer_config

    engine = PuncCT_Engine(ct_transformer_config)
    engine.start()

    with Timer() as t:
        tasks = []
        for _ in range(20):
            taskId = generate_random_string(20)
            input_data = "hello 大 家 好 我 的 名 字 叫李华来自广东深圳很高兴来到这里"
            engine.submit(taskId,input_data)
            tasks.append(taskId)
        
        for taskId in tasks:
            result = engine.get(taskId)
            print(result)
    
    print(t.interval)
    engine.stop()