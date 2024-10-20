# Gantt Diagram Maker

**Gantt Diagram Maker** is a python module that aims to make professional gantt charts from Microsoft Excel sheets.
This helps the user to visualize project structure and progress.

This repository is made for fun and was actually used to render diagrams in my studywork. 
Feel free to copy and/or improve but leave a star if you like it :-)

![Gantt Diagram](https://github.com/LS-KS/Gantt-Maker/blob/main/example_data/project_a.png)


There is also an editor for this diagram. Feel free to check it out: 
[Gantt Diagram Editor](https://github.com/LS-KS/Gantt-Maker/blob/main/gantt_editor.py)
It is not well tested and there is a bug that where old content is rendered to a new image despite reinstatiate everything. 
I'll promise to fix this as soon as I work on this project again.

# Dependencies

- Qt bindings PySide6 are used as the render backend which is the reason Qt classes are preferred datatypes.

- Pandas is used together with the package openpyxl to load excel sheets.
  
- openpyxl is used to read .xlsx files

- The underlying color palette is copied from https://www.learnui.design/tools/data-color-picker.html#palette. 

# Installation

To install the dependencies run the following commands:

```bash
 pip install PySide6
```

```bash
 pip install pandas
 ```

```bash
 pip install openpyxl
```

Download at least [ganntmaker.py](https://github.com/LS-KS/Gantt-Maker/blob/main/ganttmaker.py) in your project folder.

# Getting started

See example_usage.py to get an impression how to customize the diagram.

[example_usage.py](https://github.com/LS-KS/Gantt-Maker/blob/main/example_usage.py)

To start the editor, navigate into the directory of this repository and run the following command:

```bash
python gantt_editor.py
```

You may also execute gantt_editor.py in your favorite IDE.

## Excel sheet format
To make it actually work, your excel sheet must have the following columns:

- **Task**: A unique identifier for the task, will be treated as a **str**
- **Predecessor**: A set of **Task** identifiers, separated by a **semicolon**. This will be used to draw the arrows between the tasks.
- **Description**: A description of the task, will rendered next to the task identifier.
- **Plan-Start**: The planned start date of the task, will be treated as a **datetime**.
- **Plan-End**: The planned end date of the task, will be treated as a **datetime**.
- **Actual-Start**: The actual start date of the task, will be treated as a **datetime**.
- **Actual-End**: The actual end date of the task, will be treated as a **datetime**.

I uploaded an example excel sheet in the folder example_data:

[project_a.xlsx](https://github.com/LS-KS/Gantt-Maker/blob/main/example_data/project_a.xlsx)

## Import statements

Use the following command to import the module:

```python
import ganttmaker
```

To properly set the project start date it is helpful to use the following import statement:

```python
from datetime import datetime
```

If you want to adjust the style of the diagram, import Qt classes:

```python
from PySide6.QtGui import QFont, QColor
```

## Load the excel sheet

To load the excel sheet, the class **DataLoader** must be instantiated. the constructor needs a string that represents the path to the excel sheet.

```python
loader = ganttmaker.DataLoader("example_data/project_a.xlsx")
```

Everything else important is done in the **Figure** class. 

```python
fig = ganttmaker.Figure()
```
Check its properties to customize the diagram.
After that, call the method **draw** with the loader object as an argument.

```python
fig.draw(loader)
```

Feel free to contact me if there is a problem.

# Known issues

- I was actually too lazy to check for legend size. So the horizontal length of the legend must be adjusted manually

## Issues with the editor
- On MacOS Sequoia there is actual an issue with weird artefacts on the image after settings are changed. On Windows everything works fine.
- Not every property will trigger a redraw of the diagram.

# Contributing

Every Pull Request will be checked and accepted if I'll find it suitable.
