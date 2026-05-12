# Data Analysis Platform: End-to-End Presentation Notes

## 1. Project Overview & Architecture
This project is a functional **Data Analysis Platform** built with **Django (v5.2.11)**. The platform allows users to manage projects, upload datasets (CSV/Excel), clean data, generate reports, and analyze data. 

### Architecture Pattern:
- **Backend Framework:** Django (MVT Architecture - Model, View, Template).
- **Database:** SQLite (default Django database engine).
- **Data Processing:** Python's `pandas` and `numpy` libraries for handling tabular data constraints, dataset dimensions, and cleaning.
- **Frontend Interactivity:** HTML/CSS templates combined with Vanilla JavaScript interacting via asynchronous JSON APIs.

---

## 2. General Problem Solving Approach
For every module/problem in the system, we followed these core philosophies:
- **User Data Isolation:** Every piece of data (Projects, Activities) is tied strictly to the logged-in user through a `ForeignKey`. We use `@login_required` and `LoginRequiredMixin` systematically, and apply `.filter(user=request.user)` inside QuerySets to prevent cross-account data leakage.
- **Efficient File Handling:** Datasets are grabbed using Django's `FileField`. Upon successfully uploading, the backend immediately parses the files using `pandas` to obtain descriptive metadata (rows, columns, file sizes) natively and stores those counts in the database for fast retrieval later.
- **Asynchronous Processing (AJAX):** In highly interactive apps like the `Report_build`, we didn't want the user to refresh the page constantly. We solved this by using JavaScript `fetch` API on the frontend, which communicates with Django views returning `JsonResponse`. 

---

## 3. Libraries, Packages, and Imports

### A. Built-in Django Imports used across the system:
1. **Routing & Views:**
   - `from django.shortcuts import render, redirect, get_object_or_404`: Core functions to serve html templates, route users, and securely fetch database records (throws a 404 if data goes missing).
   - `from django.views.generic import ListView, CreateView, DetailView, DeleteView`: Class-Based Views (CBVs) used in the `projects` app to write less boilerplate code for CRUD (Create, Read, Update, Delete) operations.
   - `from django.http import JsonResponse, HttpResponseRedirect`: To return JSON payloads (used heavily in data fetching).
   
2. **Authentication & Security:**
   - `from django.contrib.auth import login, logout, authenticate`: To manage user sessions securely.
   - `from django.contrib.auth.decorators import login_required`: Applied to functions to block anonymous users.
   - `from django.contrib.auth.mixins import LoginRequiredMixin`: The CBV equivalent of `login_required`.

3. **Database Models:**
   - `from django.db import models`: To construct database tables. Uses `ForeignKey`, `CharField`, `FileField`, `DateTimeField`.

### B. Third-Party Packages (External):
1. **Pandas (`import pandas as pd`)**: 
   - **Problem it solves:** Reading `.csv` and `.xlsx` files that the user uploads. 
   - **Where is it used?** In `projects/views.py` (to calculate total dataset rows/columns) and `Report_build/views.py` (to extract samples and distinguish between categorical/numeric data columns).
2. **Numpy (`import numpy as np`)**:
   - **Problem it solves:** Dealing with missing data (`NaN`) efficiently during dataset transformations in pandas objects.

### C. Standard Python Libraries:
- **`import os`, `import json`, `from pathlib import Path`**: For path manipulation on disk and reading raw JSON strings from HTTP request bodies.

<br><br><br>

---
# DEEP DIVE: Application-by-Application Breakdown (With Code Examples)
---

### A. Accounts App (`accounts`)
**Purpose:** Handles User Authentication, Profiles, and Activity logging.

**The Problem:** We need to keep user data private and separate. We also have a single profile page that contains two different HTML forms (Profile Form and Activity Form).
**The Approach:** We use the `@login_required` decorator to restrict access. To handle multiple forms on one page, we check `request.POST` for the unique submit button name (`"profile_submit"` vs `"activity_submit"`) to know which one to process.

*Code Example (`accounts/views.py`):*
```python
from django.contrib.auth.decorators import login_required
from .models import Profile, Activity

@login_required # Prevents anonymous users from viewing this page
def profile_view(request):
    # Strictly fetch the profile associated with the logged-in user
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    if request.method == "POST":
        # Check which form was submitted by looking at the button name
        if "profile_submit" in request.POST:
            # Process Profile Update Form
            pass
        if "activity_submit" in request.POST:
            # Process Activity Logging Form
            pass
            
    return render(request, 'accounts/profile.html', {...})
```

---

### B. Dashboard App (`dashboard`)
**Purpose:** Central Landing Page summarizing user activity.

**The Problem:** The user needs a quick overview of their latest activities and projects without pulling too much data from the database, which would slow down the page.
**The Approach:** We use Django ORM's `.count()` to get quick totals without loading rows into memory. We use `.order_by('-date')[:5]` to strictly limit the query to the 5 most recent records.

*Code Example (`dashboard/views.py`):*
```python
@login_required
def dashboard_view(request):
    # Efficiently count total projects using the database engine
    total_projects = Project.objects.filter(user=request.user).count()
    
    # Only fetch the 4 most recently created projects (descending order)
    recent_projects = Project.objects.filter(user=request.user).order_by("-created_at")[:4]

    context = {
        'total_projects': total_projects,
        'recent_projects': recent_projects,
    }
    return render(request, 'dashboard.html', context)
```

---

### C. Projects App (`projects`)
**Purpose:** Allows users to create a project and securely upload datasets.

**The Problem:** When a user uploads a `.csv` or `.xlsx` file, we need to immediately know its metadata (file size, total rows, total columns) before the user even tries to generate reports. Doing this later would cause lag.
**The Approach:** We intercept the Django form submission right after validation inside our `CreateView`. We save the file to the disk momentarily, read the file path using `pandas`, calculate `len(df)` for rows, and then permanently save these stats to the model.

*Code Example (`projects/views.py`):*
```python
import pandas as pd
import os

class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    form_class = ProjectCreateForm

    def form_valid(self, form):
        project = form.save(commit=False)
        project.user = self.request.user # Bind to current user
        dataset = form.cleaned_data.get('dataset')
        
        if dataset:
            # Extract file extension to know if it's CSV or Excel
            ext = os.path.splitext(dataset.name)[1].lower()
            project.save() # Save once to put the file on disk
            
            # Read the file using Pandas to get metadata instantly
            try:
                if ext == '.csv':
                    df = pd.read_csv(project.dataset.path)
                    project.total_rows = len(df)
                    project.total_columns = len(df.columns)
            except Exception as e:
                pass # Silently ignore parsing errors
                
            project.save() # Save the updated metadata
            
        return super().form_valid(form)
        
```

---

### D. Report Builder App (`Report_build`)
**Purpose:** Turns the user's uploaded datasets into visual charts and interactive reports on the frontend.

**The Problem:** Loading a 100,000-row dataset statically into an HTML template will freeze the user's browser, and missing native values (`NaN`) break JavaScript JSON parsers.
**The Approach:** We built an API endpoint that reads the file via Pandas. To prevent freezing, we randomly sample the dataset down to 5,000 rows max. To prevent JSON errors, we use `.replace({np.nan: None})` to safely convert nulls. Lastly, we dynamically separate string columns from number columns so the frontend knows what charts to draw.

*Code Example (`Report_build/views.py`):*
```python
import pandas as pd
import numpy as np
from django.http import JsonResponse

@login_required
def get_report_data(request, project_id):
    project = get_object_or_404(Project, id=project_id, user=request.user)
    
    # Read the dataset path created earlier
    df = pd.read_csv(project.dataset.path)
        
    # FIX: Replace NaN with None so JSON serialization doesn't crash
    df = df.replace({np.nan: None})
    
    # Automatically categorize columns for the frontend charting library
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(exclude=[np.number]).columns.tolist()
    
    # CRITICAL: Prevent browser crashes by capping rows to 5000 max
    if len(df) > 5000:
        df = df.sample(n=5000, random_state=42)
        
    # Convert back to native python dictionary for HTTP sending
    data = df.to_dict(orient='records')
    
    return JsonResponse({
        'success': True,
        'data': data,
        'numeric_columns': numeric_cols,
        'categorical_columns': categorical_cols
    })
```

---

### E. Analytics App (`analytics`)
**Purpose:** Generates visual progress rings regarding user tier constraints (e.g., Disk Space Used).

**The Problem:** We need to accurately calculate how much Megabytes of data the user has uploaded across *all* their projects.
**The Approach:** We query all the user's projects, iterate through the `dataset.size` attribute (which returns bytes), sum it all up, and calculate the stroke-offset percentage mathematically to pass to an SVG HTML element.

*Code Example (`analytics/views.py`):*
```python
@login_required
def index(request):
    projects = Project.objects.filter(user=request.user)
    
    # Sum up the file sizes of all uploaded datasets
    total_bytes = 0
    for p in projects:
        if p.dataset and hasattr(p.dataset, 'size'):
            total_bytes += p.dataset.size
            
    # Convert Total Bytes to Megabytes
    total_mb = round(total_bytes / (1024 * 1024), 2)
    
    # Calculate percentage for a 200MB maximum quota ring
    quota_limit = 200
    quota_percentage = min(100, int((total_mb / quota_limit) * 100))
    
    # Math for the SVG circle dashoffset trick
    quota_dashoffset = 251.2 - (251.2 * (quota_percentage / 100.0))

    context = {
        'total_mb': total_mb,
        'quota_percentage': quota_percentage,
        'quota_dashoffset': round(quota_dashoffset, 2),
    }
    return render(request, 'analytics/index.html', context)
```

---

## 4. Challenges Faced & Solutions

**1. Django Template Syntax Errors & Strict Parsing**
* **Location:** `projects/templates/projects/project_list.html`
* **Challenge:** We encountered 500 Server Errors (`TemplateSyntaxError`) when trying to render dynamic charts. The error "default requires 2 arguments, 1 provided" occurred because of a single space inside a template variable filter.
* **Solution:** Django's template engine is extremely strict with spacing. We bypassed the flaky filter syntax entirely by using robust `{% if %}` blocks to safely inject fallback data for our JavaScript charts.
* **Code Example:**
  ```html
  <!-- BAD: Crashes the server due to the space after 'default:' -->
  const chartLabels = {{ storage_chart_labels|default: '["Jan"]' | safe }};

  <!-- GOOD: Foolproof approach using standard tags -->
  const chartLabels = {% if storage_chart_labels %}{{ storage_chart_labels|safe }}{% else %}["Jan"]{% endif %};
  ```

**2. CSRF Verification Failures on Forms**
* **Location:** `accounts/templates/accounts/login.html` & `my_project/settings.py`
* **Challenge:** During authentication development, users frequently received a 403 Forbidden "CSRF verification failed" error when submitting the login or registration forms.
* **Solution:** Django has built-in Cross-Site Request Forgery protection. We had to ensure every `POST` form included the `{% csrf_token %}` tag and that our local development host was trusted in the settings.
* **Code Example:**
  ```html
  <!-- BAD: Form submission will be rejected by Django -->
  <form method="POST" action="{% url 'accounts:login' %}">
      <input type="email" name="email">
      <button type="submit">Login</button>
  </form>

  <!-- GOOD: Form submission is securely accepted -->
  <form method="POST" action="{% url 'accounts:login' %}">
      {% csrf_token %}
      <input type="email" name="email">
      <button type="submit">Login</button>
  </form>
  ```

**3. JSON Serialization Crashes with Pandas Data**
* **Location:** `Report_build/views.py`
* **Challenge:** When attempting to send the user's uploaded dataset to the frontend for charting, the Python `json` encoder crashed with a `ValueError: Out of range float values are not JSON compliant`. This happened because real-world datasets have missing data (parsed as `NaN` by Pandas).
* **Solution:** JavaScript JSON parsers do not understand `NaN`. Before converting the Pandas DataFrame to a dictionary, we had to systematically replace all `np.nan` values with Python's `None` (which correctly translates to JSON `null`).
* **Code Example:**
  ```python
  import pandas as pd
  import numpy as np

  df = pd.read_csv("dataset.csv")

  # BAD: This dict still contains NaN and will crash JsonResponse
  data = df.to_dict(orient='records') 
  
  # GOOD: Safely replaces NaN with None before conversion
  df = df.replace({np.nan: None})
  data = df.to_dict(orient='records')
  return JsonResponse({'data': data})
  ```

**4. ModuleNotFoundError & Configuration Mismatches**
* **Location:** `my_project/settings.py` & `my_project/urls.py`
* **Challenge:** As the project grew and new apps were separated (like `Data_clean` and `Report_build`), the development server would sometimes crash with `ModuleNotFoundError` preventing boot.
* **Solution:** Django app registration is highly case-sensitive. We had to carefully audit `INSTALLED_APPS` to ensure the capitalization exactly matched the physical folder names on the OS.
* **Code Example:**
  ```python
  # settings.py
  INSTALLED_APPS = [
      ...
      # BAD: Throws ModuleNotFoundError if the folder is actually 'Report_build'
      'report_build', 
      
      # GOOD: Exact match to the folder syntax
      'Report_build', 
  ]
  ```

---

## 5. Potential Questions to Prepare For

**Q: How do you handle security for users?**
*A: By utilizing Django's native session middleware and the `login_required` decorators. Every database query that fetches user-generated content strictly filters by `user=request.user` to ensure no cross-account data leaks.*

**Q: Why use Pandas instead of writing custom CSV readers?**
*A: Pandas is the industry standard for data manipulation in python. It allows us to efficiently read both CSV and Excel files, automatically identify column data types, filter thousands of rows simultaneously, and handle missing (Null) values effortlessly.*

**Q: Why use JSON Responses in some views instead of standard `render()` redirects?**
*A: To improve UX. For the Report Generation, we didn't want the user's webpage to hard refresh every time they hit "generate" or switched a chart. Fetching JSON asynchronously makes the Data Analysis Platform feel like a Single Page Application (SPA).*
