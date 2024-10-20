import datetime
import sys
import pandas as pd
import os
from PySide6.QtGui import QImage, QPainter, QPen, QFont, QGuiApplication, QColor, QBrush, QPainterPath, QPixmap, \
    QFontMetrics
from PySide6.QtCore import Qt, QObject
from PySide6.QtWidgets import QApplication

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
    legend_width: int = 620


class RenderElementProperties(QObject):

    def __init__(self, parent=None):
        """
        Class that holds the properties of the box of the Gantt chart.
        """
        super().__init__(parent)
        self._line_width: float = 2
        self._line_color: QColor = QColor('black')
        self._line_style: Qt.PenStyle = Qt.PenStyle.SolidLine
        self._brush: QBrush = QBrush(QColor('transparent'))

    @staticmethod
    def penstyle_from_str(style: str) -> Qt.PenStyle:
        if not isinstance(style, str):
            raise TypeError("style must be a string")
        match style:
            case '-':
                style = Qt.PenStyle.SolidLine
            case '--':
                style = Qt.PenStyle.DashLine
            case '-.':
                style = Qt.PenStyle.DashDotLine
            case ':':
                style = Qt.PenStyle.DotLine
            case _:
                try:
                    style = Qt.PenStyle(style)
                except:
                    raise ValueError("Unknown linestyle")
        return style

    @staticmethod
    def brush_from_source(brush) -> QBrush:
        try:
            brush = QBrush(QColor(brush))
        except ValueError:
            raise ValueError("Unknown brush color")
        return brush

    @property
    def line_width(self) -> float:
        """
        Property that holds the linewidth.

        Returns:
            int: linewidth
        """
        return self._line_width

    @line_width.setter
    def line_width(self, width: float):
        if not isinstance(width, float):
            raise TypeError("box_width must be a float")
        if width < 0:
            raise ValueError("box_width must be a positive float")
        self._line_width = width

    @property
    def line_color(self) -> QColor:
        """
        Property that holds the color of the graph box border.

        Returns:
            QColor: box color
        """
        return self._line_color

    @line_color.setter
    def line_color(self, color: QColor):
        if not isinstance(color, QColor):
            try:
                color = QColor(color)
            except Exception:
                raise TypeError("box_color must be a QColor object")
        self._line_color = color

    @property
    def line_style(self) -> Qt.PenStyle:
        """
        Property that holds the linestyle of the graph box border.

        Returns:
            PenStyle: box penstyle
        """
        return self._line_style

    @line_style.setter
    def line_style(self, style: Qt.PenStyle | str):
        if isinstance(style, str):
            style = self.penstyle_from_str(style)
        elif not isinstance(style, Qt.PenStyle):
            raise TypeError("linestyle must be a Qt.PenStyle object, not a "+str(type(style)))
        self._line_style = style

    @property
    def brush(self) -> QBrush:
        """
        Property that holds the brush of the graph box.

        Returns:
            QBrush: box brush
        """
        return self._brush

    @brush.setter
    def brush(self, brush: QBrush | str):
        if not isinstance(brush, QBrush):
            try:
                brush = self.brush_from_source(brush)
            except ValueError:
                raise TypeError("brush must be a QBrush object or convertible")
        self._brush = brush

    @property
    def pen(self) -> QPen:
        return QPen(self._line_color, self._line_width, self._line_style)



class TaskProperties(RenderElementProperties):

    def __init__(self):
        super().__init__(None)
        self._alpha_actual = 127
        self._alpha_plan = 0
        self._corner_radius = 0

    @property
    def corner_radius(self) -> float:
        """
        Property that holds the corner radius of the task box.

        Returns:
            float: corner radius
        """
        return self._corner_radius

    @corner_radius.setter
    def corner_radius(self, radius: float):
        if not isinstance(radius, float):
            raise TypeError("corner_radius must be a float")
        self._corner_radius = radius

    @property
    def alpha_plan(self) -> int:
        """
        Property that holds the alpha value of the plan.

        Returns:
            int: alpha value
        """
        return self._alpha_plan

    @property
    def alpha_actual(self) -> int:
        """
        Property that holds the alpha value of the actual data.

        Returns:
            int: alpha value
        """
        return self._alpha_actual

    @alpha_actual.setter
    def alpha_actual(self, alpha: int):
        if not isinstance(alpha, int):
            raise TypeError("alpha_actual must be an integer")
        if alpha < 0 or alpha > 255:
            raise ValueError("alpha_actual must be between 0 and 255")
        self._alpha_actual = alpha

    @alpha_plan.setter
    def alpha_plan(self, alpha: int):
        if not isinstance(alpha, int):
            raise TypeError("alpha_plan must be an integer")
        if alpha < 0 or alpha > 255:
            raise ValueError("alpha_plan must be between 0 and 255")
        self._alpha_plan = alpha


class FontProperties(RenderElementProperties):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._font = QFont('Arial', 12)
        self._text = 'Gantt Chart'

    @property
    def font(self) -> QFont:
        """
            Property that holds the font of the text.

            Returns:
                QFont: font
            """
        return self._font

    @font.setter
    def font(self, font: QFont):
        if not isinstance(font, QFont):
            raise TypeError("font must be a QFont object")
        self._font = font

    @property
    def text(self) -> str:
        """
            Property that holds the text.

            Returns:
                str: text
            """
        return self._text

    @text.setter
    def text(self, text: str):
        try:
            text = str(text)
        except ValueError:
            raise ValueError("text must be a string")
        self._text = text

class TitleProperties(FontProperties):
    def __init__(self):
        super().__init__(None)

    @property
    def font(self) -> QFont:
        """
            Property that holds the font of the text.

            Returns:
                QFont: font
            """
        return self._font

    @font.setter
    def font(self, font: QFont):
        if not isinstance(font, QFont):
            raise TypeError("font must be a QFont object")
        self._font = font
        fontsize = self._font.pointSize()
        RenderMetrics.title_height = fontsize + 5

class AxesProperties(FontProperties):
    def __init__(self):
        super().__init__(None)

    @property
    def font(self) -> QFont:
        """
            Property that holds the font of the text.

            Returns:
                QFont: font
            """
        return self._font

    @font.setter
    def font(self, font: QFont):
        if not isinstance(font, QFont):
            raise TypeError("font must be a QFont object")
        self._font = font
        fontsize = self._font.pointSize()
        RenderMetrics.axis_height = fontsize * 2

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
        self.arrow_properties: RenderElementProperties = RenderElementProperties()
        self.arrow_properties.line_color = QColor('black')
        self.arrow_properties.line_width = 2.0
        self.arrow_properties.line_style = Qt.PenStyle.SolidLine
        self.arrow_properties.brush = QBrush(QColor('black'))

        self.title_properties: TitleProperties = TitleProperties()
        self.title_properties.line_color = QColor('black')
        self.title_properties.line_width = 2.0
        self.title_properties.line_style = Qt.PenStyle.SolidLine
        self.title_properties.brush = QBrush(QColor('black'))
        self.title_properties.font = QFont('Arial', 64)

        self.legend_properties: FontProperties = FontProperties()
        self.legend_properties.line_color = QColor(_colors[0])
        self.legend_properties.line_width = 2.0
        self.legend_properties.line_style = Qt.PenStyle.SolidLine
        self.legend_properties.brush = QBrush(QColor('black'))
        self.legend_properties.font = QFont('Arial', 32)

        self.box_properties: RenderElementProperties = TaskProperties()
        self.box_properties.line_color = QColor(_colors[0])
        self.box_properties.line_width = 2.0
        self.box_properties.line_style = Qt.PenStyle.SolidLine
        self.box_properties.brush = QBrush(QColor('transparent'))
        self.box_properties.corner_radius = 1.0

        self.grid_properties: RenderElementProperties = RenderElementProperties()
        self.grid_properties.line_color = QColor('gray')
        self.grid_properties.line_width = 0.5
        self.grid_properties.line_style = Qt.PenStyle.DotLine
        self.grid_properties.brush = QBrush(QColor('transparent'))

        self.axes_properties: AxesProperties = AxesProperties()
        self.axes_properties.line_color = QColor(_colors[0])
        self.axes_properties.line_width = 1.0
        self.axes_properties.line_style = Qt.PenStyle.SolidLine
        self.axes_properties.brush = QBrush(QColor('transparent'))
        self.axes_properties.font = QFont('Arial', 24)

        self.week_highlight_properties: RenderElementProperties = RenderElementProperties()
        self.week_highlight_properties.line_color = QColor(_colors[0])
        self.week_highlight_properties.line_width = 0.75
        self.week_highlight_properties.line_style = Qt.PenStyle.SolidLine
        self.week_highlight_properties.brush = QBrush(QColor('transparent'))

        self.month_highlight_properties: RenderElementProperties = RenderElementProperties()
        self.month_highlight_properties.line_color = QColor(_colors[0])
        self.month_highlight_properties.line_width = 2.5
        self.month_highlight_properties.line_style = Qt.PenStyle.SolidLine
        self.month_highlight_properties.brush = QBrush(QColor('transparent'))

        self.task_properties: TaskProperties = TaskProperties()
        self.task_properties.line_color = QColor(_colors[0])
        self.task_properties.line_width = 2.0
        self.task_properties.line_style = Qt.PenStyle.SolidLine
        self.task_properties.brush = QBrush(QColor(_colors[0]))
        self.task_properties.corner_radius = 1.0

        self._background_color: QColor = QColor('transparent')
        self._export_file: str | None = 'gantt_diagram.png'
        self._start_date: datetime.date | None = None
        self._canvas_size: tuple[int, int] | None = None
        self._unit: float = _units['px']
        self._loader: 'Dataloader' | None = None
        self.render_metrics: RenderMetrics = RenderMetrics()

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
        pass
        #painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        #painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        #painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

    def draw(self, loader: Dataloader) -> QPixmap:
        """
        First perform guard checks.
        Second loads data using Dataloader instance.
        Third creates a new or gets an existing QApplication instance.
        Then the image is rendered:
        1.) Calculate the start coordinates as well as width and height of the figure box.
        2.) Calculate the height and width of a day of a task.
        3.) Draw the box layer
        4.) Draw the title layer
        5.) Draw the legend layer
        6.) Draw the grid layer
        7.) Draw time hints for the beginning of the week and month
        8.) Draw the planned tasks
        9.) Draw the actual tasks
        10.) Draw the axis layer
        11.) Draw the arrows
        12.) Combine all layers

        Parameters:
            loader: Dataloader object that contains the data to be drawn

        Returns:
            None
        """
        # First
        if self.start_date is None:
            raise ValueError("start_date not set")
        if self.canvas_size is None:
            raise ValueError("canvas_size not set")
        if not isinstance(loader, Dataloader):
            raise TypeError("data must be a pandas.DataFrame object")

        # Second
        self._loader = loader
        if self._loader._data is None:
            self._loader.load()

        # Third
        if not QGuiApplication.instance():
            app = QApplication(sys.argv)
        else:
            app = QApplication.instance()
        # 1.)
        figure_start: tuple[int, int] = self._define_drawing_start()
        figure_width = self.canvas_size[0] - figure_start[0] - self.render_metrics.horizontal_padding
        figure_height = (self.canvas_size[1]
                         - figure_start[1]
                         - self.render_metrics.vertical_padding
                         - self.render_metrics.axis_height
                         - self.render_metrics.vertical_padding)
        # 2.)
        task_height: int = self._define_task_height(figure_height)
        task_width: int = self._define_task_width(figure_width)

        # draw image layers
        # 3.)
        box_layer = self.draw_box_layer(figure_start, figure_width, figure_height)
        box_layer.save('0_box_layer.png')
        # 4.)
        title_layer = self.draw_title()
        title_layer.save('1_title_layer.png')
        # 5.)
        legend_layer = self.draw_legend(figure_start, task_height)
        legend_layer.save('2_legend_layer.png')
        # 6.)
        grid_layer = self.draw_grid_layer(figure_start, task_width, task_height, figure_width, 'Plan-End')
        grid_layer.save('3_grid_layer.png')
        # 7.)
        monday_layer = self.draw_monday_lines(figure_start, task_width, 'Plan-End')
        monday_layer.save('4_monday_layer.png')
        # 8.)
        graph_layer = self.draw_tasks(figure_start, task_height, task_width, 'Plan-Start', 'Plan-End')
        graph_layer.save('5_graph_layer.png')
        # 9.)
        actual_layer = self.draw_tasks(figure_start, task_height, task_width, 'Actual-Start', 'Actual-End', plan=False)
        actual_layer.save('6_actual_layer.png')
        # 10.)
        axes_layer = self.draw_xaxis(figure_start, figure_height, task_width,'Plan-End')
        axes_layer.save('7_axes_layer.png')
        # 11.)
        arrows_layer = self.draw_arrows(figure_start, task_width, task_height)
        arrows_layer.save('8_arrows_layer.png')

        # 12.)
        image = QImage(self.canvas_size[0], self.canvas_size[1], QImage.Format.Format_ARGB32)
        image.fill(self.background_color)
        painter = QPainter()
        painter.begin(image)
        painter.drawImage(0, 0, box_layer)
        #image.save('combined_0.png')
        painter.drawImage(0, 0, title_layer)
        #image.save('combined_1.png')
        painter.drawImage(0, 0, legend_layer)
        #image.save('combined_2.png')
        painter.drawImage(0, 0, grid_layer)
        #image.save('combined_3.png')
        painter.drawImage(0, 0, axes_layer)
        #image.save('combined_4.png')
        painter.drawImage(0, 0, monday_layer)
        #image.save('combined_5.png')
        painter.drawImage(0, 0, graph_layer)
        #image.save('combined_6.png')
        painter.drawImage(0, 0, actual_layer)
        #image.save('combined_7.png')
        painter.drawImage(0, 0, arrows_layer)
        #image.save('combined_8.png')
        painter.end()

        # save image
        image.save(self.export_file)
        return QPixmap.fromImage(image.copy())

    def draw_arrows(self, start, t_width, t_height):
        """
        Method that draws arrows at the end of each task.
        Creates a QPainter object and a QImage object using the canvas size.
        Configure the painter object with pen and brush from the arrow_properties and set hints for rendering.
        Iterating over the data, the predecessors of each task are determined.
        If a task has predecessors, the start and end date of the predecessor are determined.
        The x and y coordinates of the predecessor are calculated.
        A circle is drawn at the end of the predecessor.
        A vertical line is drawn from the end of the predecessor to the y-coordinate of the task.
        A horizontal line to the beginning of the task is drawn.
        An arrow head is drawn at the end of the horizontal line.
        If the end date of the predecessor is the same as the start date of the task,
        the horizontal line will basically not be visible and the arrow will always face down.

        Parameters:
            start: tuple[int, int], starting point of the figure
            t_width: int, width of a task
            t_height: int, height of a task

        Returns:
            QImage: arrows layer
        """

        arrowslayer = QImage(self.canvas_size[0], self.canvas_size[1], QImage.Format.Format_ARGB32)
        painter = QPainter()
        painter.begin(arrowslayer)
        painter.setPen(self.arrow_properties.pen)
        painter.setBrush(self.arrow_properties.brush)
        for i, task in enumerate(self._loader.data.itertuples()):
            predecessors: list = str(self._loader.data['Predecessor'].loc[i]).split(';')
            if predecessors[0] != 'nan':
                # print(predecessors)
                for j, pred in enumerate(predecessors):
                    record = self._loader.data[self._loader.data['Task'] == pred]
                    start_date = record['Actual-End'].iloc[0].date()
                    end_date = self._loader.data['Actual-Start'][i].date()
                    x_start = ((start_date - self.start_date).days + 1) * t_width + start[
                        0] + self.render_metrics.horizontal_padding - t_width / 2
                    pred_idx = self._loader.data.index[self._loader.data['Task'] == pred].tolist()[0]
                    y_start = start[1] + self.render_metrics.vertical_padding + pred_idx * t_height + t_height / 2
                    if start_date == end_date:
                        x_end = (end_date - self.start_date).days * t_width + start[
                            0] + self.render_metrics.horizontal_padding + t_width / 2
                    else:
                        x_end = (end_date - self.start_date).days * t_width + start[
                            0] + self.render_metrics.horizontal_padding
                    if len(predecessors) > 1:
                        y_end = start[1] + self.render_metrics.vertical_padding + i * t_height + j * (
                                t_height / len(predecessors)) + (t_height / len(predecessors)) / 2
                    else:
                        y_end = start[1] + self.render_metrics.vertical_padding + i * t_height + t_height / 2
                    circle = 0.1 * t_height
                    pen = painter.pen()
                    pen.setColor(QColor(_colors[pred_idx % len(_colors)]))
                    brush = QBrush(pen.color())
                    painter.setBrush(brush)
                    painter.setPen(pen)

                    # define arrow head
                    arrow_head = QPainterPath()
                    if start_date == end_date:
                        arrow_head.moveTo(x_end - circle / 2, y_end - circle * 2)
                        arrow_head.lineTo(x_end + circle / 2, y_end - circle * 2)
                        arrow_head.lineTo(x_end, y_end)
                        arrow_head.closeSubpath()
                    else:
                        arrow_head.moveTo(x_end - circle * 2, y_end - circle / 2)
                        arrow_head.lineTo(x_end - circle * 2, y_end + circle / 2)
                        arrow_head.lineTo(x_end, y_end)
                        arrow_head.closeSubpath()

                    # starting dot
                    painter.drawEllipse(x_start - circle / 2, y_start - circle / 2, circle, circle)

                    # connection lines
                    painter.drawLine(x_start, y_start, x_start, y_end)
                    painter.drawLine(x_start, y_end, x_end, y_end)

                    # arrow head
                    painter.drawPath(arrow_head)

        painter.end()
        return arrowslayer

    def draw_monday_lines(self, figure_start, task_width, column):
        """
        Method that draws vertical lines at the beginning of each week and month.
        Creates two QPainter objects and two QImage objects using the canvas size.
        Configure the painter objects with color, pen and brush from the week_highlight_properties and set hints for rendering.
        A range depending on the maximum date in the data and the start date is calculated.
        While iterating over this range a vertical line for each week is drawn.
        Configures the painter for monthly hints with color, pen and brush from the month_highlight_properties and set hints for rendering.
        While iterating over the range a vertical line for each month is drawn.

        Parameters:
            figure_start: tuple[int, int], starting point of the figure
            task_width: int that defines the width of a task
            column: str, column of the data that is used to determine the maximum date
        """
        layer = QImage(self.canvas_size[0], self.canvas_size[1], QImage.Format.Format_ARGB32)
        monday_painter = QPainter()
        monthly_painter = QPainter()
        monday_painter.begin(layer)
        monday_painter.setPen(self.week_highlight_properties.pen)
        monday_painter.setBrush(self.week_highlight_properties.brush)
        dates = (self._loader.data[column].max().date() - self.start_date).days + 1
        for i in range(dates):
            if (self.start_date + datetime.timedelta(days=i)).weekday() == 0:
                x = int(figure_start[0] + i * task_width + self.render_metrics.horizontal_padding)
                monday_painter.drawLine(x, figure_start[1], x,
                                        self.canvas_size[1] - self.render_metrics.vertical_padding)
        monday_painter.end()
        monthly_painter.begin(layer)
        monthly_painter.setPen(self.month_highlight_properties.pen)
        monthly_painter.setBrush(self.month_highlight_properties.brush)
        for i in range(dates):
            if (self.start_date + datetime.timedelta(days=i)).day == 1:
                x = int(figure_start[0] + i * task_width + self.render_metrics.horizontal_padding)
                monthly_painter.drawLine(x, figure_start[1] - self.render_metrics.axis_height, x,
                                         self.canvas_size[1] - self.render_metrics.vertical_padding)
        monthly_painter.end()
        return layer

    def draw_xaxis(self, start, height, task_width, column):
        """
        Method that draws the x-axis of the Gantt chart.
        Creates a QPainter object and a QImage object using the canvas size.
        Configure the painter object with pen and brush from the axes_properties and set hints for rendering.
        A range depending on the maximum date in the data and the start date is calculated.
        Iterating over this range, x-coordinates are calculated depending on the task_width and figure_start.
        The first two letters of the weekday and the day of the month are drawn at the x-coordinates.
        As well as the number of the day in month beneath.
        If the day is the first of the month, the month and year are drawn as formatted string above the figure.
        At the end the creation date is drawn at the bottom left of the figure.

        Parameters:
            start: tuple[int, int], starting point of the figure
            height: int, height of the figure
            task_width: int, width of a task
            column: str, column of the data to be drawn

        Returns:
            QImage: axes layer
        """
        painter = QPainter()
        axes_layer = QImage(self.canvas_size[0], self.canvas_size[1], QImage.Format.Format_ARGB32)
        painter.begin(axes_layer)
        painter.setPen(self.axes_properties.pen)
        painter.setBrush(self.axes_properties.brush)
        painter.setFont(self.axes_properties.font)
        dates = (self._loader.data[column].max().date() - self.start_date).days + 1
        for i in range(dates):
            x = int(start[0]
                    + i * task_width
                    + self.render_metrics.horizontal_padding
                    )
            y = self.canvas_size[1] - self.render_metrics.vertical_padding - self.render_metrics.axis_height//2
            date = self.start_date + datetime.timedelta(days=i)
            text = date.strftime('%A')[0:2]
            day_text = date.strftime('%d')
            painter.drawText(
                x, y,
                task_width, self.render_metrics.axis_height//2,
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom,
                text
            )
            painter.drawText(
                x, y - self.render_metrics.axis_height//2 - self.render_metrics.axis_padding,
                task_width, self.render_metrics.axis_height//2 + self.render_metrics.axis_padding,
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                day_text
            )
            if date.day == 1:
                metrics = QFontMetrics(self.axes_properties.font)
                font_width = metrics.horizontalAdvance(date.strftime('%B %Y'))
                if x + self.render_metrics.horizontal_padding + font_width > self.canvas_size[0]:
                    continue
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
            self.render_metrics.horizontal_padding*2,
            self.canvas_size[1] - self.render_metrics.vertical_padding*2 - self.render_metrics.axis_height,
            self.canvas_size[0] - self.render_metrics.horizontal_padding * 2,
            self.render_metrics.axis_height + self.render_metrics.vertical_padding,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom,
            'created: ' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        painter.end()

        return axes_layer

    def draw_tasks(self, figure_start: tuple[int, int], task_height: int, task_width: int, start_column, end_column, plan=True):
        """
        Method that draws the tasks of the Gantt chart.
        Creates a QPainter object and a QImage object using the canvas size.
        Configure the painter object with pen and brush from the task_properties and set hints for rendering.
        the colors of the tasks are determined by the index of the task in the dataframe.
        The alpha value of the plan and actual data is set in the task_properties.
        For each task in the dataframe a rectangle is drawn with the start and end date of the task.
        The height is determined by the task_height.

        Parameters:
            figure_start: tuple[int, int], starting point of the figure
            task_height: int, height of a task
            task_width: int, width of a task
            start_column: str, column of the data to be drawn
            end_column: str, column of the data to be drawn
            plan: bool, if True, the plan is drawn, if False, the actual data is drawn

        Returns:
            QImage: graph layer
        """
        painter = QPainter()
        graph_layer = QImage(self.canvas_size[0], self.canvas_size[1], QImage.Format.Format_ARGB32)
        painter.begin(graph_layer)
        painter.setPen(self.task_properties.pen)
        painter.setBrush(self.task_properties.brush)
        self.set_painter_renderoptions(painter)
        for i, task in enumerate(self._loader.data.itertuples()):
            pen = painter.pen()
            pen.setColor(QColor(_colors[i % len(_colors)]))
            painter.setPen(pen)
            brush_color = QColor(_colors[i % len(_colors)])
            if plan:
                brush_color.setAlpha(self.task_properties.alpha_plan)
            else:
                brush_color.setAlpha(self.task_properties.alpha_actual)
            brush = painter.brush()
            brush.setColor(brush_color)
            painter.setBrush(brush)
            plan_start = self._loader.data[start_column][i].date()
            plan_end = self._loader.data[end_column][i].date()
            x_start = figure_start[0] + task_width * (
                    plan_start - self.start_date).days + self.render_metrics.horizontal_padding
            x_end = figure_start[0] + task_width * (
                    plan_end - self.start_date).days + self.render_metrics.horizontal_padding
            width = x_end - x_start + task_width
            y = figure_start[1] + self.render_metrics.vertical_padding + i * task_height
            painter.drawRect(x_start, y, width, task_height)
        painter.end()
        return graph_layer

    def draw_grid_layer(self, figure_start, task_width, task_height, figure_width, column):
        """
        Method that draws the grid of the Gantt chart.
        Creates a QPainter object and a QImage object using the canvas size.
        Configure the painter object with color, pen and brush from the grid_properties and set hints for rendering.
        A range depending of the maximum date in the data and the start date is calculated.
        While iterating over this range a vertical line for each day is drawn.
        For horizontal lines the number of tasks is determined by the length of the dataframe. The horizontal lines are
        drawn for each task.

        Parameters:
            figure_start: tuple[int, int], starting point of the figure
            task_width: int, width of a task
            task_height: int, height of a task
            figure_width: int, width of the figure
            column: str, column of the data that is used to determine the maximum date

        Returns:
            QImage: grid layer
        """
        grid_layer = QImage(self.canvas_size[0], self.canvas_size[1], QImage.Format.Format_ARGB32)
        painter = QPainter()
        painter.begin(grid_layer)
        painter.setPen(self.grid_properties.pen)
        painter.setBrush(self.grid_properties.brush)
        self.set_painter_renderoptions(painter)

        # draw vertical lines
        for i in range((self._loader.data[column].max().date() - self.start_date).days + 2):
            x = figure_start[0] + i * task_width + self.render_metrics.horizontal_padding
            painter.drawLine(x, figure_start[1], x, self.canvas_size[1] - self.render_metrics.vertical_padding)

        # draw horizontal lines
        for i in range(len(self._loader.data) + 1):
            y = figure_start[1] + self.render_metrics.vertical_padding + i * task_height
            painter.drawLine(
                figure_start[0] - self.render_metrics.legend_width, y,
                figure_start[0] + figure_width, y)
        painter.end()
        return grid_layer

    def draw_box_layer(self, figure_start, width, height):
        """
        Method that draws the box of the Gantt chart.
        First initializes a QPainter object.
        Second initialize a QImage object using the canvas size.
        Configure the painter object with color, pen and brush from the box_properties and set hints for rendering.
        Draw the box rectangle.

        Parameters:
            figure_start: tuple[int, int], starting point of the figure
            width: int, width of the box
            height: int, height of the box

        Returns:
            QImage: box layer
        """
        painter = QPainter()
        box_layer = QImage(self.canvas_size[0], self.canvas_size[1], QImage.Format.Format_ARGB32)
        painter.begin(box_layer)
        painter.setPen(self.box_properties.pen)
        painter.setBrush(self.box_properties.brush)
        self.set_painter_renderoptions(painter)
        # draw figure box
        painter.drawRect(
            figure_start[0],
            figure_start[1],
            width,
            height
        )
        painter.end()
        return box_layer

    def draw_title(self):
        """
        Method that draws the title of the Gantt chart.
        First initializes a QPainter object and a QImage object using the canvas size.
        Configure the painter object with color, pen and brush from the title_properties and set hints for rendering.
        Draw the title text using dimensions from the render_metrics.

        Returns:
            QImage: title layer
        """
        painter = QPainter()
        title_layer = QImage(self.canvas_size[0], self.canvas_size[1], QImage.Format.Format_ARGB32)
        painter.begin(title_layer)
        painter.setPen(self.title_properties.pen)
        painter.setFont(self.title_properties.font)
        painter.setBrush(self.title_properties.brush)
        self.set_painter_renderoptions(painter)
        painter.drawText(
            self.render_metrics.horizontal_padding,
            self.render_metrics.title_padding,
            self.canvas_size[0] - self.render_metrics.horizontal_padding * 2,
            self.render_metrics.title_height,
            Qt.AlignmentFlag.AlignCenter,
            self.title_properties.text)
        painter.end()
        return title_layer

    def draw_legend(self, figure_start, task_height):
        """
        Method that draws the legend of the Gantt chart.
        First create a QPainter object and a QImage object using the canvas size.
        Configure the painter object with color, pen and brush from the legend_properties and set hints for rendering.
        Iterate over the dataframe stored in Dataloader object.
        The vertical starting position of each legend entry is determined by the top edge of the figure box and the task height
        as well as the index in the dataframe.
        The horizontal starting position is determined by the horizontal padding of the render_metrics attribute.
        The height of a legend entry is the task height. The width is determined legend_width from the render_metrics attribute.

        Parameters:
            figure_start: tuple[int, int], starting point of the figure
            task_height: int, height of a task

        Returns:
            QImage: legend layer
        """
        painter = QPainter()
        legend_layer = QImage(self.canvas_size[0], self.canvas_size[1], QImage.Format.Format_ARGB32)
        painter.begin(legend_layer)
        painter.setPen(self.legend_properties.pen)
        painter.setBrush(self.legend_properties.brush)
        painter.setFont(self.legend_properties.font)
        self.set_painter_renderoptions(painter)
        for i, task in enumerate(self._loader.data.itertuples()):
            y = figure_start[1] + self.render_metrics.vertical_padding + i * task_height
            x = self.render_metrics.horizontal_padding
            painter.drawText(
                x,
                y,
                self.render_metrics.legend_width,
                task_height,
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                self._loader.data['Task'][i] + ": " + self._loader.data['Description'][i],
            )
        painter.end()
        return legend_layer

    def _define_task_height(self, height) -> int:
        if self.canvas_size is None:
            raise ValueError("canvas_size not set")
        height -= 2 * self.render_metrics.vertical_padding
        num_tasks = len(self._loader.data)
        if int(height / num_tasks) < self.render_metrics.min_task_height:
            raise ValueError("Canvas too small for all tasks or RenderMetrics inappropriately set")
        return int(height / num_tasks)

    def _define_task_width(self, width: int) -> int:
        if self.canvas_size is None:
            raise ValueError("canvas_size not set")
        av_width = width - 2 * self.render_metrics.horizontal_padding
        time_span = self._loader.data['Plan-End'].max().date() - self.start_date
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
