from xsound.utils import *


def cif(hidden, alphas, threshold=1.0,max_len=100):
    B, F, C = hidden.shape

    # Padding: Add dummy frame and alpha
    hidden = np.concatenate((hidden, np.zeros((B, 1, C), dtype='float32')), axis=1)
    F += 1
    pad_alpha = np.full((B, 1), 0.45, dtype='float32')
    alphas = np.concatenate((alphas.squeeze(-1), pad_alpha), axis=1)

    integrate = np.zeros((B,), dtype='float32')
    frame = np.zeros((B, C), dtype='float32')

    final_frames = [[] for _ in range(B)]

    for t in range(F):
        alpha_t = alphas[:, t]
        distribution_completion = threshold - integrate
        integrate += alpha_t

        flags = integrate >= threshold
        cur = np.where(flags, distribution_completion, alpha_t)
        remains = alpha_t - cur

        # Add weighted contribution to frame
        frame += (cur[:, None] * hidden[:, t, :])

        for b in range(B):
            if flags[b]:
                final_frames[b].append(frame[b].copy())
                frame[b] = remains[b] * hidden[b, t, :]

        integrate = np.where(flags, integrate - threshold, integrate)

    # Finalize output
    final_frame_list = []
    max_label_lens = []

    for b in range(B):
        label_len = int(np.round(alphas[b].sum()))
        max_label_lens.append(label_len)
        frames = final_frames[b]
        if label_len > len(frames):
            frames.append(np.zeros((C,), dtype='float32'))
        final_frame_list.append(np.stack(frames, axis=0))

    # Pad to the same length
    padded_frames = np.zeros((B, max_len, C), dtype='float32')
    for b in range(B):
        length = final_frame_list[b].shape[0]
        padded_frames[b, :length, :] = final_frame_list[b]

    return padded_frames, max_label_lens



def cif2(tokens:list,
         alphas,
         threshold=1.0,
         audio_seconds=30,
         start_end_format=False,
         delta=0.1):

    intergrate = 0.
    ans1 = []
    num = len(alphas)
    for i in range(len(alphas)):
        intergrate += alphas[i]
        if intergrate>=threshold:
            ans1.append([tokens.pop(0),round(i/num*audio_seconds,3)])
            intergrate -= threshold
    
    if start_end_format:
        ans2 = []
        pre_token = [None, None]
        for token,t in ans1:
            start = max(pre_token[1],t-delta) if pre_token[1] else max(0,t-delta) 
            end = min(audio_seconds, t+delta) 
            ans2.append([token,[start,end]])
            pre_token = [start,end]
    return ans2 if start_end_format else ans1


def subword_merge(alignment):
    cache = None 
    ans = []
    for token, timestamp in alignment:
        if "@@" in token:
            token_clean = token.replace("@@","")
            if not cache:
                cache = [token_clean,timestamp]
            else:
                cache[0] += token_clean
                cache[1][1] = timestamp[1]
        else:
            if cache:
                cache[0] += token
                cache[1][1] = timestamp[1]
                ans.append(cache)
                cache = None
            else:
                ans.append([token,timestamp])
    return  ans


