import datetime
import warnings
import pandas as pd
import openpyxl
import os


_units = {
    'pt': 1,                     # 1 point is 1 point
    'px': 1/0.75,                # 1 pixel ≈ 0.75 points (at 96 DPI)
    'mm': 1/0.352778,            # 1 point = 0.352778 mm
    'cm': 1/0.0352778,           # 1 point = 0.0352778 cm
    'in': 72                     # 1 inch = 72 points
}

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
    title_height: int = 20
    title_padding: int = 10
    vertical_padding: int = 10
    horizontal_padding: int = 5
    axis_width: int = 20
    axis_height: int = 20
    axis_padding: int = 10

    min_task_height: int = 20
    max_task_description_width: int = 200

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
        self._start_date: datetime.date = None
        self._canvas_size: tuple[int, int] = None
        self._unit: float = _units['px']
        self._loader = None
        self.render_metrics = RenderMetrics()

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

    def draw(self, loader: Dataloader):
        if self.start_date is None:
            raise ValueError("start_date not set")
        if self.canvas_size is None:
            raise ValueError("canvas_size not set")
        if not isinstance(loader, Dataloader):
            raise TypeError("data must be a pandas.DataFrame object")
        self._loader = loader
        if self._loader._data is None:
            self._loader.load()
        task_height: int = self._define_task_height()
        task_width: int = self._define_task_width()
        figure_start: tuple[int, int]  = self._define_drawingstart()
        tasks = self._compute_task_chain()
        self._update_start_dates(tasks)
        critical_path = self._compute_critical_path(tasks)

    def _define_task_height(self) -> int:
        if self.canvas_size is None:
            raise ValueError("canvas_size not set")
        height = self.canvas_size[1]
        av_height = height - self.render_metrics.title_height
        av_height -= self.render_metrics.title_padding
        av_height -= self.render_metrics.vertical_padding
        av_height -= self.render_metrics.axis_height
        av_height -= self.render_metrics.axis_padding * 2
        num_tasks = len(self._loader._data)
        if int(av_height / num_tasks) < self.render_metrics.min_task_height:
            raise ValueError("Canvas too small for all tasks or RenderMetrics inappropriately set")
        return int(av_height / num_tasks)

    def _define_task_width(self) -> int:
        if self.canvas_size is None:
            raise ValueError("canvas_size not set")
        width = self.canvas_size[0]
        av_width = width - self.render_metrics.axis_width
        av_width -= self.render_metrics.horizontal_padding * 3
        av_width -= self.render_metrics.max_task_description_width
        time_span = self._loader._data['Plan-End'].max().date() - self.start_date
        time_span = int(time_span.days)
        if int(av_width/time_span) < 1:
            raise ValueError("Canvas too small for all tasks or RenderMetrics inappropriately set")
        return int(av_width/time_span)

    def _define_drawingstart(self) -> tuple[int, int]:
        if self.canvas_size is None:
            raise ValueError("canvas_size not set")
        x = self.render_metrics.axis_width + self.render_metrics.horizontal_padding
        y = self.render_metrics.title_height + self.render_metrics.title_padding + self.render_metrics.vertical_padding
        return (x, y)

    def _compute_task_chain(self) -> Task:
        tasks = []
        for i in range(0, len(self._loader._data)):
            task = Task(
                self._loader._data['Task'][i],
                self._loader._data['Plan-End'][i],
                self._loader._data['Actual-End'][i],
                self._loader._data['Description'][i],
                self._loader._data['Predecessor'][i],
            )
            tasks.append(task)
        initial_task = tasks.pop(0)
        main_task = initial_task
        while len(tasks) >0:
            for i, subtask in enumerate(tasks):
                if str(main_task.name) in subtask.predecessors:
                    main_task.with_children(subtask)
            main_task = tasks.pop(0)
        return initial_task

    def _compute_critical_path(self) -> list[Task]:
        """
        Walks the task-tree and adds  critical steps into a list.
        
        Returns:
            critical_path: list[Task] an ordered list of tasks that represent the critical path

        """
        critical_path: list[Task] = []

        depth: int = 0
        end = False
        while not end:
            for child in self.tasks.children:
                pass

        return critical_path

    def _update_start_dates(self, tasks: Task):
        def _get_latest_end_date(task: Task) -> datetime.date:
            latest = None
            for parent in task.parents:
                if latest is None:
                    latest = parent.end
                elif parent.end > latest:
                    latest = parent.end
            return latest

        if tasks.parents == []:
            tasks.start = self.start_date
        else:
            latest = _get_latest_end_date(tasks)
            tasks.start = latest

        for child in tasks.children:
            self._update_start_dates(child)
