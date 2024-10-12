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

# define canvas size and export file
figure.canvas_size = (2400, 1200)
figure.render_metrics.legend_width = 620
figure.export_file = 'example_data/project_a.png'

# set title and title properties
figure.title_properties.text = 'Project A'
figure.title_properties.line_color = QColor(ganttmaker._colors[0])
figure.title_properties.font = QFont('Arial', 64)

# draw and save figure
figure.draw(loader)

