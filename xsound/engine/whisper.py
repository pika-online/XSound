from .base import Engine, FLAG_END, FLAG_ERROR
from xsound.utils import *

class Whisper_ENGINE(Engine):
    def __init__(self, config):
        super().__init__(config)
        
    @staticmethod
    def init_session(config):
        from faster_whisper import WhisperModel
        session = WhisperModel(
            model_size_or_path=config["model_dir"],
            device=config['device'],
            compute_type=config['compute_type'],
        )
        return session

    @staticmethod
    def inference(session, input_data, config):
        language = config.get('language', None)
        task = config.get('task', 'transcribe')
        hotwords = config.get('hotwords', [])

        # 调用模型进行识别
        segments, info = session.transcribe(
            input_data,
            condition_on_previous_text=False,
            language=language,
            task=task,
            hotwords= hotwords
        )

        for i, segment in enumerate(segments):
            yield {
                'start': segment.start,
                'end': segment.end,
                'text': segment.text,
            }
        yield FLAG_END
    
if __name__ == "__main__":

    from config import whisper_config

    engine = Whisper_ENGINE(whisper_config)
    engine.start()

    with Timer() as t:
        input_data = "examples/test.wav"
        taskId = generate_random_string(20)
        engine.submit(taskId,input_data)

        while True:
            result = engine.get(taskId)
            print(result)
            if result in [FLAG_END,FLAG_ERROR]:
                break

    
    print(t.interval)
    engine.stop()