# Data Analysis Platform (Django)

## Overview

This project is a **web-based Data Analysis Platform** built with **Django (v5.2)**.
It allows users to upload datasets (CSV/Excel), clean and analyze data, and generate interactive reports through a user-friendly interface.

The system focuses on **efficient dataset processing, secure user data isolation, and dynamic report generation**.

---

## Architecture

**Backend Framework**

* Django (MVT Architecture)

**Database**

* SQLite (default Django database)

**Data Processing**

* Pandas
* NumPy

**Frontend**

* HTML
* CSS
* JavaScript (AJAX / Fetch API)

---

## Core Features

### Project Management

* Create and manage projects
* Upload datasets (CSV / Excel)
* Automatic dataset metadata extraction:

  * Row count
  * Column count
  * File size

### Data Cleaning

* Detect missing values
* Process tabular datasets using Pandas
* Prepare datasets for analysis

### Report Generation

* Automatic column detection:

  * Numeric columns
  * Categorical columns
* Dynamic report generation
* JSON-based data APIs for frontend charts

### Dashboard & Analytics

* Overview of projects
* Recent project tracking
* Storage usage visualization

---

## Key Technical Concepts

### User Data Isolation

All project data is tied to the logged-in user using Django ForeignKey relationships.

Security mechanisms:

* `@login_required`
* `LoginRequiredMixin`
* Query filtering with `user=request.user`

---

### Efficient Dataset Processing

Datasets are processed immediately after upload using **Pandas**.

Example:

```python
df = pd.read_csv(project.dataset.path)
project.total_rows = len(df)
project.total_columns = len(df.columns)
```

This allows quick metadata retrieval without repeatedly loading large files.

---

### Asynchronous Data Loading

Interactive reports use **AJAX (Fetch API)** to request data from Django views.

Example:

```python
return JsonResponse({
    "success": True,
    "data": data,
    "numeric_columns": numeric_cols,
    "categorical_columns": categorical_cols
})
```

This prevents page reloads and improves user experience.

---

### Large Dataset Handling

To prevent browser crashes, datasets are sampled:

```python
if len(df) > 5000:
    df = df.sample(n=5000, random_state=42)
```

---

## Technology Stack

Backend

* Python
* Django

Data Processing

* Pandas
* NumPy

Frontend

* HTML
* CSS
* JavaScript

Database

* SQLite

---

## Challenges & Solutions

### Template Syntax Errors

Django template filters are strict with spacing.

Solution:

```html
{% if storage_chart_labels %}
{{ storage_chart_labels|safe }}
{% else %}
["Jan"]
{% endif %}
```

---

### CSRF Verification Failures

Every POST form must include:

```html
{% csrf_token %}
```

---

### JSON Serialization Issues

Pandas `NaN` values cause JSON errors.

Solution:

```python
df = df.replace({np.nan: None})
```

---

### Django App Configuration Errors

Django apps are **case sensitive** in `INSTALLED_APPS`.

Correct example:

```python
INSTALLED_APPS = [
    "Report_build",
]
```

---

## Installation

Clone the repository:

```bash
git clone https://github.com/your-username/data-analysis-platform.git
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Apply migrations:

```bash
python manage.py migrate
```

Run the development server:

```bash
python manage.py runserver
```

Open in browser:

```
http://127.0.0.1:8000
```

---

## Future Improvements

* PostgreSQL database support
* Advanced data visualization
* Machine learning integration
* Cloud storage for datasets

---

## Author

**Shanmukha Nanda Reddy**

Django Developer | Data Analysis Enthusiast

