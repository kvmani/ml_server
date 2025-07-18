import multiprocessing

bind = "0.0.0.0:5000"
workers = max(2, multiprocessing.cpu_count())
threads = 4
worker_class = "gthread"
accesslog = "-"
errorlog = "-"
