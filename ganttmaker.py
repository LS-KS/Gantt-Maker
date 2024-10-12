import datetime
import sys
import pandas as pd
import os
from PySide6.QtGui import QImage, QPainter, QPen, QFont, QGuiApplication, QColor, QBrush, QPainterPath
from PySide6.QtCore import Qt

_units = {
    'pt': 1,  # 1 point is 1 point
    'px': 1 / 0.75,  # 1 pixel ≈ 0.75 points (at 96 DPI)
    'mm': 1 / 0.352778,  # 1 point = 0.352778 mm
    'cm': 1 / 0.0352778,  # 1 point = 0.0352778 cm
    'in': 72  # 1 inch = 72 points
}

# color palette: https://www.learnui.design/tools/data-color-picker.html#palette
_colors = ["#003f5c", "#2f4b7c", "#665191", "#a05195", "#d45087", "#f95d6a", "#ff7c43", "#ffa600"]


class RenderMetrics:
    title_height: int = 50
    title_padding: int = 10
    vertical_padding: int = 10
    horizontal_padding: int = 5
    axis_width: int = 20
    axis_height: int = 20
    axis_padding: int = 10
    min_task_height: int = 20
    max_task_description_width: int = 200
    legend_width: int = 5


def validate_columns(data: pd.DataFrame):
    """
    Method that validates the columns of the Excel file.

    Parameters:
        data: pandas.DataFrame object
    """
    if 'Task' not in data.columns:
        raise ValueError("Column 'Task' missing")
    if 'Plan-End' not in data.columns:
        raise ValueError("Column 'Plan-End' missing")
    if 'Actual-End' not in data.columns:
        raise ValueError("Column 'Actual-End' missing")
    if 'Predecessor' not in data.columns:
        raise ValueError("Column 'Predecessor' missing")


class Dataloader:
    _file: str | None = None

    @property
    def file(self):
        """
        File property holds the path to the Excel file.

        Returns:
            str: path to the Excel file
        """
        return self._file

    @file.setter
    def file(self, file_string):
        if os.path.exists(file_string):
            self._file = file_string
        else:
            raise FileNotFoundError(f"File {file_string} not found")

    def __init__(self, file_string: str):
        """
        Class that handles the loading of data from an Excel file and holds the data in a pandas.DataFrame object.

        Parameters:
             file_string: path to a file
        """
        self.file = file_string
        self._data = None

    def load(self):
        """
        Method that loads the data from the Excel file into a pandas.DataFrame object.
        """
        data = pd.read_excel(self.file, engine='openpyxl', dtype={'Task': str, 'Predecessor': str})
        validate_columns(data)
        data['Plan-Start'] = pd.to_datetime(data['Plan-Start'], format='%d.%m.%Y')
        data['Actual-Start'] = pd.to_datetime(data['Actual-Start'], format='%d.%m.%Y')
        data['Plan-End'] = pd.to_datetime(data['Plan-End'], format='%d.%m.%Y')
        data['Actual-End'] = pd.to_datetime(data['Actual-End'], format='%d.%m.%Y')
        #data['Task'] = data['Task']
        #data['Predecessor'] = data['Predecessor']
        self._data = data

    @property
    def data(self):
        return self._data


class Figure:
    def __init__(self):
        """
        Core class of the Ganntmaker module.
        The Figure class holds all properties and methods to draw a Gantt chart.

        Properties:
            time_highlightline_width: tuple[float, float] - width of the time highlight lines.
            First element is for beginning of the week, second for beginning of the month.

            time_highlightline_color: QColor - color of the time highlight lines

            background_color: QColor - color of the background

            axes_color: QColor - color of the axes

            task_line_width: float - width of the task outlines

            task_brush_saturation: float - saturation of the task brush

            box_width: int - width of the graph box

            box_color: QColor - color of the graph box

            export_file: str - path to the export file

            start_date: datetime.date - start date of the project

            canvas_size: tuple[int, int] - size of the canvas

            unit: float - unit of the canvas size

            loader: Dataloader - Dataloader object

            render_metrics: RenderMetrics - RenderMetrics object

            title: str - title of the Gantt chart

            title_font: QFont - font of the title

            axes_font: QFont - font of the axes

            title_font: QFont - font of the title

            legend_font: QFont - font of the legend

            legend_color: QColor - color of the legend
        """
        self._arrow_pen_width: float = 2.0
        self._title_pen_width: float = 2.0
        self._legend_pen_width = 2.0
        self._axes_pen_width: float = 1.0
        self._grid_pen_width: float = 0.5
        self._title_color: QColor = QColor('black')
        self._time_highlightline_width: tuple[float, float] = (0.75, 2.5)
        self._time_highlightline_color: QColor = QColor('red')
        self._background_color: QColor = QColor('transparent')
        self._axes_color: QColor = QColor('black')
        self._task_line_width: float = 4.0
        self._task_brush_saturation: int = 127
        self._box_width: int = 2
        self._box_color: QColor = QColor('black')
        self._export_file: str | None = None
        self._start_date: datetime.date | None = None
        self._canvas_size: tuple[int, int] | None = None
        self._unit: float = _units['px']
        self._loader: 'Dataloader' | None = None
        self.render_metrics: RenderMetrics = RenderMetrics()
        self.title: str = "Gantt Chart"
        self._axes_font = QFont("Arial", 10)
        self._title_font = QFont("Arial", 24)
        self._legend_font = QFont("Arial", 12)
        self._legend_color = QColor('black')

    @property
    def title_pen_width(self) -> float:
        """
        Property that holds the width of the title lines.

        Returns:
            float: width of the title lines
        """
        return self._title_pen_width

    @title_pen_width.setter
    def title_pen_width(self, width: float):
        if not isinstance(width, float):
            raise TypeError("title_pen_width must be a float")
        elif width < 0:
            raise ValueError("title_pen_width must be a positive float")
        self._title_pen_width = width

    @property
    def arrow_pen_width(self) -> float:
        """
        Property that holds the width of the arrow lines.

        Returns:
            float: width of the arrow lines
        """
        return self._arrow_pen_width

    @arrow_pen_width.setter
    def arrow_pen_width(self, width: float):
        if not isinstance(width, float):
            raise TypeError("arrow_pen_width must be a float")
        elif width < 0:
            raise ValueError("arrow_pen_width must be a positive float")
        self._arrow_pen_width = width
    @property
    def legend_pen_width(self) -> float:
        """
        Property that holds the width of the legend lines.

        Returns:
            float: width of the legend lines
        """
        return self._legend_pen_width

    @legend_pen_width.setter
    def legend_pen_width(self, width: float):
        if not isinstance(width, float):
            raise TypeError("legend_pen_width must be a float")
        elif width < 0:
            raise ValueError("legend_pen_width must be a positive float")
        self._legend_pen_width = width

    @property
    def axes_pen_width(self) -> float:
        """
        Property that holds the width of the axes lines.

        Returns:
            float: width of the axes lines
        """
        return self._axes_pen_width

    @axes_pen_width.setter
    def axes_pen_width(self, width: float):
        if not isinstance(width, float):
            raise TypeError("axes_pen_width must be a float")
        elif width < 0:
            raise ValueError("axes_pen_width must be a positive float")
        self._axes_pen_width = width

    @property
    def grid_pen_width(self) -> float:
        """
        Property that holds the width of the grid lines.

        Returns:
            float: width of the grid lines
        """
        return self._grid_pen_width

    @grid_pen_width.setter
    def grid_pen_width(self, width: float):
        if not isinstance(width, float):
            raise TypeError("grid_pen_width must be a float")
        elif width < 0:
            raise ValueError("grid_pen_width must be a positive float")
        self._grid_pen_width = width

    @property
    def time_highlightline_width(self) -> tuple[float, float]:
        """
        Property that holds the width of the time highlight lines.
        First element is the line width to highlight the beginning of the week, second for beginning of the month.
        """
        return self._time_highlightline_width

    @time_highlightline_width.setter
    def time_highlightline_width(self, width: tuple[int, int]):
        if not isinstance(width, tuple):
            raise TypeError("time_highlightline_width must be a tuplpe of floats")
        elif len(width) != 2:
            raise ValueError("time_highlightline_width must be a tuple of two floats")
        self._time_highlightline_width = width

    @property
    def time_highlightline_color(self) -> QColor:
        """
        Property that holds the color of the time highlight lines.
        """
        return self._time_highlightline_color

    @time_highlightline_color.setter
    def time_highlightline_color(self, color: QColor):
        if not isinstance(color, QColor):
            raise TypeError("time_highlightline_color must be a QColor object")
        self._time_highlightline_color = color

    @property
    def background_color(self) -> QColor:
        """
        Property that holds the color of the background.

        Returns:
            QColor: background color
        """
        return self._background_color

    @background_color.setter
    def background_color(self, color: QColor):
        if not isinstance(color, QColor):
            raise TypeError("background_color must be a QColor object")
        self._background_color = color

    @property
    def axes_color(self) -> QColor:
        """
        Property that holds the color of the ax annotations.

        Returns:
            QColor: axes color
        """
        return self._axes_color

    @axes_color.setter
    def axes_color(self, color: QColor):
        if not isinstance(color, QColor):
            raise TypeError("axes_color must be a QColor object")
        self._axes_color = color

    @property
    def axes_font(self) -> QFont:
        """
        Property that holds the font of the ax annotations.

        Returns:
            QFont: axes font
        """
        return self._axes_font

    @axes_font.setter
    def axes_font(self, font: QFont):
        if not isinstance(font, QFont):
            raise TypeError("axes_font must be a QFont object")
        self._axes_font = font

    @property
    def task_brush_saturation(self) -> int:
        """
        Property that holds the saturation of the task brush.

        Returns:
            float: task brush saturation
        """
        return self._task_brush_saturation

    @task_brush_saturation.setter
    def task_brush_saturation(self, saturation: int):
        if not isinstance(saturation, int):
            raise TypeError("task_brush_saturation must be an integer")
        elif saturation < 0 or saturation > 255:
            raise ValueError("task_brush_saturation must be between 0 and 255")
        self._task_brush_saturation = saturation

    @property
    def task_line_width(self) -> float:
        """
        Property that holds the width of the task lines.

        Returns:
            int: task line width
        """
        return self._task_line_width

    @task_line_width.setter
    def task_line_width(self, width: int):
        if not isinstance(width, int):
            raise TypeError("task_line_width must be an integer")
        self._task_line_width = width

    @property
    def box_width(self):
        """
        Property that holds the width of the graph box.

        Returns:
            int: box width
        """
        return self._box_width

    @box_width.setter
    def box_width(self, width: int):
        if not isinstance(width, int):
            raise TypeError("box_width must be an integer")
        self._box_width = width

    @property
    def box_color(self) -> QColor:
        """
        Property that holds the color of the graph box.

        Returns:
            QColor: box color
        """
        return self._box_color

    @box_color.setter
    def box_color(self, color: QColor):
        if not isinstance(color, QColor):
            raise TypeError("box_color must be a QColor object")
        self._box_color = color

    @property
    def legend_color(self) -> QColor:
        """
        Property that holds the color of the legend.

        Returns:
            QColor: legend color
        """
        return self._legend_color

    @legend_color.setter
    def legend_color(self, color: QColor):
        if not isinstance(color, QColor):
            raise TypeError("legend_color must be a QColor object")
        self._legend_color = color

    @property
    def legend_font(self) -> QFont:
        """
        Property that holds the font of the legend.

        Returns:
            QFont: legend font
        """
        return self._legend_font

    @legend_font.setter
    def legend_font(self, font: QFont):
        if not isinstance(font, QFont):
            raise TypeError("legend_font must be a QFont object")
        self._legend_font = font

    @property
    def title_font(self) -> QFont:
        """
        Property that holds the font of the title.

        Returns:
            QFont: title font
        """
        return self._title_font

    @title_font.setter
    def title_font(self, font: QFont):
        if not isinstance(font, QFont):
            raise TypeError("title_font must be a QFont object")
        self._title_font = font

    @property
    def title_color(self) -> QColor:
        """
        Property that holds the color of the title.

        Returns:
            QColor: title color
        """
        return self._title_color

    @title_color.setter
    def title_color(self, color: QColor):
        if not isinstance(color, QColor):
            raise TypeError("title_color must be a QColor object")
        self._title_color = color

    @property
    def start_date(self) -> datetime.date:
        """
        Property that holds the start date of the project.
        Must be set or the diagram will mess up.

        Returns:
            datetime.date: start date of the project
        """
        return self._start_date

    @start_date.setter
    def start_date(self, date: datetime.date):
        if isinstance(date, pd.Timestamp):
            self._start_date = date.date()
            return
        if isinstance(date, datetime.date):
            self._start_date = date
        else:
            raise TypeError("start_date must be a pandas.Timestamp object")

    @property
    def unit(self) -> float:
        """
        Property that holds the unit of the canvas size.

        Returns:
            float: unit of the canvas resulted from enum _units
        """
        return self._unit

    @unit.setter
    def unit(self, unit: str):
        """
        Setter for the unit property.

        Parameters:
            unit: string that defines the unit of the canvas size
        """
        if unit not in _units:
            raise ValueError(f"Unknown unit {unit}, choose one of {_units.keys()}")
        self._unit = _units[unit]

    @property
    def canvas_size(self) -> tuple[int, int]:
        """
        Property that holds the size of the canvas.

        Returns:
            tuple[int, int]: size of the canvas
        """
        return self._canvas_size

    @canvas_size.setter
    def canvas_size(self, size: tuple[int, int]):
        if len(size) == 2:
            self._canvas_size = tuple([int(x * self.unit) for x in size])
        else:
            raise ValueError("canvas_size must be a tuple of two integers")

    @property
    def export_file(self):
        """
        Property that holds the path to the export file.

        Returns:
            str: path to the export file
        """
        return self._export_file

    @export_file.setter
    def export_file(self, file: str):
        self._export_file = file

    @staticmethod
    def set_painter_renderoptions(painter):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

    def draw(self, loader: Dataloader):
        """
        Main method to draw the Gantt chart.
        The process of drawing is seperated in multiple submethods.
        The image is built by layering multiple QImage objects.

        Parameters:
            loader: Dataloader object that contains the data to be drawn

        Returns:
            None
        """
        # guard checks
        if self.start_date is None:
            raise ValueError("start_date not set")
        if self.canvas_size is None:
            raise ValueError("canvas_size not set")
        if not isinstance(loader, Dataloader):
            raise TypeError("data must be a pandas.DataFrame object")
        self._loader = loader
        if self._loader._data is None:
            self._loader.load()

        # get or construct QApplication instance
        if not QGuiApplication.instance():
            app = QGuiApplication(sys.argv)
        else:
            app = QGuiApplication(sys.argv)

        figure_start: tuple[int, int] = self._define_drawing_start()
        figure_width = self.canvas_size[0] - figure_start[0] - self.render_metrics.horizontal_padding
        figure_height = (self.canvas_size[1]
                         - figure_start[1]
                         - self.render_metrics.vertical_padding
                         - self.render_metrics.axis_height
                         - self.render_metrics.vertical_padding)
        task_height: int = self._define_task_height(figure_height)
        task_width: int = self._define_task_width(figure_width)

        image = QImage(self.canvas_size[0], self.canvas_size[1], QImage.Format.Format_ARGB32)
        image.fill(self.background_color)

        # painter initialization
        painter = QPainter()

        # pen initialization
        box_pen = QPen(self._box_color, self.box_width, Qt.PenStyle.SolidLine)
        grid_pen = QPen(Qt.GlobalColor.gray, self.grid_pen_width, Qt.PenStyle.DotLine)
        axes_pen = QPen(self.axes_color, self.axes_pen_width, Qt.PenStyle.SolidLine)
        legend_pen = QPen(self.legend_color, self.legend_pen_width, Qt.PenStyle.SolidLine)
        graph_pen = QPen(Qt.GlobalColor.blue, self.task_line_width, Qt.PenStyle.SolidLine)
        title_pen = QPen(self.title_color, self.title_pen_width, Qt.PenStyle.SolidLine)
        arrow_pen = QPen(Qt.GlobalColor.black, self.arrow_pen_width, Qt.PenStyle.SolidLine)

        # draw image layers
        box_layer = self.draw_box_layer(box_pen, figure_start, figure_width, figure_height, painter)
        box_layer = self.draw_title(box_layer, painter, title_pen, self.title)
        box_layer = self.draw_legend(box_layer, painter, legend_pen, figure_start, task_height, self.legend_font)
        grid_layer = self.draw_grid_layer(figure_start, grid_pen, painter, task_width, task_height, figure_width, 'Plan-End')
        grid_layer = self.draw_monday_lines(grid_layer, figure_start, painter, task_width, 'Plan-End')
        graph_layer = self.draw_tasks(figure_start, graph_pen, self.task_brush_saturation, painter, task_height,
                                      task_width, 'Plan-Start', 'Plan-End')
        actual_layer = self.draw_tasks(figure_start, graph_pen, self.task_brush_saturation, painter, task_height,
                                       task_width, 'Actual-Start', 'Actual-End', plan=False)
        axes_layer = self.draw_xaxis(figure_start, figure_height, task_width, painter, axes_pen, self.axes_font, 'Plan-End')

        arrows_layer = self.draw_arrows(figure_start, task_width, task_height, painter, arrow_pen)

        # combine all layers
        painter.begin(image)
        painter.drawImage(0, 0, box_layer)
        painter.drawImage(0, 0, grid_layer)
        painter.drawImage(0, 0, axes_layer)
        painter.drawImage(0, 0, graph_layer)
        painter.drawImage(0, 0, actual_layer)
        painter.drawImage(0, 0, arrows_layer)
        painter.end()

        # save image
        image.save(self.export_file)

    def draw_arrows(self, start, t_width, t_height, painter, pen):
        """
        Method that draws arrows at the end of each task.

        Parameters:
            start: tuple[int, int], starting point of the figure
            t_width: int, width of a task
            t_height: int, height of a task
            painter: QPainter object (painting device)
            pen: QPen object, pen for the arrows
        """

        arrowslayer = QImage(self.canvas_size[0], self.canvas_size[1], QImage.Format.Format_ARGB32)
        painter.begin(arrowslayer)
        for i, task in enumerate(self._loader._data.itertuples()):
            predecessors: list = str(self._loader.data['Predecessor'].loc[i]).split(';')
            if predecessors[0] != 'nan':
                # print(predecessors)
                for j, pred in enumerate(predecessors):
                    record = self._loader._data[self._loader._data['Task'] == pred]
                    start_date = record['Actual-End'].iloc[0].date()
                    end_date = self._loader._data['Actual-Start'][i].date()
                    x_start = ((start_date - self.start_date).days + 1) * t_width + start[0] + self.render_metrics.horizontal_padding - t_width/2
                    pred_idx = self._loader.data.index[self._loader.data['Task'] == pred].tolist()[0]
                    y_start = start[1] + self.render_metrics.vertical_padding + pred_idx*t_height + t_height/2
                    if start_date == end_date:
                        x_end = (end_date - self.start_date).days * t_width + start[0] + self.render_metrics.horizontal_padding + t_width/2
                    else:
                        x_end = (end_date - self.start_date).days * t_width + start[0] + self.render_metrics.horizontal_padding
                    if len(predecessors) > 1:
                        y_end = start[1] + self.render_metrics.vertical_padding + i*t_height + j * (t_height / len(predecessors)) + (t_height / len(predecessors))/2
                    else:
                        y_end = start[1] + self.render_metrics.vertical_padding + i*t_height + t_height/2
                    circle = 0.1 * t_height
                    pen.setColor(QColor(_colors[pred_idx % len(_colors)]))
                    brush = QBrush(pen.color())
                    painter.setBrush(brush)
                    painter.setPen(pen)

                    # define arrow head
                    arrow_head = QPainterPath()
                    if start_date == end_date:
                        arrow_head.moveTo(x_end - circle / 2, y_end - circle*2)
                        arrow_head.lineTo(x_end + circle / 2, y_end - circle*2)
                        arrow_head.lineTo(x_end, y_end)
                        arrow_head.closeSubpath()
                    else:
                        arrow_head.moveTo(x_end - circle * 2, y_end - circle / 2)
                        arrow_head.lineTo(x_end - circle * 2, y_end + circle / 2)
                        arrow_head.lineTo(x_end, y_end)
                        arrow_head.closeSubpath()

                    # starting dot
                    painter.drawEllipse(x_start - circle/2, y_start - circle/2, circle, circle)

                    # connection lines
                    painter.drawLine(x_start, y_start, x_start, y_end)
                    painter.drawLine(x_start, y_end, x_end, y_end)

                    # arrow head
                    painter.drawPath(arrow_head)


        painter.end()
        return arrowslayer

    def draw_monday_lines(self, layer, figure_start, painter, task_width, column):
        """
        Method that draws vertical lines at the beginning of each week and month.

        Parameters:
            layer: QImage object where the lines are drawn
            figure_start: tuple[int, int], starting point of the figure
            painter: QPainter object (painting device)
            task_width: int that defines the width of a task
            column: str, column of the data to be drawn
        """
        monday_pen = QPen(self.time_highlightline_color, self.time_highlightline_width[0], Qt.PenStyle.SolidLine)
        monthly_pen = QPen(self.time_highlightline_color, self.time_highlightline_width[1], Qt.PenStyle.SolidLine)
        painter.begin(layer)
        dates = (self._loader.data[column].max().date() - self.start_date).days + 1
        for i in range(dates):
            x = int(figure_start[0] + i * task_width + self.render_metrics.horizontal_padding)
            if (self.start_date + datetime.timedelta(days=i)).weekday() == 0:
                painter.setPen(monday_pen)
                painter.drawLine(x, figure_start[1], x, self.canvas_size[1] - self.render_metrics.vertical_padding)
            if (self.start_date + datetime.timedelta(days=i)).day == 1:
                painter.setPen(monthly_pen)
                painter.drawLine(x, figure_start[1] - self.render_metrics.axis_height, x,
                                 self.canvas_size[1] - self.render_metrics.vertical_padding)
        painter.end()
        return layer

    def draw_xaxis(self, start, height, task_width, painter, pen, font, column):
        """
        Method that draws the x-axis of the Gantt chart.

        Parameters:
            start: tuple[int, int], starting point of the figure
            height: int, height of the figure
            task_width: int, width of a task
            painter: QPainter object (painting device)
            pen: QPen object, pen for the axes
            font: QFont object, font for the axes
            column: str, column of the data to be drawn
        """
        axes_layer = QImage(self.canvas_size[0], self.canvas_size[1], QImage.Format.Format_ARGB32)
        painter.begin(axes_layer)
        painter.setPen(pen)
        painter.setFont(font)
        dates = (self._loader._data[column].max().date() - self.start_date).days + 1
        for i in range(dates):
            x = int(start[0]
                    + i * task_width
                    + self.render_metrics.horizontal_padding
                    )
            y = start[1] + height + self.render_metrics.vertical_padding
            date = self.start_date + datetime.timedelta(days=i)
            text = date.strftime('%A')[0:2]
            day_text = date.strftime('%d')
            painter.drawText(
                x, y,
                task_width, self.render_metrics.axis_height,
                Qt.AlignmentFlag.AlignCenter,
                text
            )
            painter.drawText(
                x, y - self.render_metrics.axis_height - self.render_metrics.axis_padding,
                task_width, self.render_metrics.axis_height + self.render_metrics.axis_padding,
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                day_text
            )
            if date.day == 1:
                painter.drawText(
                    x + self.render_metrics.horizontal_padding,
                    (start[1]
                     - self.render_metrics.axis_height
                     - self.render_metrics.axis_padding
                     - self.render_metrics.title_padding),
                    task_width * 30,
                    (self.render_metrics.axis_height
                     + self.render_metrics.axis_padding
                     + self.render_metrics.title_padding),
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom,
                    date.strftime('%B %Y'))
        painter.drawText(
            self.render_metrics.horizontal_padding,
            self.canvas_size[1] - self.render_metrics.vertical_padding - self.render_metrics.axis_height,
            self.canvas_size[0] - self.render_metrics.horizontal_padding * 2,
            self.render_metrics.axis_height + self.render_metrics.vertical_padding,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom,
            'created: ' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        painter.end()

        return axes_layer

    def draw_tasks(self, figure_start: tuple[int, int], task_pen: QPen, brush_saturation: int, painter: QPainter,
                   task_height: int, task_width: int, start_column, end_column, plan=True):
        """
        Method that draws the tasks of the Gantt chart.

        Parameters:
            figure_start: tuple[int, int], starting point of the figure
            task_pen: QPen object, pen for the tasks
            brush_saturation: int, saturation of the task brush
            painter: QPainter object (painting device)
            task_height: int, height of a task
            task_width: int, width of a task
        """
        graph_layer = QImage(self.canvas_size[0], self.canvas_size[1], QImage.Format.Format_ARGB32)
        painter.begin(graph_layer)
        self.set_painter_renderoptions(painter)

        painter.setPen(task_pen)
        for i, task in enumerate(self._loader._data.itertuples()):
            painter.setPen(QColor(_colors[i % len(_colors)]))
            brush_color = QColor(_colors[i % len(_colors)])
            if plan:
                brush_color.setAlpha(0)
                pen = painter.pen()
                painter.setPen(pen)
            else:
                brush_color.setAlpha(brush_saturation)
            task_brush = QBrush(brush_color)
            painter.setBrush(task_brush)
            plan_start = self._loader._data[start_column][i].date()
            plan_end = self._loader._data[end_column][i].date()
            x_start = figure_start[0] + task_width * (
                    plan_start - self.start_date).days + self.render_metrics.horizontal_padding
            x_end = figure_start[0] + task_width * (
                    plan_end - self.start_date).days + self.render_metrics.horizontal_padding
            width = x_end - x_start + task_width
            y = figure_start[1] + self.render_metrics.vertical_padding + i * task_height
            painter.drawRect(x_start, y, width, task_height)
        painter.end()
        return graph_layer

    def draw_grid_layer(self, figure_start, grid_pen, painter, task_width, task_height, figure_width, column):
        """
        Method that draws the grid of the Gantt chart.

        Parameters:
            figure_start: tuple[int, int], starting point of the figure
            grid_pen: QPen object, pen for the grid
            painter: QPainter object (painting device)
            task_width: int, width of a task
            task_height: int, height of a task
            figure_width: int, width of the figure
            column: str, column of the data to be drawn
        """
        grid_layer = QImage(self.canvas_size[0], self.canvas_size[1], QImage.Format.Format_ARGB32)
        painter.begin(grid_layer)
        self.set_painter_renderoptions(painter)
        painter.setPen(grid_pen)

        # draw vertical lines
        for i in range((self._loader._data[column].max().date() - self.start_date).days + 2):
            x = figure_start[0] + i * task_width + self.render_metrics.horizontal_padding
            painter.drawLine(x, figure_start[1], x, self.canvas_size[1] - self.render_metrics.vertical_padding)

        # draw horizontal lines
        for i in range(len(self._loader._data) + 1):
            y = figure_start[1] + self.render_metrics.vertical_padding + i * task_height
            painter.drawLine(
                figure_start[0] - self.render_metrics.legend_width, y,
                figure_start[0] + figure_width, y)

        painter.end()
        return grid_layer

    def draw_box_layer(self, box_pen, figure_start, width, height, painter):
        """
        Method that draws the box of the Gantt chart.

        Parameters:
            box_pen: QPen object, pen for the box
            figure_start: tuple[int, int], starting point of the figure
            width: int, width of the box
            height: int, height of the box
            painter: QPainter object (painting device)
        """
        box_layer = QImage(self.canvas_size[0], self.canvas_size[1], QImage.Format.Format_ARGB32)
        painter.begin(box_layer)
        self.set_painter_renderoptions(painter)
        painter.setPen(box_pen)
        # draw figure box
        painter.drawRect(
            figure_start[0],
            figure_start[1],
            width,
            height
        )
        painter.end()
        return box_layer

    def draw_title(self, box_layer, painter, title_pen, title: str = "Gantt Chart"):
        """
        Method that draws the title of the Gantt chart.

        Parameters:
            box_layer: QImage object where the title is drawn
            painter: QPainter object (painting device)
            title_pen: QPen object, pen for the title
            title: str, title of the Gantt chart
        """
        painter.begin(box_layer)
        self.set_painter_renderoptions(painter)
        painter.setPen(title_pen)
        painter.setFont(self.title_font)
        painter.drawText(
            0,
            self.render_metrics.title_padding,
            self.canvas_size[0],
            self.render_metrics.title_height,
            Qt.AlignmentFlag.AlignCenter,
            title)
        painter.end()
        return box_layer

    def draw_legend(self, box_layer, painter, pen, figure_start, task_height, font):
        """
        Method that draws the legend of the Gantt chart.

        Parameters:
            box_layer: QImage object where the legend is drawn
            painter: QPainter object (painting device)
            pen: QPen object, pen for the legend
            figure_start: tuple[int, int], starting point of the figure
            task_height: int, height of a task
            font: QFont object, font for the legend
        """
        painter.begin(box_layer)
        self.set_painter_renderoptions(painter)
        painter.setPen(pen)
        painter.setFont(font)
        for i, task in enumerate(self._loader._data.itertuples()):
            y = figure_start[1] + self.render_metrics.vertical_padding + i * task_height
            x = self.render_metrics.horizontal_padding
            painter.drawText(
                x,
                y,
                self.render_metrics.legend_width,
                task_height,
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                self._loader._data['Task'][i] + ": " + self._loader._data['Description'][i],
            )
        painter.end()
        return box_layer

    def _define_task_height(self, height) -> int:
        if self.canvas_size is None:
            raise ValueError("canvas_size not set")
        height -= 2 * self.render_metrics.vertical_padding
        num_tasks = len(self._loader._data)
        if int(height / num_tasks) < self.render_metrics.min_task_height:
            raise ValueError("Canvas too small for all tasks or RenderMetrics inappropriately set")
        return int(height / num_tasks)

    def _define_task_width(self, width: int) -> int:
        if self.canvas_size is None:
            raise ValueError("canvas_size not set")
        av_width = width - 2 * self.render_metrics.horizontal_padding
        time_span = self._loader._data['Plan-End'].max().date() - self.start_date
        time_span = int(time_span.days)
        if int(av_width / time_span) < 1:
            raise ValueError("Canvas too small for all tasks or RenderMetrics inappropriately set")
        return int(av_width / time_span)

    def _define_drawing_start(self) -> tuple[int, int]:
        if self.canvas_size is None:
            raise ValueError("canvas_size not set")
        x = (self.render_metrics.legend_width
             + self.render_metrics.axis_width
             + self.render_metrics.horizontal_padding)
        y = (self.render_metrics.title_height
             + self.render_metrics.title_padding
             + self.render_metrics.vertical_padding
             + self.render_metrics.axis_height
             )
        return x, y

