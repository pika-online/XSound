from .utils import *
from xsound.core.ort_session import *

class CT_Transformer:


    def __init__(
        self,
        model_dir,
        intra_op_num_threads = 1,
        inter_op_num_threads = 1,
        use_gpu = True,
    ):

        self.config_file = os.path.join(model_dir, "config.yaml")
        with open(str(self.config_file), "rb") as f:
            self.config = yaml.load(f, Loader=yaml.Loader)

        self.token_list = os.path.join(model_dir, "tokens.json")
        with open(self.token_list, "r", encoding="utf-8") as f:
            self.token_list = json.load(f)
        

        self.vocab = {}
        for i, token in enumerate(self.token_list):
            self.vocab[token] = i
        self.unk_symbol = self.token_list[-1]
        self.unk_id = self.vocab[self.unk_symbol]

        self.punc_list = self.config["model_conf"]["punc_list"]
        self.punc2id, self.id2punc = {}, {}
        for i,punc in enumerate(self.punc_list):
            self.punc2id[punc] = i
            self.id2punc[i] = punc

        self.session = OrtInferSession(
            model_file=f"{model_dir}/model.onnx",
            intra_op_num_threads=intra_op_num_threads,
            inter_op_num_threads=inter_op_num_threads,
            use_gpu=use_gpu
        )
        print("初始化成功")


    def infer(self,text,text_lengths):
        return self.session([text,text_lengths])

    def __call__(self, text, split_size=20):

        
        period = 0
        


        split_text = code_mix_split_words(text)
        # print(split_text)
        split_text_id = [self.vocab.get(token,self.unk_id) for token in split_text]
        mini_sentences = split_to_mini_sentence(split_text, split_size)
        mini_sentences_id = split_to_mini_sentence(split_text_id, split_size)
        assert len(mini_sentences) == len(mini_sentences_id)
        cache_sent = []
        cache_sent_id = []
        new_mini_sentence = ""
        new_mini_sentence_punc = []
        cache_pop_trigger_limit = 200
        for mini_sentence_i in range(len(mini_sentences)):
            mini_sentence = mini_sentences[mini_sentence_i]
            mini_sentence_id = mini_sentences_id[mini_sentence_i]
            mini_sentence = cache_sent + mini_sentence
            mini_sentence_id = np.array(cache_sent_id + mini_sentence_id, dtype="int32")
            data = {
                "text": mini_sentence_id[None, :],
                "text_lengths": np.array([len(mini_sentence_id)], dtype="int32"),
            }
            try:
                outputs = self.infer(data["text"], data["text_lengths"])
                y = outputs[0]
                punctuations = np.argmax(y, axis=-1)[0]
                assert punctuations.size == len(mini_sentence)
            except :
                print("error")

            # Search for the last Period/QuestionMark as cache
            if mini_sentence_i < len(mini_sentences) - 1:
                sentenceEnd = -1
                last_comma_index = -1
                for i in range(len(punctuations) - 2, 1, -1):
                    if (
                        self.punc_list[punctuations[i]] == "。"
                        or self.punc_list[punctuations[i]] == "？"
                    ):
                        sentenceEnd = i
                        break
                    if last_comma_index < 0 and self.punc_list[punctuations[i]] == "，":
                        last_comma_index = i

                if (
                    sentenceEnd < 0
                    and len(mini_sentence) > cache_pop_trigger_limit
                    and last_comma_index >= 0
                ):
                    # The sentence it too long, cut off at a comma.
                    sentenceEnd = last_comma_index
                    punctuations[sentenceEnd] = period
                cache_sent = mini_sentence[sentenceEnd + 1 :]
                cache_sent_id = mini_sentence_id[sentenceEnd + 1 :].tolist()
                mini_sentence = mini_sentence[0 : sentenceEnd + 1]
                punctuations = punctuations[0 : sentenceEnd + 1]

            new_mini_sentence_punc += [int(x) for x in punctuations]
            words_with_punc = []
            for i in range(len(mini_sentence)):
                if i > 0:
                    if (
                        len(mini_sentence[i][0].encode()) == 1
                        and len(mini_sentence[i - 1][0].encode()) == 1
                    ):
                        mini_sentence[i] = " " + mini_sentence[i]
                words_with_punc.append(mini_sentence[i])
                if self.punc_list[punctuations[i]] != "_":
                    words_with_punc.append(self.punc_list[punctuations[i]])
            new_mini_sentence += "".join(words_with_punc)
            # Add Period for the end of the sentence
            new_mini_sentence_out = new_mini_sentence
            new_mini_sentence_punc_out = new_mini_sentence_punc
            if mini_sentence_i == len(mini_sentences) - 1:
                if new_mini_sentence[-1] == "，" or new_mini_sentence[-1] == "、":
                    new_mini_sentence_out = new_mini_sentence[:-1] + "。"
                    new_mini_sentence_punc_out = new_mini_sentence_punc[:-1] + [period]
                elif new_mini_sentence[-1] != "。" and new_mini_sentence[-1] != "？":
                    new_mini_sentence_out = new_mini_sentence + "。"
                    new_mini_sentence_punc_out = new_mini_sentence_punc[:-1] + [period]
        return new_mini_sentence_out, new_mini_sentence_punc_out








if __name__ == "__main__":

    model = CT_Transformer(
        model_dir="models/punc/sherpa-onnx-punct-ct-transformer-zh-en-vocab272727-2024-04-12"
    )

    for _ in range(20):
        with Timer() as t:
            input_data = "hello 大 家 好 我 的 名 字 叫李华来自广东深圳很高兴来到这里"
            x = model(input_data)
        print(x) 
        print(t.interval)
