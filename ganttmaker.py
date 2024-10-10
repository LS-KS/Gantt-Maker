import datetime
import sys

import pandas as pd
import openpyxl
import os
import PySide6
from PySide6.QtGui import QImage, QPainter, QPen, QFont, QGuiApplication, QColor, QBrush
from PySide6.QtCore import Qt

_units = {
    'pt': 1,                     # 1 point is 1 point
    'px': 1/0.75,                # 1 pixel ≈ 0.75 points (at 96 DPI)
    'mm': 1/0.352778,            # 1 point = 0.352778 mm
    'cm': 1/0.0352778,           # 1 point = 0.0352778 cm
    'in': 72                     # 1 inch = 72 points
}

# color palette: https://www.learnui.design/tools/data-color-picker.html#palette
_colors = ["#003f5c", "#2f4b7c", "#665191", "#a05195", "#d45087", "#f95d6a", "#ff7c43", "#ffa600"]

class Task(object):
    _empty_task = None

    def __new__(cls, *args, **kwargs):
        if Task._empty_task is None:
            Task._empty_task = object.__new__(Task)
        if len(args) == 0 and len(kwargs) == 0:
            return Task._empty_task
        return object.__new__(Task)

    def __str__(self):
        return self.name + ' ' + self.description

    @property
    def children(self) -> list['Task']:
        return self._children

    @children.setter
    def children(self, task: 'Task'):
        raise AttributeError("Use with_children() to add a child and without_children() to remove a child")

    def with_children(self, task: 'Task'):
        """
        This method adds the argument to he children attribute
        Calls arguments with_parents method for self-referencing behaviour.

        Parameters:
          task: 'Task' object that shall be added as a child
        
        Returns:
          None
        
        Raises:
          TypeError: If the object is not a 'Task' object.

        """
        if not isinstance(task, Task):
            raise TypeError("Successor must be a Task object")
        if task in self._children:
            return
        if task not in self._children:
            self._children.append(task)
        if self not in task.parents:
            task.with_parents(self)

    def without_children(self, task: 'Task'):
        """
        This nethod removes the given task from children.
        For self-referencing, calls without_parents method from argument
        
        Parameters:
          task: Task object that shall be removed from children attribute

        Returns:
          None

        Raises:
          TypeError if the argument is not a Task object

        """
        if not isinstance(task, Task):
            raise(TypeError, "Argument is not a 'Task' object")
        if task not in self.children:
            return
        else:
            self._children.remove(task)
            task.without_parents(self)

    def with_parents(self, task: 'Task'):
        if not isinstance(task, Task):
            raise TypeError("parent must be a Task object")
        if task in self._parents:
            return
        else:
            self._parents.append(task)
        if self not in task._children:
            task._children.append(self)

    def without_parents(self, task: 'Task'):
        """
        This nethod removes the given task from parents.
        For self-referencing, calls without_children method from argument
        
        Parameters:
          task: Task object that shall be removed from parents attribute

        Returns:
          None

        Raises:
          TypeError if the argument is not a Task object

        """
        if not isinstance(task, Task):
            raise(TypeError, "Argument is not a 'Task' object")
        if task not in self._parents:
            return
        else:
            self._parents.remove(task)
            task.without_children(self)

    def __init__(self, task_no: str, start: pd.Timestamp, end: pd.Timestamp, description: str, predecessor: str = None):
        self._children = []
        self._parents = []
        self._start = None
        self._end = None
        self._predecessors = []
        self.start: datetime.date = start
        self.end: datetime.date = end
        self.name: str = str(task_no)
        self.description: str = str(description)
        self.predecessors: str = str(predecessor)

    @property
    def parents(self) -> list['Task']:
        return self._parents

    @parents.setter
    def parents(self, task: 'Task'):
        raise AttributeError("Use with_parents() to add a parent and without_parent() to remove a parent")

    @property
    def start(self) -> datetime.date:
        return self._start

    @start.setter
    def start(self, date: datetime.date):
        if isinstance(date, datetime.date):
            self._start = date
        else:
            raise TypeError("start must be a datetime.date object")

    @property
    def end(self) -> datetime.date:
        return self._end

    @end.setter
    def end(self, date: datetime.date):
        if isinstance(date, datetime.date):
            self._end = date
        else:
            raise TypeError("end must be a datetime.date object")

    @property
    def predecessors(self) -> list[str]:
        return self._predecessors

    @predecessors.setter
    def predecessors(self, task: str):
        if isinstance(task, str):
            pres = task.split(';')
            for pre in pres:
                self._predecessors.append(pre)
        else:
            raise TypeError("Predecessor must be a string, delimited by ';'")
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

class Dataloader:
    _file = None
    @property
    def file(self):
        return self._file

    @file.setter
    def file(self, file_string):
        if os.path.exists(file_string):
            self._file = file_string
        else:
            raise FileNotFoundError(f"File {file_string} not found")

    def __init__(self, file_string:str):
        """
        :param file_string: path to a file
        """
        self.file = file_string
        self._data = None

    def load(self):
        # data = openpyxl.load_workbook(self.file)
        data = pd.read_excel(self.file, engine='openpyxl', dtype={'Task': str, 'Predecessor': str})
        self.validate_columns(data)
        data['Plan-Start'] = pd.to_datetime(data['Plan-Start'], format='%d.%m.%Y')
        data['Actual-Start'] = pd.to_datetime(data['Actual-Start'], format='%d.%m.%Y')
        data['Plan-End'] = pd.to_datetime(data['Plan-End'], format='%d.%m.%Y')
        data['Actual-End'] = pd.to_datetime(data['Actual-End'], format='%d.%m.%Y')
        data['Task'] = data['Task']
        data['Predecessor'] = data['Predecessor']
        self._data = data

    def validate_columns(self, data: pd.DataFrame):
        if 'Task' not in data.columns:
            raise ValueError("Column 'Task' missing")
        if 'Plan-End' not in data.columns:
            raise ValueError("Column 'Plan-End' missing")
        if 'Actual-End' not in data.columns:
            raise ValueError("Column 'Actual-End' missing")
        if 'Predecessor' not in data.columns:
            raise ValueError("Column 'Predecessor' missing")

class Figure:
    def __init__(self):
        self._time_highlightline_width = (0.75, 2.5)
        self._time_highlightline_color = None
        self.time_highlightline_color = QColor('red')
        self._background_color = None
        self.background_color = QColor('transparent')
        self._axes_color = None
        self.axes_color = QColor('black')
        self._task_line_width = None
        self.task_line_width = 4
        self._task_brush_saturation = None
        self.task_brush_saturation = 127
        self._box_width = None
        self.box_width = 2
        self._box_color = None
        self.box_color = QColor('black')
        self._export_file = None
        self._start_date: datetime.date = None
        self._canvas_size: tuple[int, int] = None
        self._unit: float = _units['px']
        self._loader = None
        self.render_metrics = RenderMetrics()
        self.title = "Gantt Chart"
        self.title_font = QFont("Arial", 24)
        self._axes_font = None
        self.axes_font = QFont("Arial", 10)
        self._title_font = None
        self._title_color = QColor('black')
        self._legend_font = None
        self.legend_font = QFont("Arial", 12)
        self._legend_color = None
        self.legend_color = QColor('black')

    @property
    def time_highlightline_width(self) -> tuple[float, float]:
        return self._time_highlightline_width

    @time_highlightline_width.setter
    def time_highlightline_width(self, width: tuple[int, int]):
        if not isinstance(width, tuple):
            raise TypeError("time_highlightline_width must be a tuplpe of floats")
        elif len(width) != 2:
            raise ValueError("time_highlightline_width must be a tuple of two floats")
        self._time_highlightline_width = width

    @property
    def time_highlightline_color(self):
        return self._time_highlightline_color

    @time_highlightline_color.setter
    def time_highlightline_color(self, color: QColor):
        if not isinstance(color, QColor):
            raise TypeError("time_highlightline_color must be a QColor object")
        self._time_highlightline_color = color

    @property
    def background_color(self):
        return self._background_color

    @background_color.setter
    def background_color(self, color: QColor):
        if not isinstance(color, QColor):
            raise TypeError("background_color must be a QColor object")
        self._background_color = color

    @property
    def axes_color(self):
        return self._axes_color

    @axes_color.setter
    def axes_color(self, color: QColor):
        if not isinstance(color, QColor):
            raise TypeError("axes_color must be a QColor object")
        self._axes_color = color
    @property
    def axes_font(self):
        return self._axes_font

    @axes_font.setter
    def axes_font(self, font: QFont):
        if not isinstance(font, QFont):
            raise TypeError("axes_font must be a QFont object")
        self._axes_font = font

    @property
    def task_brush_saturation(self):
        return self._task_brush_saturation

    @task_brush_saturation.setter
    def task_brush_saturation(self, saturation: int):
        if not isinstance(saturation, int):
            raise TypeError("task_brush_saturation must be an integer")
        elif saturation < 0 or saturation > 255:
            raise ValueError("task_brush_saturation must be between 0 and 255")
        self._task_brush_saturation = saturation

    @property
    def task_line_width(self):
        return self._task_line_width

    @task_line_width.setter
    def task_line_width(self, width: int):
        if not isinstance(width, int):
            raise TypeError("task_line_width must be an integer")
        self._task_line_width = width

    @property
    def box_width(self):
        return self._box_width

    @box_width.setter
    def box_width(self, width: int):
        if not isinstance(width, int):
            raise TypeError("box_width must be an integer")
        self._box_width = width

    @property
    def box_color(self):
        return self._box_color

    @box_color.setter
    def box_color(self, color: QColor):
        if not isinstance(color, QColor):
            raise TypeError("box_color must be a QColor object")
        self._box_color = color


    @property
    def legend_color(self):
        return self._legend_color

    @legend_color.setter
    def legend_color(self, color: QColor):
        if not isinstance(color, QColor):
            raise TypeError("legend_color must be a QColor object")
        self._legend_color = color

    @property
    def legend_font(self):
        return self._legend_font

    @legend_font.setter
    def legend_font(self, font: QFont):
        if not isinstance(font, QFont):
            raise TypeError("legend_font must be a QFont object")
        self._legend_font = font

    @property
    def title_font(self):
        return self._title_font

    @title_font.setter
    def title_font(self, font: QFont):
        if not isinstance(font, QFont):
            raise TypeError("title_font must be a QFont object")
        self._title_font = font

    @property
    def title_color(self):
        return self._title_color

    @title_color.setter
    def title_color(self, color: QColor):
        if not isinstance(color, QColor):
            raise TypeError("title_color must be a QColor object")
        self._title_color = color

    @property
    def start_date(self):
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
    def unit(self):
        return self._unit

    @unit.setter
    def unit(self, unit: str):
        if not unit in _units:
            raise ValueError(f"Unknown unit {unit}, choose one of {_units.keys()}")
        self._unit = _units[unit]

    @property
    def canvas_size(self):
        return self._canvas_size

    @canvas_size.setter
    def canvas_size(self, size: tuple[int, int]):
        if len(size) == 2:
            self._canvas_size = tuple([int(x * self.unit) for x in size])
        else:
            raise ValueError("canvas_size must be a tuple of two integers")

    @property
    def export_file(self):
        return self._export_file

    @export_file.setter
    def export_file(self, file: str):
        self._export_file = file

    def draw(self, loader: Dataloader):
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

        figure_start: tuple[int, int] = self._define_drawingstart()
        figure_width = self.canvas_size[0] - figure_start[0] - self.render_metrics.horizontal_padding
        figure_height = (self.canvas_size[1]
                         - figure_start[1]
                         - self.render_metrics.vertical_padding
                         - self.render_metrics.axis_height
                         - self.render_metrics.vertical_padding )
        task_height: int = self._define_task_height(figure_height)
        task_width: int = self._define_task_width(figure_width)

        arrows_layer = QImage(self.canvas_size[0], self.canvas_size[1], QImage.Format_ARGB32)
        image = QImage(self.canvas_size[0], self.canvas_size[1], QImage.Format_ARGB32)
        image.fill(self.background_color)

        # painter initialization
        painter = QPainter()

        # pen initialization
        box_pen = QPen(self._box_color, self.box_width, Qt.SolidLine)
        grid_pen = QPen(Qt.gray, 0.5, Qt.DotLine)
        axes_pen = QPen(self.axes_color, 2, Qt.SolidLine)
        legend_pen = QPen(self.legend_color, 2, Qt.SolidLine)
        graph_pen = QPen(Qt.blue, self.task_line_width, Qt.SolidLine)
        title_pen = QPen(self.title_color, 2, Qt.SolidLine)
        arrows_pen = QPen(Qt.black, 2, Qt.SolidLine)

        # draw image layers
        box_layer = self.draw_box_layer(box_pen, figure_start, figure_width, figure_height, painter)
        box_layer = self.draw_title(box_layer, painter, title_pen, figure_start, self.title)
        box_layer = self.draw_legend(box_layer, painter, legend_pen, figure_start, task_height, self.legend_font)
        grid_layer = self.draw_grid_layer(figure_start, grid_pen, painter, task_width, task_height, figure_width)
        grid_layer = self.draw_monday_lines(grid_layer, figure_start, painter, task_width)
        graph_layer = self.draw_tasks(figure_start, graph_pen, self.task_brush_saturation, painter, task_height, task_width)
        axes_layer = self.draw_xaxis(figure_start, figure_width, figure_height, task_width,painter, axes_pen, self.axes_font)

        painter.begin(image)
        painter.drawImage(0, 0, box_layer)
        painter.drawImage(0, 0, grid_layer)
        painter.drawImage(0, 0, axes_layer)
        painter.drawImage(0, 0, graph_layer)
        painter.drawImage(0, 0, arrows_layer)
        painter.end()
        image.save(self.export_file)

    def draw_monday_lines(self, layer, figure_start, painter, task_width):
        monday_pen = QPen(self.time_highlightline_color, self.time_highlightline_width[0], Qt.SolidLine)
        monthly_pen = QPen(self.time_highlightline_color, self.time_highlightline_width[1], Qt.SolidLine)
        painter.begin(layer)
        dates = (self._loader._data['Plan-End'].max().date() - self.start_date).days + 1
        for i in range(dates):
            x = int(figure_start[0] + i * task_width + self.render_metrics.horizontal_padding)
            if (self.start_date + datetime.timedelta(days=i)).weekday() == 0:
                painter.setPen(monday_pen)
                painter.drawLine(x, figure_start[1], x, self.canvas_size[1] - self.render_metrics.vertical_padding)
            if (self.start_date + datetime.timedelta(days=i)).day == 1:
                painter.setPen(monthly_pen)
                painter.drawLine(x, figure_start[1] - self.render_metrics.axis_height, x, self.canvas_size[1] - self.render_metrics.vertical_padding)
        painter.end()
        return layer

    def draw_xaxis(self, start, width, height, task_width,  painter, pen, font):
        axes_layer = QImage(self.canvas_size[0], self.canvas_size[1], QImage.Format_ARGB32)
        painter.begin(axes_layer)
        painter.setPen(pen)
        painter.setFont(font)
        dates = (self._loader._data['Plan-End'].max().date() - self.start_date).days + 1
        for i in range(dates):
            x = int(start[0]
                    + i * task_width
                    + self.render_metrics.horizontal_padding
                 )
            y = start[1] + height + self.render_metrics.vertical_padding
            date = self.start_date + datetime.timedelta(days=i)
            text = date.strftime('%A')[0:2]
            painter.drawText(
                x,y,
                task_width, self.render_metrics.axis_height,
                Qt.AlignmentFlag.AlignCenter,
                text)
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

    def draw_tasks(self, figure_start: tuple[int, int], task_pen: QPen, brush_saturation: int, painter: QPainter, task_height: int, task_width: int):
        graph_layer = QImage(self.canvas_size[0], self.canvas_size[1], QImage.Format_ARGB32)
        painter.begin(graph_layer)
        self.set_painter_renderoptions(painter)
        painter.setPen(task_pen)
        for i, task in enumerate(self._loader._data.itertuples()):
            painter.setPen(QColor(_colors[i % len(_colors)]))
            brush_color = QColor(_colors[i % len(_colors)])
            brush_color.setAlpha(brush_saturation)
            task_brush = QBrush(brush_color)
            painter.setBrush(task_brush)
            plan_start = self._loader._data['Plan-Start'][i].date()
            plan_end = self._loader._data['Plan-End'][i].date()
            x_start = figure_start[0] + task_width * (plan_start - self.start_date).days + self.render_metrics.horizontal_padding
            x_end = figure_start[0] + task_width * (plan_end - self.start_date).days + self.render_metrics.horizontal_padding
            width = x_end - x_start + task_width
            y = figure_start[1] + self.render_metrics.vertical_padding + i * task_height
            painter.drawRect(x_start, y, width, task_height)
        painter.end()
        return graph_layer

    def draw_grid_layer(self, figure_start, grid_pen, painter, task_width, task_height, figure_width):
        grid_layer = QImage(self.canvas_size[0], self.canvas_size[1], QImage.Format_ARGB32)
        painter.begin(grid_layer)
        self.set_painter_renderoptions(painter)
        painter.setPen(grid_pen)

        # draw vertical lines
        for i in range((self._loader._data['Plan-End'].max().date() - self.start_date).days + 2):
            x = figure_start[0] + i * task_width + self.render_metrics.horizontal_padding
            painter.drawLine(x, figure_start[1], x, self.canvas_size[1] - self.render_metrics.vertical_padding)

        # draw horizontal lines
        for i in range(len(self._loader._data)+1):
            y = figure_start[1] + self.render_metrics.vertical_padding + i * task_height
            painter.drawLine(
                figure_start[0] - self.render_metrics.legend_width, y,
                figure_start[0] + figure_width, y)

        painter.end()
        return grid_layer

    def draw_box_layer(self, box_pen, figure_start, width, height, painter):
        box_layer = QImage(self.canvas_size[0], self.canvas_size[1], QImage.Format_ARGB32)
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

    def set_painter_renderoptions(self, painter):
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

    def _define_task_height(self, height) -> int:
        if self.canvas_size is None:
            raise ValueError("canvas_size not set")
        height -= 2* self.render_metrics.vertical_padding
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
        if int(av_width/time_span) < 1:
            raise ValueError("Canvas too small for all tasks or RenderMetrics inappropriately set")
        return int(av_width/time_span)

    def _define_drawingstart(self) -> tuple[int, int]:
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
        return (x, y)

    def draw_title(self, box_layer, painter, title_pen, figure_start, title: str = "Gantt Chart"):
        painter.begin(box_layer)
        self.set_painter_renderoptions(painter)
        painter.setPen(title_pen)
        painter.setFont(self.title_font)
        painter.drawText(
            0,
            self.render_metrics.title_padding,
            self.canvas_size[0],
            self.render_metrics.title_height,
            Qt.AlignCenter,
            title)
        painter.end()
        return box_layer

    def draw_legend(self, box_layer, painter, pen,  figure_start, task_height, font):
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
                self._loader._data['Task'][i] +": " + self._loader._data['Description'][i],
            )
        painter.end()
        return box_layer

