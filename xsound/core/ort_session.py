import numpy as np
import onnxruntime as ort 

class OrtInferSession:
    def __init__(self,
                 model_file,
                 intra_op_num_threads=1,
                 inter_op_num_threads=1,
                 use_gpu=False,
                 execution_mode=ort.ExecutionMode.ORT_PARALLEL,
                 ):

        session_options = ort.SessionOptions()
        session_options.intra_op_num_threads = intra_op_num_threads   # 单推理线程数
        session_options.inter_op_num_threads = inter_op_num_threads   # 多推理任务线程数
        session_options.execution_mode = execution_mode
        # session_options.log_severity_level = 0
        # session_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        self.session = ort.InferenceSession(model_file, sess_options=session_options, providers=["CPUExecutionProvider" if not use_gpu else "CUDAExecutionProvider"])

        self.input_names = [v.name for v in self.session.get_inputs()]
        self.output_names = [v.name for v in self.session.get_outputs()]


    def __call__(self, input_content) -> np.ndarray:
        input_dict = dict(zip(self.input_names, input_content))
        try:
            result = self.session.run(self.output_names, input_dict)
            return result
        except Exception as e:
            raise e
        
    def get_input_names(
        self,
    ):
        return [v.name for v in self.session.get_inputs()]

    def get_output_names(
        self,
    ):
        return [v.name for v in self.session.get_outputs()]
