# Gannt Diagram Maker

This python module aims to make a gannt diagram from an Microsoft Excel sheet to visualize project planning. 
At this point column names of the excel sheet must match those from the example. 

This repository is made for fun and was actually used to render diagrams in my studywork. 
Feel free to copy and/or improve. 
Every Pull Request will be checked and accepted if I'll find it suitable.

# Dependencies

Qt bindings PySide6 are used as the render backend which is the reason Qt classes are preferred datatypes. 

Pandas is used together with the package openpyxl to load excel sheets. 

The underlying color palette is copied by https://www.learnui.design/tools/data-color-picker.html#palette. 

# Known issues

- When changing the fontsize the property defining the underlying rectangle must be adjusted manually. If it doesn't match, the text will either be clipped or too much space may be used.
- I was actually too lazy to check for legend size. So the horizontal length of the legend must be adjusted manually

# Usage

--> See example_usage.py
