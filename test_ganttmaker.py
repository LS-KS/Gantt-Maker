import datetime

import pytest
import ganttmaker
import pandas as pd

testfile = 'example_data/project_a.xlsx'
def test_instantiation():
    loader = ganttmaker.Dataloader(testfile)
    assert loader is not None
    drawer = ganttmaker.Figure()
    assert drawer is not None


def test_loading():
    loader = ganttmaker.Dataloader(testfile)
    loader.load()
    assert loader._data is not None

def test_start_date():
    drawer = ganttmaker.Figure()
    drawer.start_date = datetime.date(2021, 1, 1)
    assert drawer.start_date == datetime.date(2021, 1, 1)
    with pytest.raises(TypeError):
        drawer.start_date = '2021-01-01'
    drawer.start_date = pd.Timestamp('2021-01-01')
    assert drawer.start_date == datetime.date(2021, 1, 1)

def test_canvas_size():
    drawer = ganttmaker.Figure()
    drawer.canvas_size = (800, 600)
    assert drawer.canvas_size == (1066, 800)
    drawer.unit = 'px'
    drawer.canvas_size = (800, 600)
    assert drawer.canvas_size == (1066, 800)
    drawer.unit = 'pt'
    drawer.canvas_size = (800, 600)
    assert drawer.canvas_size == (800, 600)
    drawer.unit = 'mm'
    drawer.canvas_size = (800, 600)
    assert drawer.canvas_size == (2267, 1700)
    drawer.unit = 'cm'
    drawer.canvas_size = (800, 600)
    assert drawer.canvas_size == (22677, 17007)
    drawer.unit = 'in'
    drawer.canvas_size = (800, 600)
    assert drawer.canvas_size == (57600, 43200)
    with pytest.raises(ValueError):
        drawer.canvas_size = (800, 600, 400)
    with pytest.raises(TypeError):
        drawer.canvas_size = 800

def test_draw():
    loader = ganttmaker.Dataloader(testfile)
    loader.load()
    drawer = ganttmaker.Figure()
    drawer.start_date = pd.Timestamp('2024-07-01')
    drawer.canvas_size = (800, 600)
    drawer.draw(loader)

    # Loader loads testfile in Figure initialization
    loader = ganttmaker.Dataloader(testfile)
    drawer = ganttmaker.Figure()
    drawer.start_date = pd.Timestamp('2021-01-01')
    with pytest.raises(ValueError): # canvas_size not set
        drawer.draw(loader)

    loader = ganttmaker.Dataloader(testfile)
    loader.load()
    drawer = ganttmaker.Figure()
    drawer.canvas_size = (800, 600)
    with pytest.raises(ValueError): # start_date not set
        drawer.draw(loader)


def test_Task():
    task_1 = ganttmaker.Task(
        task_no = '1.0',
        start = pd.Timestamp('2021-01-01'),
        end= pd.Timestamp('2021-01-02'),
        description= "Do something",
        predecessor = "2.1;2.2;2.3")
    assert task_1 is not None

    task_2 = ganttmaker.Task(
        task_no = 'Task 2',
        start = pd.Timestamp('2021-01-02'),
        end = pd.Timestamp('2021-01-03'),
        description = "Do something else",
        predecessor = "3.1;3.2;3.3")
    assert task_2 is not None

    task_1.with_children(task_2)
    assert task_1.children == [task_2]
    assert task_1.parents == []
    assert task_2.children == []
    assert task_2.parents == [task_1]

    task_1.without_children(task_2)
    assert task_1.children == []
    assert task_2.parents == []
    assert task_2.children == []
    assert task_1.parents == []
