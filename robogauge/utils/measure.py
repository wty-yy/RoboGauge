class Average:
    def __init__(self):
        self.avg = 0.0
        self.count = 0
    
    def update(self, value: float):
        self.avg += (value - self.avg) / (self.count + 1)
        self.count += 1
        return self.avg
    
    @property
    def mean(self):
        return self.avg
