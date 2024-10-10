from datetime import datetime
from PySide6.QtGui import QFont, QColor

import ganttmaker

# define file path to Excel sheet
testfile = 'example_data/project_a.xlsx'

# instatiate dataloader and load data
loader = ganttmaker.Dataloader(testfile)
loader.load()

# create figure object and set properties
figure = ganttmaker.Figure()

# set project start date
figure.start_date = datetime.fromisoformat('2024-08-01').date()

# set title and title properties
figure.title = 'Project A'
figure.title_font = QFont('Arial', 64)
figure.render_metrics.title_height = 64
figure.title_color = QColor(ganttmaker._colors[0])

# set axis properties
figure.axes_font = QFont('Arial', 24)
figure.axes_color = QColor(ganttmaker._colors[0])

# set box and background properties
figure.box_color = QColor(ganttmaker._colors[0])
figure.background_color = QColor('transparent')

# set legend properties
figure.legend_font = QFont('Arial', 32)
figure.legend_color = QColor(ganttmaker._colors[0])

# define canvas size and export file
figure.canvas_size = (2400, 1200)
figure.render_metrics.legend_width = 620
figure.export_file = 'example_data/project_a.png'

# draw and save figure
figure.draw(loader)

