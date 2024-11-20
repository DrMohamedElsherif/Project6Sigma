from models.chart import BaseChart


class ChartProcessor:
    def __init__(self, chart: BaseChart):
        self.chart = chart
        self.message = ""
        self.figure = ''

    def process(self):
        return "implement it"

    def getProcessMessage(self):
        return self.message

    def getFigure(self):
        return self.figure
