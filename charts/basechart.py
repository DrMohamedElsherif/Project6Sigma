from models.chart import Chart

class BaseChart:
    def __init__(self, chart: Chart):
        self.chart = chart
        self.message = ""
        self.figure = ''

    def process(self):
        return "implement it"

    def getProcessMessage(self):
        return self.message

    def getFigure(self):
        return self.figure

