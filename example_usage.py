from datetime import datetime
from PySide6.QtGui import QFont
import ganttmaker

testfile = 'example_data/project_a.xlsx'

loader = ganttmaker.Dataloader(testfile)
loader.load()

figure = ganttmaker.Figure()
figure.start_date = datetime.fromisoformat('2024-08-01').date()
figure.title = 'Project A'
figure.title_font = QFont('Arial', 16)
figure.canvas_size = (600, 300)
figure.render_metrics.legend_width = 35
figure.render_metrics.title_height = 30
figure.export_file = 'example_data/project_a.png'
figure.draw(loader)

