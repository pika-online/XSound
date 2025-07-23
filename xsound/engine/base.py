import multiprocessing as mp
import threading
import queue
from xsound.utils import *

# 结果标志
FLAG_END = "<END>"
FLAG_ERROR = "<ERROR>"

class Engine:
    def __init__(self, config):
        """
        初始化 Engine 类
        :param config: 配置字典，包含 engine 类型、最大工作数、实例配置等
        """
        self.config = config
        self.engine_type = self.config['engine']  # 'mp' or 'mt'
        self.max_workers = self.config['num_workers']
        self.instance_config = self.config['instance']
        self.stream = self.config['stream'] # 是否流式返回

        # 初始化任务队列和结果队列
        if self.engine_type == 'mp':
            self.task_queue = mp.Queue()
            self.result_queue = mp.Queue()
        elif self.engine_type == 'mt':
            self.task_queue = queue.Queue()
            self.result_queue = queue.Queue()
        else:
            raise ValueError(f"Unsupported engine type: {self.engine_type}")

        self.workers = []
        self.task_results = {}  # 每个 task_id 映射一个 queue.Queue()
        self.result_lock = threading.Lock()

    def _collect_results(self):
        """
        后台线程函数，持续从结果队列中收集结果，存入 task_results 中
        """
        while True:
            try:
                item = self.result_queue.get()
                if item == "STOP":
                    break
                task_id, result = item
                with self.result_lock:
                    if task_id in self.task_results:
                        self.task_results[task_id].put(result)
            except Exception:
                continue
        print("[END] Result collection thread exited.")

    @staticmethod
    def init_session(config):
        """
        子类应实现：根据配置初始化推理实例
        """
        pass

    @staticmethod
    def inference(instance, input_data, config):
        """
        子类应实现：根据输入执行推理
        """
        pass

    @staticmethod
    def worker_process(worker_id, cls, stream, instance_config, task_queue, result_queue):
        """
        工作进程/线程函数：处理任务，调用 inference 并将结果回传
        """
        print(f"[START] --> Worker-{worker_id}")
        session = cls.init_session(instance_config)
        print(f"[READY] --> Worker-{worker_id}")
        result_queue.put("ready")

        while True:
            try:
                task = task_queue.get()
            except Exception:
                continue

            if task is None:
                break  # 接收到退出信号

            task_id, input_data, config = task
            try:
                response = cls.inference(session, input_data, config)
                if stream:
                    for item in response:
                        result_queue.put((task_id, item))
                    result_queue.put((task_id, FLAG_END))
                else:
                    result_queue.put((task_id, response))
            except Exception:
                traceback.print_exc()
                result_queue.put((task_id, FLAG_ERROR))

        print(f"[END] --> Worker-{worker_id}")

    def start(self):
        """
        启动工作线程/进程和结果收集线程
        """
        cls = self.__class__
        for worker_id in range(self.max_workers):
            if self.engine_type == 'mp':
                worker = mp.Process(
                    target=Engine.worker_process,
                    args=(worker_id, cls, self.stream, self.instance_config, self.task_queue, self.result_queue),
                    daemon=True
                )
            elif self.engine_type == 'mt':
                worker = threading.Thread(
                    target=Engine.worker_process,
                    args=(worker_id, cls, self.stream, self.instance_config, self.task_queue, self.result_queue),
                    daemon=True
                )
            worker.start()
            self.workers.append(worker)

        # 等待所有 worker 准备就绪
        for _ in range(self.max_workers):
            self.result_queue.get()

        # 启动结果收集线程
        self.result_collector = threading.Thread(target=self._collect_results, daemon=True)
        self.result_collector.start()
        print("[INFO] Engine started successfully.")

    def submit(self, task_id, input_data, config={}):
        """
        提交任务
        :param task_id: 任务唯一标识
        :param input_data: 输入数据
        :param config: 可选配置
        """
        with self.result_lock:
            self.task_results[task_id] = queue.Queue()
        self.task_queue.put((task_id, input_data, config))

    def get(self, task_id, timeout=10):
        """
        获取任务结果
        :param task_id: 对应任务 ID
        :param timeout: 等待超时时间
        :return: 推理结果或 FLAG_ERROR
        """
        try:
            result = self.task_results[task_id].get(timeout=timeout)
        except Exception:
            result = FLAG_ERROR
        # 释放资源
        if result is FLAG_ERROR or result is FLAG_END or not self.stream:
            with self.result_lock:
                if task_id in self.task_results:
                    del self.task_results[task_id]
        return result

    def stop(self):
        """
        停止所有工作线程/进程和收集线程
        """
        # 通知 worker 停止
        for _ in self.workers:
            self.task_queue.put(None)
        for worker in self.workers:
            worker.join()

        # 停止结果收集线程
        self.result_queue.put("STOP")
        self.result_collector.join()
        print("[END] Engine shutdown.")

def batch_inference_generator(engine:Engine,batch_data:list,configs:list=[]):
    if not configs:
        configs = [{} for _ in range(len(batch_data))]
    # PUT
    tasks = []
    for input_data,config in zip(batch_data,configs):
        taskId = generate_random_string(20)
        engine.submit(taskId,input_data,config)
        tasks.append(taskId)
    # GET
    for taskId in tasks:
        yield engine.get(taskId)
        
