import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QFont, QColor, QPainter
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
import argparse
import subprocess
from parse_data.parse import parse
from threading import Thread
from sig_process import processing
from garden_game import game_start

class ZenGardenGame(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Zen Garden Game")
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.main_layout = QVBoxLayout()
        self.central_widget.setLayout(self.main_layout)

        self.game_widget = GameWidget()
        self.main_layout.addWidget(self.game_widget)

        self.show()


class GameWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.concentration_low = False
        self.concentration_medium = False
        self.concentration_high = False
        self.plant_size = 50

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_game)
        self.timer.start(1000)
        self.endgame = False

    def paintEvent(self, event):
        painter = QPainter(self)
        #painter.setRenderHint(QPainter.Antialiasing)

        # Draw the plant
        if self.plant_size <= 300:
            painter.setBrush(QColor(0, 255, 0))
            painter.drawEllipse(self.width() // 2 - self.plant_size // 2, self.height() // 2 - self.plant_size // 2,
                                self.plant_size, self.plant_size)
        else:
            self.endgame = True
            painter.setBrush(QColor(255, 255, 255))
            painter.drawEllipse(self.width() // 2 - self.plant_size // 2, self.height() // 2 - self.plant_size // 2,
                                self.plant_size, self.plant_size)
            painter.setPen(QColor(255, 0, 0))
            painter.setFont(QFont('Arial', 30))
            painter.drawText(self.rect(), 0x0081, "WIN")

    def update_game(self):
        concentration_level = np.load("status.npy")
        if self.endgame == False:
            if concentration_level == "low":
                if self.plant_size >= 10:
                    self.plant_size *= 0.8
                print("low", self.plant_size)
            elif concentration_level == "medium":
                self.plant_size *= 1.2
                print("med", self.plant_size)
            elif concentration_level == "high":
                self.plant_size *= 1.5
                print("high", self.plant_size)

        self.update()

class MyMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Real-time Frequency Response Plot")
        self.setGeometry(200, 100, 1920, 1080)

        # Create main layout
        layout = QVBoxLayout()

        # Create a Matplotlib figure
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        # Create a widget to hold the layout
        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        # Initialize the plots
        self.init_plots()

        # Timer for updating the plots
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_plots)
        self.timer.start(1000)  # Update plots every 300 milliseconds

    def init_plots(self):
        # Initialize the subplots for each channel
        self.axes = []
        for i in range(8):
            ax = self.figure.add_subplot(4, 2, i+1)
            ax.set_title(f'Channel {i+1}')
            ax.set_xlabel('Frequency')
            ax.set_ylabel('Magnitude')
            self.axes.append(ax)

    def update_plots(self):
        print("update")
        # Get new frequency response data from the processing function
        frequency_responses = processing()
        print(np.max(frequency_responses[2]))
        if np.max(frequency_responses[2]) > 100:
            status = "medium"
            print("keep going, you are concentrating!")
        else:
            status = "low"
            print("wtf are you doing?")
        np.save("status.npy", np.array(status))
        # Clear the existing plots and plot the new frequency responses for each channel
        for ax, response, i in zip(self.axes, frequency_responses, range(8)):
            ax.clear()
            ax.plot(response[0], response[1])
            ax.set_title(f'Channel {i+1}')
            ax.set_xlabel('Frequency')
            ax.set_ylabel('Magnitude')
        self.figure.subplots_adjust(hspace=1, wspace=0.5)
        # Update the canvas
        self.canvas.draw()

    def processing(self):
        # Placeholder for processing function, replace this with your actual processing logic
        frequency_responses = processing()
        #num_channels = 8
        #frequencies = np.linspace(0, 10, 100)
        #frequency_responses = []
        #for _ in range(num_channels):
            #magnitude = np.random.rand(100)
            #frequency_responses.append((frequencies, magnitude))
        return frequency_responses

if __name__ == "__main__":
    sys.path.append('./parse_data')
    from parse_data.parse import parse
    parser = argparse.ArgumentParser(description='Script to process a file at a custom location')
    parser.add_argument('file', metavar='FILE', type=str, help='Path to the file to process')
    args = parser.parse_args()
    target = args.file
    target_folder = f"../../../../OpenBCI_GUI/Recordings/OpenBCISession_{target}/"
    output = subprocess.check_output(f"ls -t {target_folder} | head -n 1", shell=True)
    file_name = output.decode("utf-8")
    target_file = target_folder + file_name[:-1] # remove the new line

    t1 = Thread(target = parse, args = (target_file,))
    t1.start()

    app = QApplication(sys.argv)
    window = MyMainWindow()
    game = ZenGardenGame()
    window.show()

    sys.exit(app.exec_())
