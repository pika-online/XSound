from .utils import *
from xsound.core.ort_session import *

class Embedding:

    def __init__(
        self,
        model_dir,
        intra_op_num_threads = 1,
        inter_op_num_threads = 1,
        use_gpu=False
    ):
        self.session = OrtInferSession(
            model_file=f"{model_dir}/model.onnx",
            intra_op_num_threads=intra_op_num_threads,
            inter_op_num_threads=inter_op_num_threads,
            use_gpu=use_gpu
        )

    def unsqueeze(self,x,axis):
        return np.expand_dims(x,axis=axis)

    def wave2embedding(self,x,norm=True,max_len=160000):
        if len(x)>max_len:x = x[:max_len]
        mel = extract_fbank_kaldi(x)
        return self.mel2embedding(mel,norm)

    def mel2embedding(self, mel, norm=True):
        if norm:
            mel -= np.mean(mel, axis=0)
        mel = self.unsqueeze(mel,0)
        return self.session([mel])[0]
    
    def mel_global_feature(self, mel, local_feature_size=50, local_max_feature_n=10, local_min_feature_n=1):
        L = mel.shape[0]

        # Step 1: 如果 mel 长度小于一个局部特征所需的帧数，补零
        if L < local_feature_size:
            pad_len = local_feature_size - L
            mel = np.pad(mel, ((0, pad_len), (0, 0)), mode='constant')
            L = local_feature_size

        # Step 2: 计算最多能提取多少个局部特征
        max_possible_n = L // local_feature_size
        feature_n = min(max_possible_n, local_max_feature_n)
        feature_n = max(feature_n, local_min_feature_n)

        # Step 3: 均匀采样起始位置
        stride = (L - local_feature_size) / (feature_n - 1) if feature_n > 1 else 0
        start_indices = [int(i * stride) for i in range(feature_n)]

        # Step 4: 提取局部特征并生成 embedding
        local_embeddings = []
        for start in start_indices:
            local_mel = mel[start:start + local_feature_size]
            emb = self.mel2embedding(local_mel)  # shape: (1, embedding_dim)
            local_embeddings.append(emb[0])      # remove batch dim

        # Step 5: 求局部声纹均值作为全局声纹
        global_embedding = np.mean(local_embeddings, axis=0)
        return global_embedding


    
if __name__ == "__main__":

    model = Embedding("models/sv/speech_eres2net_large_sv_zh-cn_3dspeaker_16k_onnx")

    for _ in range(20):
        with Timer() as t:
            input_data = np.zeros([16000*10],dtype='int16')
            x = model.wave2embedding(input_data)[0]
        print(x.shape) 
        print(t.interval)