import sys
import time
class ProgressBar:
    def __init__(self, count = 100):
        self.count = count
        self.curr = 0
        self.start = time.time()
        self.remain = count / 2
        self.last = time.time()

    def update(self):
        if self.curr == 0:
            remaining = self.remain
        else:
            remaining = (time.time() - self.last) * (self.count - self.curr)
        self.remain = self.remain + (remaining - self.remain) * (1/12)
        min, sec = divmod(self.remain, 60)
        string = f"{self.curr}/{self.count} {int(min):02}:{int(sec):02}"
        print(string, end=' \r', file=sys.stdout, flush=True)

    def increment(self):
        self.curr += 1
        self.update()
        self.last = time.time()

    def set(self, curr = 0, count = 100):
        self.count = count
        self.curr = curr
        self.start = time.time()
        self.remain = count / 2
        self.update()
        self.last = time.time()
