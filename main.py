import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout

class ClothingApp(QWidget):
    def __init__(self):
        super().__init__()

        # Set window properties
        self.setWindowTitle('Clothing Manufacturing Manager')
        self.setGeometry(100, 100, 400, 200)

        # Layout and widgets
        layout = QVBoxLayout()

        self.label = QLabel('Welcome to the Clothing Manufacturing Manager App', self)
        layout.addWidget(self.label)

        self.setLayout(layout)

if __name__ == '__main__':
    app = QApplication(sys.argv)

    window = ClothingApp()
    window.show()

    sys.exit(app.exec_())
