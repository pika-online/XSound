from .utils import *
from concurrent.futures import ThreadPoolExecutor


def extract_fbank_kaldi(audio_data, sample_rate=16000, num_mel_bins=80):

    opts = knf.FbankOptions()
    opts.frame_opts.samp_freq = sample_rate
    opts.frame_opts.dither = 0
    opts.frame_opts.window_type = "hamming"
    opts.frame_opts.frame_shift_ms = float(10)
    opts.frame_opts.frame_length_ms = float(25)
    opts.mel_opts.num_bins = num_mel_bins
    opts.energy_floor = 0
    opts.frame_opts.snip_edges = False
    opts.mel_opts.debug_mel = False

    fbank = knf.OnlineFbank(opts)
    fbank.accept_waveform(sample_rate, audio_data)
    fbank.input_finished() 

    feats = []
    while fbank.num_frames_ready > len(feats):
        feats.append(fbank.get_frame(len(feats)))

    features = np.stack(feats, axis=0)
    return features

def extract_fbank_batch_kaldi(waveforms, sample_rate=16000, num_mel_bins=80):
    feats = []
    for waveform in waveforms:
        feat = extract_fbank_kaldi(waveform, sample_rate=sample_rate, num_mel_bins=num_mel_bins)
        feats.append(feat)
    return np.array(feats)


def apply_lfr(inputs: np.ndarray, lfr_m: int, lfr_n: int) -> np.ndarray:
    LFR_inputs = []

    T = inputs.shape[0]
    T_lfr = int(np.ceil(T / lfr_n))
    left_padding = np.tile(inputs[0], ((lfr_m - 1) // 2, 1))
    inputs = np.vstack((left_padding, inputs))
    T = T + (lfr_m - 1) // 2
    for i in range(T_lfr):
        if lfr_m <= T - i * lfr_n:
            LFR_inputs.append((inputs[i * lfr_n : i * lfr_n + lfr_m]).reshape(1, -1))
        else:
            # process last LFR frame
            num_padding = lfr_m - (T - i * lfr_n)
            frame = inputs[i * lfr_n :].reshape(-1)
            for _ in range(num_padding):
                frame = np.hstack((frame, inputs[-1]))

            LFR_inputs.append(frame)
    LFR_outputs = np.vstack(LFR_inputs).astype(np.float32)
    return LFR_outputs



def apply_cmvn( inputs: np.ndarray, cmvn) -> np.ndarray:
    """
    Apply CMVN with mvn data
    """
    frame, dim = inputs.shape
    means = np.tile(cmvn[0:1, :dim], (frame, 1))
    vars = np.tile(cmvn[1:2, :dim], (frame, 1))
    inputs = (inputs + means) * vars
    return inputs


def load_cmvn(cmvn_file) -> np.ndarray:
    with open(cmvn_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    means_list = []
    vars_list = []
    for i in range(len(lines)):
        line_item = lines[i].split()
        if line_item[0] == "<AddShift>":
            line_item = lines[i + 1].split()
            if line_item[0] == "<LearnRateCoef>":
                add_shift_line = line_item[3 : (len(line_item) - 1)]
                means_list = list(add_shift_line)
                continue
        elif line_item[0] == "<Rescale>":
            line_item = lines[i + 1].split()
            if line_item[0] == "<LearnRateCoef>":
                rescale_line = line_item[3 : (len(line_item) - 1)]
                vars_list = list(rescale_line)
                continue

    means = np.array(means_list).astype(np.float64)
    vars = np.array(vars_list).astype(np.float64)
    cmvn = np.array([means, vars])
    return cmvn





def pad_feats(feats, max_feat_len: int) -> np.ndarray:
    def pad_feat(feat: np.ndarray, cur_len: int) -> np.ndarray:
        pad_width = ((0, max_feat_len - cur_len), (0, 0))
        return np.pad(feat, pad_width, "constant", constant_values=0)

    feat_res = [pad_feat(feat, feat.shape[0]) for feat in feats]
    feats = np.array(feat_res).astype(np.float32)
    return feats