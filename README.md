# BOQ Visualizer

The BOQ Visualizer is a Dash-based Python web application that allows users to upload Excel files containing BOQ (Bill of Quantities) data and visualize selected numerical values in an interactive bar chart format. Users can filter, search, sort, and drill into details of specific items across multiple datasets.

---

## Features

- Upload and visualize one or more `.xlsx` files with BOQ data
- Choose value columns and categories to group or color bars
- Search for specific items by keyword
- Sort bars by value or keep the original order
- View charts page-by-page with adjustable bar count per page
- Click on any item to view a detailed breakdown across all uploaded files

---

## Input File Requirements

- Excel (`.xlsx`) format
- Sheet name must be **`Database BOQ`**
- Data must have a **`Description`** column (used for labeling)
- The columns after the first four are used for value/category selection
- Percentage columns (like "85%") are automatically parsed

---

## How to Run

### Install Dependencies

Make sure you have Python 3 installed, then install required libraries:

```bash
pip install dash dash-bootstrap-components pandas plotly openpyxl
