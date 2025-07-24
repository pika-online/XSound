from xsound.utils import *
from .fbank import Fbank_Engine
from xsound.core.asr.parajet.front_end import extract_fbank_kaldi


class Paraformer_Engine:
    
    def __init__(self,config:dict,fbank_engine:Fbank_Engine=None):
        
        self.config = config
        self.engine = config['engine']
        if self.engine == 'mt':
            self.inputs1 = queue.Queue()
            self.inputs2 = queue.Queue()
            self.outputs = queue.Queue()
        elif self.engine == 'mp':
            self.inputs1 = multiprocessing.Queue()
            self.inputs2 = multiprocessing.Queue()
            self.outputs = multiprocessing.Queue()
        self.fbank_engine = fbank_engine

    
        self.num_workers = config["num_workers"]
        self.batch_wait_seconds = config["batch_wait_seconds"]
        self.B, self.T = config['instance']["feed_fixed_shape"]
        self.empty_fbank = extract_fbank_kaldi(np.zeros(self.T,dtype="int16"))

        self.stop_event = threading.Event()
        self.thread_backend_aggregation = threading.Thread(target=self._backend_aggregation,daemon=True)
        self.thread_backend_summary = threading.Thread(target=self._backend_summary,daemon=True)
        self.workers = []
        self.results = {}
        self.lock = threading.Lock()
        
    def _now(self):
        return time.time()

    @staticmethod
    def _init_session(config):
        from xsound.core.asr.parajet.inference import SeacoParaformer
        session = SeacoParaformer(
            model_dir=config['instance']['model_dir'],
            intra_op_num_threads=config['instance']['intra_op_num_threads'],
            inter_op_num_threads=config['instance']['inter_op_num_threads'],
            use_gpu=config['instance']["use_gpu"],
            fixed_shape=config['instance']["feed_fixed_shape"]
        )
        return  session

    
    @staticmethod
    def worker_process(id,cls,config,task_queue, result_queue, batch_size, empty_fbank):
        print(f'开始进程:{id}')

        session = cls._init_session(config)
        result_queue.put('ready')
        print('完成模型加载')

        while True:
            try:
                item = task_queue.get()
            except:
                continue
            
            if item is None:
                break 

            taskIds, audio_data, configs = item
            size = len(taskIds)
            hotwords = [config['hotwords'] for config in configs]

            # 整理成 fixed_shape_input
            taskIds_fixed = ['' for _ in range(batch_size)]
            waveforms_fixed = [empty_fbank for _ in range(batch_size)]
            hotwords_fixed = ['' for _ in range(batch_size)]
            for i in range(size):
                taskIds_fixed[i] = taskIds[i]
                waveforms_fixed[i] = audio_data[i]
                hotwords_fixed[i] = hotwords[i]

    
            result = session(waveforms_fixed, hotwords_fixed,audio_type="feat")
            fbank = result["feats"]["fbank"]
            asr = result["asr"]
            print(f"推理耗时：{result['time_cost']}, 稀疏度: {size}/{batch_size}")

            # 提取fbank, asr结果
            for taskId,a,b in zip(taskIds_fixed,fbank,asr):
                if taskId:
                    result_queue.put((taskId,
                                      {
                                          "fbank":a,
                                          "asr":b
                                      }))


        print(f'退出进程:{id}')


    def _extract_fbank_batch(self,waveforms):

        tasks = []
        results = []
        for input_data  in waveforms:
            taskId = generate_random_string(20)
            self.fbank_engine.submit(taskId,input_data)
            tasks.append(taskId)

        for taskId in tasks:
            result = self.fbank_engine.get(taskId)
            results.append(result)
        return results
        


    # 任务聚合线程
    def _backend_aggregation(self):

        print("[START]: _backend_aggregation")

        a,b,c,d = [],[],[],[] # 聚合变量
        while not self.stop_event.is_set():

            
            # 限定时间内抓取batch
            while 1:
                try:
                    item = self.inputs1.get(timeout=self.batch_wait_seconds)
                    # print("get_task",time.time())
                    timestamp, taskId, waveform, config = item
                    a.append(timestamp)
                    b.append(taskId)
                    c.append(waveform)
                    d.append(config)
                except queue.Empty:
                    break

            # 处理batch
            # print("build_batch[start]",time.time())
            while len(a):
                _a,a = a[:self.B], a[self.B:]
                _b,b = b[:self.B], b[self.B:]
                _c,c = c[:self.B], c[self.B:]
                _d,d = d[:self.B], d[self.B:]

                _c = self._extract_fbank_batch(_c)
                self.inputs2.put((_b,_c,_d))
            # print("build_batch[end]",time.time())


        print("[END]: _backend_aggregation")


    # 结果整合线程
    def _backend_summary(self):

        print("[START]: _backend_summary")
        while not self.stop_event.is_set():
            try:
                item = self.outputs.get(timeout=1e-3)
                taskId, result = item 
                with self.lock:
                    self.results[taskId].put(result)
            except queue.Empty:
                continue

        print("[END]: _backend_summary")


    def submit(self,taskId,input_data,config={}):
        # print("submit[start]",time.time())
        self.inputs1.put((time.time(),taskId,input_data,config))
        if taskId not in self.results:
            self.results[taskId] = queue.Queue()
        # print("submit[end]",time.time())

    def get(self,taskId,timeout=None):
        res = self.results[taskId].get(timeout=timeout)
        if not self.results[taskId].qsize():
            with self.lock:
                del self.results[taskId]
        return res



    def start(self):
        cls = self.__class__
        for i in range(self.num_workers):
            if self.engine=='mt':
                p = threading.Thread(target=self.worker_process,args=(i,cls,self.config,self.inputs2,self.outputs,self.B,self.empty_fbank),daemon=True)
            if self.engine=='mp':
                p = multiprocessing.Process(target=self.worker_process,args=(i,cls,self.config,self.inputs2,self.outputs,self.B,self.empty_fbank),daemon=True)
            p.start()
            self.workers.append(p)
        for i in range(self.num_workers):
            self.outputs.get()

        self.thread_backend_aggregation.start()
        self.thread_backend_summary.start()
        print('启动成功')
        
        

    def stop(self):
        self.stop_event.set()
        for i in range(self.num_workers):
            self.inputs2.put(None)
        for worker in self.workers:
            worker.join()
        self.thread_backend_aggregation.join()
        self.thread_backend_summary.join()
        print('关闭成功')


if __name__ == "__main__":

    from config import *
    from .base import batch_inference_generator

    fbank_engine = Fbank_Engine(fbank_config)
    fbank_engine.start()
    asr_engine = Paraformer_Engine(parajet_config,fbank_engine=fbank_engine)
    asr_engine.start()

    input_data = np.zeros(asr_engine.T,dtype='int16')
    audio_data = read_audio_file("examples/short.mp3")
    input_data[:len(audio_data)] = audio_data
    
    with Timer() as t:
        taskId = generate_random_string(10)
        asr_engine.submit(taskId,input_data,config={"hotwords":""})
        asr_engine.get(taskId)
    print(t.interval)

    asr_engine.stop()
    fbank_engine.stop()

