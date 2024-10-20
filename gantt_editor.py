import datetime
import sys
import os

import PySide6
from PySide6.QtCore import Slot, Signal, QRect
from PySide6.QtGui import QImage, QFont, QColor, QPalette, QBrush
from PySide6.QtWidgets import QMainWindow, QSplitter, QFrame, QVBoxLayout, QLabel, QSizePolicy, QHBoxLayout, \
    QPushButton, QLineEdit, QScrollArea, QFileDialog, QMessageBox, QApplication, QFontDialog, QColorDialog, \
    QRadioButton, QDoubleSpinBox, QComboBox

import ganttmaker


class FloatOptionDelegate(QHBoxLayout):
    changedProperty = Signal()

    def __init__(self, label: str, default: float):
        super().__init__()
        self.label = QLabel(label)
        self.input = QLineEdit()
        self.input.setPlaceholderText(str(default))
        self.addWidget(self.label)
        self.addWidget(self.input)
        self.default = default

    @property
    def value(self) -> float:
        try:
            return float(self.input.text())
        except ValueError:
            return self.default

    @value.setter
    def value(self, value: float):
        self.default = value
        self.input.setText(str(self.default))
        self.changedProperty.emit()


class FontOptionDelegate(QHBoxLayout):
    changedProperty = Signal()

    def __init__(self, label: str, default_font: QFont, default_color: QColor):
        super().__init__()
        self.label = QLabel(label)
        self.input = QFontDialog()
        self.button = QPushButton("Select Font")
        self.button.clicked.connect(self.show_font_dialog)

        self.color_dialog = QColorDialog()
        self.color_button = QPushButton("Select Color")
        self.color_button.clicked.connect(self.show_color_dialog)
        self.color_label = QLabel("Color:")

        self.addWidget(self.label)
        self.addWidget(self.button)
        self.addWidget(self.color_button)
        self.addWidget(self.color_label)
        self._font = default_font
        self._color = None
        self.color = default_color

    @property
    def font(self) -> str:
        return self._font

    @font.setter
    def font(self, value: QFont):
        if not isinstance(value, QFont):
            raise ValueError("Value must be a QFont")
        if value != self.font:
            self._font = value
            self.changedProperty.emit()

    @property
    def color(self) -> QColor:
        return self._color

    @color.setter
    def color(self, value: QColor):
        if not isinstance(value, QColor):
            raise ValueError("Value must be a QColor")
        if value != self.color:
            self._color = value
            self.color_label.setStyleSheet(f"background-color: {value.name()}")
            self.changedProperty.emit()

    def show_font_dialog(self):
        self.input.setCurrentFont(self.font)
        self.input.show()
        if self.input.exec():
            self.font = self.input.selectedFont()

    def show_color_dialog(self):
        self.color_dialog.setCurrentColor(self.color)
        self.color_dialog.show()
        if self.color_dialog.exec():
            self.color = self.color_dialog.selectedColor()


class LineOptionDelegate(QVBoxLayout):
    changedProperty = Signal()
    def __init__(self, label: str, color: QColor, width: float, line_style:PySide6.QtCore.Qt.PenStyle):
        super().__init__()
        self._color = None
        self._width = None
        self.color_label = QLabel("Color:")
        self.width = QDoubleSpinBox()
        self.line_color = color
        self.line_width = width
        self.label = QLabel(label)
        self.h_layout = QHBoxLayout()
        self.h_layout.addWidget(QLabel("Width:"))
        self.width.setMinimum(0.5)
        self.width.setMaximum(100)
        self.width.setDecimals(1)
        self.width.setSingleStep(0.5)
        self.width.valueChanged.connect(self.widthChanged)

        self.color_dialog = QColorDialog()
        self.color_button = QPushButton("Select Color")
        self.color_button.clicked.connect(self.show_color_dialog)
        self.h_layout.addWidget(self.color_button)
        self.h_layout.addWidget(self.width)
        self.h_layout.addWidget(self.color_label)

        self.linestyle_layout = QHBoxLayout()
        self.linestyle_label = QLabel("Line Style:")
        self.linestyle = QComboBox()
        self.linestyle.addItem("SolidLine", PySide6.QtCore.Qt.PenStyle.SolidLine)
        self.linestyle.addItem("DashLine", PySide6.QtCore.Qt.PenStyle.DashLine)
        self.linestyle.addItem("DotLine", PySide6.QtCore.Qt.PenStyle.DotLine)
        self.linestyle.addItem("DashDotLine", PySide6.QtCore.Qt.PenStyle.DashDotLine)
        self.linestyle.addItem("DashDotDotLine", PySide6.QtCore.Qt.PenStyle.DashDotDotLine)
        self.linestyle.setCurrentText(line_style.name)
        self.linestyle_layout.addWidget(self.linestyle_label)
        self.linestyle_layout.addWidget(self.linestyle)
        self.linestyle.currentIndexChanged.connect(self.emitPropertyChange)

        self.addWidget(self.label)
        self.addLayout(self.h_layout)
        self.addLayout(self.linestyle_layout)

    @Slot(float)
    def widthChanged(self, value):
        self.line_width = value

    @Slot(int)
    def emitPropertyChange(self, index):
        self.changedProperty.emit()
    @property
    def line_width(self) -> float:
        return self._width

    @line_width.setter
    def line_width(self, value: float):
        self.width.setValue(value)
        self._width = value
        self.changedProperty.emit()

    @property
    def line_color(self) -> QColor:
        return self._color

    @line_color.setter
    def line_color(self, value: QColor):
        if not isinstance(value, QColor):
            raise ValueError("Value must be a QColor")
        self._color = value
        self.color_label.setStyleSheet(f"background-color: {value.name()}")
        self.changedProperty.emit()

    def show_color_dialog(self):
        self.color_dialog.setCurrentColor(self.line_color)
        self.color_dialog.show()
        if self.color_dialog.exec():
            self.line_color = self.color_dialog.selectedColor()




class BrushOptionsDelegate(QHBoxLayout):
    changedProperty = Signal()

    def __init__(self, color: QColor, parent=None):
        super().__init__(parent)
        self._color = None
        self.color_label = QLabel("Color:")
        self.color_dialog = QColorDialog()
        self.color_button = QPushButton("Select Color")
        self.color_button.clicked.connect(self.show_color_dialog)
        self.addWidget(self.color_button)
        self.addWidget(self.color_label)
        self.color = color

    @property
    def color(self) -> QColor:
        return self._color

    @color.setter
    def color(self, value: QColor):
        if not isinstance(value, QColor):
            raise ValueError("Value must be a QColor")
        self._color = value
        self.color_label.setStyleSheet(f"background-color: {value.name()}")
        self.changedProperty.emit()

    def show_color_dialog(self):
        self.color_dialog.setCurrentColor(self.color)
        self.color_dialog.show()
        if self.color_dialog.exec():
            self.color = self.color_dialog.selectedColor()


class MainWindow(QMainWindow):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.zoom_factor = 1
        self.last_canvas_size = None
        self.loader = None
        self.figure = ganttmaker.Figure()
        self.image: QImage | None = None
        self.setWindowTitle('Gantt Editor')
        self.setGeometry(100, 100, 800, 600)
        self._build_ui()

    def _build_ui(self):
        # Create the status bar
        self.statusbar = self.statusBar()
        self.statusbar.showMessage('loading...')
        self.statusbar.setStyleSheet('color: red')

        # Create the central widget using a splitter
        self.statusbar.showMessage('load menu and canvas', 500)
        splitter = QSplitter()

        # Create the left side menu area (fixed size)
        scroll_container = QScrollArea()
        scroll_container.setVerticalScrollBarPolicy(PySide6.QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        left_menu = self._build_menu()
        #left_menu.setFixedWidth(400)
        scroll_container.setWidget(left_menu)

        # Create the right side canvas (resizable and scrollable)
        self.canvas_scroll_area = self._build_canvas_scroll_area()

        # Add both to the splitter
        splitter.addWidget(scroll_container)
        splitter.addWidget(self.canvas_scroll_area)

        # Set initial splitter sizes: 1/3 for menu, 2/3 for canvas
        splitter.setSizes([250, 550])

        # Set the splitter as the central widget
        self.setCentralWidget(splitter)
        self.statusbar.showMessage('ready', )
        self.statusbar.setStyleSheet('color: green')

    def _build_menu(self):
        def new_placeholder():
            placeholder = QLabel("")
            placeholder.setStyleSheet(f"background-color: {'darkgray'}")
            placeholder.setFixedHeight(2)
            return placeholder

        # Create a left-side widget for the menu
        self.left_menu = QFrame()
        self.left_menu.setFrameShape(QFrame.Shape.StyledPanel)

        # Create layout for the left menu
        self.layout = QVBoxLayout()

        self.layout.addWidget(new_placeholder())

        self.start_date_layout = QHBoxLayout()
        self.start_date = QLineEdit()
        self.start_date.setPlaceholderText("YYYY-MM-DD")
        self.start_date.setText("2024-08-01")
        self.start_date_layout.addWidget(QLabel("Start Date:"))
        self.start_date_layout.addWidget(self.start_date)
        self.layout.addLayout(self.start_date_layout)

        self.layout.addWidget(new_placeholder())
        self.canvas_size_layout = QHBoxLayout()
        self.canvas_width = QLineEdit()
        self.canvas_width.setPlaceholderText("Width")
        self.canvas_width.setText("2000")
        self.canvas_height = QLineEdit()
        self.canvas_height.setPlaceholderText("Height")
        self.canvas_height.setText("800")
        self.canvas_size_layout.addWidget(QLabel("Canvas Size:"))
        self.canvas_size_layout.addWidget(self.canvas_width)
        self.canvas_size_layout.addWidget(self.canvas_height)
        self.layout.addLayout(self.canvas_size_layout)

        self.layout.addWidget(new_placeholder())
        self.load_button = QPushButton("Load File")
        self.load_button.clicked.connect(self.load_file)

        self.file_layout = QHBoxLayout()
        self.file_layout.addWidget(QLabel("File:"))
        self.file_layout.addWidget(self.load_button)
        self.layout.addLayout(self.file_layout)
        self.file_label = QLabel("No file loaded")
        self.layout.addWidget(self.file_label)

        # Add legend options
        self.layout.addWidget(new_placeholder())
        self.layout.addWidget(QLabel("Legend Options:"))
        self.legend_width = FloatOptionDelegate("Legend Width:", self.figure.render_metrics.legend_width)
        self.legend_width.changedProperty.connect(self.rewrite_properties)
        self.layout.addLayout(self.legend_width)
        self.legend_font_layout = FontOptionDelegate("Font:", self.figure.legend_properties.font, self.figure.legend_properties.line_color)
        self.legend_font_layout.changedProperty.connect(self.rewrite_properties)
        self.layout.addLayout(self.legend_font_layout)

        # Add box options
        self.layout.addWidget(new_placeholder())
        self.layout.addWidget(QLabel("Box Options:"))
        self.box_line_layout = LineOptionDelegate("Box Line:", self.figure.box_properties.line_color, self.figure.box_properties.line_width, PySide6.QtCore.Qt.PenStyle.SolidLine)
        self.box_line_layout.changedProperty.connect(self.rewrite_properties)
        self.layout.addLayout(self.box_line_layout)
        self.box_brush_color = BrushOptionsDelegate(self.figure.box_properties.brush.color())
        self.box_brush_color.changedProperty.connect(self.rewrite_properties)
        self.layout.addLayout(self.box_brush_color)
        self.box_corner_layout = QHBoxLayout()
        self.box_corner_layout.addWidget(QLabel("Corner Radius:"))
        self.box_corner_radius = QDoubleSpinBox()
        self.box_corner_radius.setMinimum(0)
        self.box_corner_radius.setMaximum(10)
        self.box_corner_radius.setDecimals(1)
        self.box_corner_radius.setSingleStep(0.1)
        self.box_corner_radius.valueChanged.connect(self.rewrite_properties)
        self.box_corner_layout.addWidget(self.box_corner_radius)
        self.layout.addLayout(self.box_corner_layout)

        # Add grid options
        self.layout.addWidget(new_placeholder())
        self.layout.addWidget(QLabel("Grid Options:"))
        self.grid_line_layout = LineOptionDelegate("Grid Line:", self.figure.grid_properties.line_color, self.figure.grid_properties.line_width, PySide6.QtCore.Qt.PenStyle.DashLine)
        self.grid_line_layout.changedProperty.connect(self.rewrite_properties)
        self.layout.addLayout(self.grid_line_layout)
        self.grid_brush_color = BrushOptionsDelegate(self.figure.grid_properties.brush.color())
        self.grid_brush_color.changedProperty.connect(self.rewrite_properties)
        self.layout.addLayout(self.grid_brush_color)

        # Add title options
        self.layout.addWidget(new_placeholder())
        self.layout.addWidget(QLabel("Title Options:"))
        self.title_font_layout = FontOptionDelegate("Font:", self.figure.title_properties.font, self.figure.title_properties.line_color)
        self.title_font_layout.changedProperty.connect(self.rewrite_properties)
        self.layout.addLayout(self.title_font_layout)

        # Add task options
        self.layout.addWidget(new_placeholder())
        self.layout.addWidget(QLabel("Tasks Options:"))
        self.task_line_layout = LineOptionDelegate("Box Line:", self.figure.task_properties.line_color, self.figure.task_properties.line_width, PySide6.QtCore.Qt.PenStyle.SolidLine)
        self.task_line_layout.changedProperty.connect(self.rewrite_properties)
        self.layout.addLayout(self.task_line_layout)
        self.task_brush_color = BrushOptionsDelegate(self.figure.box_properties.brush.color())
        self.task_brush_color.changedProperty.connect(self.rewrite_properties)
        self.layout.addLayout(self.task_brush_color)
        self.taskcorner_layout = QHBoxLayout()
        self.taskcorner_layout.addWidget(QLabel("Corner Radius:"))
        self.taskcorner_radius = QDoubleSpinBox()
        self.taskcorner_radius.setMinimum(0)
        self.taskcorner_radius.setMaximum(10)
        self.taskcorner_radius.setDecimals(1)
        self.taskcorner_radius.setSingleStep(0.1)
        self.taskcorner_radius.valueChanged.connect(self.rewrite_properties)
        self.taskcorner_layout.addWidget(self.taskcorner_radius)
        self.layout.addLayout(self.taskcorner_layout)

        # Add arrow options
        self.layout.addWidget(new_placeholder())
        self.layout.addWidget(QLabel("Arrow Options:"))
        self.arrow_line_layout = LineOptionDelegate("Line:", self.figure.arrow_properties.line_color, self.figure.arrow_properties.line_width, PySide6.QtCore.Qt.PenStyle.SolidLine)
        self.arrow_line_layout.changedProperty.connect(self.rewrite_properties)
        self.layout.addLayout(self.arrow_line_layout)
        self.arrow_brush_color = BrushOptionsDelegate(self.figure.arrow_properties.brush.color())
        self.arrow_brush_color.changedProperty.connect(self.rewrite_properties)
        self.layout.addLayout(self.arrow_brush_color)

        # Add axes options
        self.layout.addWidget(new_placeholder())
        self.layout.addWidget(QLabel("Axes Options:"))
        self.axis_line_layout = LineOptionDelegate("Line:", self.figure.axes_properties.line_color, self.figure.axes_properties.line_width, PySide6.QtCore.Qt.PenStyle.SolidLine)
        self.axis_line_layout.changedProperty.connect(self.rewrite_properties)
        self.layout.addLayout(self.axis_line_layout)
        self.axis_brush_color = BrushOptionsDelegate(self.figure.axes_properties.brush.color())
        self.axis_brush_color.changedProperty.connect(self.rewrite_properties)
        self.layout.addLayout(self.axis_brush_color)
        self.axis_font_layout = FontOptionDelegate("Font:", self.figure.axes_properties.font, self.figure.axes_properties.line_color)
        self.axis_font_layout.changedProperty.connect(self.rewrite_properties)
        self.layout.addLayout(self.axis_font_layout)

        # Add week highlight options
        self.layout.addWidget(new_placeholder())
        self.layout.addWidget(QLabel("Week Highlight Options:"))
        self.week_line_layout = LineOptionDelegate("Line:", self.figure.week_highlight_properties.line_color, self.figure.week_highlight_properties.line_width, PySide6.QtCore.Qt.PenStyle.SolidLine)
        self.week_line_layout.changedProperty.connect(self.rewrite_properties)
        self.layout.addLayout(self.week_line_layout)
        self.week_brush_color = BrushOptionsDelegate(self.figure.week_highlight_properties.brush.color())
        self.week_brush_color.changedProperty.connect(self.rewrite_properties)
        self.layout.addLayout(self.week_brush_color)

        # Add month highlight options
        self.layout.addWidget(new_placeholder())
        self.layout.addWidget(QLabel("Month Highlight Options:"))
        self.month_line_layout = LineOptionDelegate("Line:", self.figure.month_highlight_properties.line_color, self.figure.month_highlight_properties.line_width, PySide6.QtCore.Qt.PenStyle.SolidLine)
        self.month_line_layout.changedProperty.connect(self.rewrite_properties)
        self.layout.addLayout(self.month_line_layout)
        self.month_brush_color = BrushOptionsDelegate(self.figure.month_highlight_properties.brush.color())
        self.month_brush_color.changedProperty.connect(self.rewrite_properties)
        self.layout.addLayout(self.month_brush_color)

        # Add misc options
        self.layout.addWidget(new_placeholder())
        self.layout.addWidget(QLabel("Background Options:"))
        self.background_brush_color = BrushOptionsDelegate(self.figure.background_color)
        self.background_brush_color.changedProperty.connect(self.rewrite_properties)
        self.layout.addLayout(self.background_brush_color)

        # Add export options
        self.layout.addWidget(new_placeholder())
        self.layout.addWidget(QLabel("Export Options:"))
        self.export_layout = QHBoxLayout()
        self.export_layout.addWidget(QLabel("Export File:"))
        self.export_file = QLineEdit()
        self.export_file.setPlaceholderText("File path and name")
        self.export_file.editingFinished.connect(self.rewrite_properties)
        self.export_layout.addWidget(self.export_file)
        self.layout.addLayout(self.export_layout)

        self.left_menu.setLayout(self.layout)
        return self.left_menu

    def _build_canvas_scroll_area(self):
        # Create a QScrollArea that will hold the QLabel (canvas)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)  # Allow scroll area to resize with the window

        # Create the right-side canvas area (a QLabel inside the QScrollArea)
        self.canvas = QLabel()
        self.canvas.setFrameShape(QFrame.Shape.StyledPanel)
        self.canvas.setStyleSheet("background-color: white;")  # Example: white background for the canvas
        self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Set the QLabel as the widget inside the scroll area
        self.scroll_area.setWidget(self.canvas)

        return self.scroll_area

    @Slot()
    def load_file(self):
        if self.image is not None:
            window = QMessageBox()
            window.setText("Just reload the image or reload the file?")
            window.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            window.setDefaultButton(QMessageBox.StandardButton.Yes)
            window.show()
            if window.exec() == QMessageBox.StandardButton.Yes:
                self.canvas.clear()
                self.image = None
                self.image = self.figure.draw(self.loader)
                self.update_canvas_image()
                return
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter('Spreadsheet files (*.xlsx *.xls *.ods)')
        file_dialog.show()
        if file_dialog.exec():
            file_path = file_dialog.selectedFiles()[0]
            if not os.path.isfile(file_path):
                self.statusbar.showMessage('File not found', 2000)
                return
            try:
                self.figure.start_date = datetime.datetime.fromisoformat(self.start_date.text()).date()
                assert self.canvas_width.text().isdigit() and self.canvas_height.text().isdigit()
                assert int(self.canvas_width.text()) > 0 and int(self.canvas_height.text()) > 0
                self.figure.canvas_size = (int(self.canvas_width.text()), int(self.canvas_height.text()))
                self.loader = ganttmaker.Dataloader(file_path)
                self.loader.load()
                self.image = self.figure.draw(self.loader)
                self.update_canvas_image()
            except Exception as e:
                self.statusbar.showMessage(f'Error loading file: {e}', 2000)
                self.statusbar.setStyleSheet('color: red')
                return
            self.statusbar.showMessage(f'Loaded: {os.path.basename(file_path)}')
            self.statusbar.setStyleSheet('color: green')
            self.file_label.setText(file_path)
            self.statusbar.showMessage('File loaded', 2000)

    def update_canvas_image(self):
        if self.image:
            self.canvas.clear()
            scaled_pixmap = self.image.scaled(
                self.image.width() * self.zoom_factor,
                self.image.height() * self.zoom_factor,
                PySide6.QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                PySide6.QtCore.Qt.TransformationMode.SmoothTransformation
            )
            self.canvas.setPixmap(scaled_pixmap)
            self.canvas.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
            self.canvas.setScaledContents(True)

    @Slot()
    def rewrite_properties(self):
        print("Rewriting properties")
        self.image = None
        self.figure = ganttmaker.Figure()
        self.figure.start_date = datetime.datetime.fromisoformat(self.start_date.text()).date()
        canvas_size = (int(self.canvas_width.text()), int(self.canvas_height.text()))
        self.figure.canvas_size = canvas_size
        self.figure.render_metrics.legend_width = self.legend_width.value

        self.figure.legend_properties.font = self.legend_font_layout.font
        self.figure.legend_properties.line_color = self.legend_font_layout.color

        self.figure.box_properties.line_color = self.box_line_layout.line_color
        self.figure.box_properties.line_width = self.box_line_layout.line_width
        self.figure.box_properties.brush = QBrush(self.box_brush_color.color)
        self.figure.box_properties.corner_radius = self.box_corner_radius.value()

        self.figure.grid_properties.line_color = self.grid_line_layout.line_color
        self.figure.grid_properties.line_width = self.grid_line_layout.line_width
        self.figure.grid_properties.brush = QBrush(self.grid_brush_color.color)
        self.figure.grid_properties.line_style = self.grid_line_layout.linestyle.currentData(PySide6.QtCore.Qt.ItemDataRole.UserRole)

        self.figure.title_properties.font = self.title_font_layout.font
        self.figure.title_properties.line_color = self.title_font_layout.color

        self.figure.task_properties.line_color = self.task_line_layout.line_color
        self.figure.task_properties.line_width = self.task_line_layout.line_width
        self.figure.task_properties.line_style = self.task_line_layout.linestyle.currentData(PySide6.QtCore.Qt.ItemDataRole.UserRole)
        self.figure.task_properties.brush = QBrush(self.task_brush_color.color)
        self.figure.task_properties.corner_radius = self.taskcorner_radius.value()

        self.figure.arrow_properties.line_color = self.arrow_line_layout.line_color
        self.figure.arrow_properties.line_width = self.arrow_line_layout.line_width
        self.figure.arrow_properties.line_style = self.arrow_line_layout.linestyle.currentData(PySide6.QtCore.Qt.ItemDataRole.UserRole)
        self.figure.arrow_properties.brush = QBrush(self.arrow_brush_color.color)

        self.figure.axes_properties.line_color = self.axis_line_layout.line_color
        self.figure.axes_properties.line_width = self.axis_line_layout.line_width
        self.figure.axes_properties.line_style = self.axis_line_layout.linestyle.currentData(PySide6.QtCore.Qt.ItemDataRole.UserRole)
        self.figure.axes_properties.brush = QBrush(self.axis_brush_color.color)
        self.figure.axes_properties.font = self.axis_font_layout.font

        self.figure.week_highlight_properties.line_color = self.week_line_layout.line_color
        self.figure.week_highlight_properties.line_width = self.week_line_layout.line_width
        self.figure.week_highlight_properties.line_style = self.week_line_layout.linestyle.currentData(PySide6.QtCore.Qt.ItemDataRole.UserRole)
        self.figure.week_highlight_properties.brush = QBrush(self.week_brush_color.color)

        self.figure.month_highlight_properties.line_color = self.month_line_layout.line_color
        self.figure.month_highlight_properties.line_width = self.month_line_layout.line_width
        self.figure.month_highlight_properties.line_style = self.month_line_layout.linestyle.currentData(PySide6.QtCore.Qt.ItemDataRole.UserRole)
        self.figure.month_highlight_properties.brush = QBrush(self.month_brush_color.color)

        # Add misc options
        self.figure.background_color = self.background_brush_color.color
        if self.export_file.text() != "":
            self.figure.export_file = self.export_file.text()
        if self.loader is not None:
            self.loader.file_path = self.file_label.text()
            self.redraw()

    @Slot()
    def redraw(self):
        print("Redrawing")
        self.image = None
        self.image = self.figure.draw(self.loader)
        self.update_canvas_image()

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            self.zoom_factor += 0.05  # zoom in
        else:
            self.zoom_factor -= 0.05 if self.zoom_factor > 0.5 else 0  # zoom out
        self.update_canvas_image()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_canvas_image()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
