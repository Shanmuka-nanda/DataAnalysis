# Class Presentation Script: Data Analysis Platform

**Goal:** To confidently demonstrate your Data Analysis Platform application to the class, detailing the problem it solves, how it works, and the technical challenges you overcame.

----

## 🕒 1. The Hook (1 minute)
**What to show:** The Login/Register screen.

**What to say:**
> "Hi everyone, my name is [Your Name] and today I'm excited to present my project: **Data Analysis Platform**. 
>
> The problem I wanted to solve is that working with raw Excel or CSV files is often messy and intimidating for non-technical users. I wanted to build a clean, web-based tool where anyone can securely upload their messy data, clean it on the fly, and instantly generate interactive dashboards and PDF reports — all without writing a single line of code."

---

## 🕒 2. Authentication & Onboarding (1 minute)
**What to show:** Fill out the registration form with a new test account email and hit submit.

**What to say:**
> "Let's start from the beginning. Security and user-isolation are core to any data platform. I implemented a full authentication system using Django's backend. 
> 
> When a new user signs up, the system provisions an isolated workspace for them—meaning they can only see and edit their own data. *[Click Register]* 
>
> I've also integrated Django's SMTP backend. The moment I registered just now, the system fired off an automated welcome email to that email address to verify the account creation."

---

## 🕒 3. The Dashboard & Core Navigation (30 seconds)
**What to show:** The main Dashboard screen, moving your mouse over the sidebar links.

**What to say:**
> "Once logged in, the user lands on their Dashboard. This gives a top-level overview of their recent activity. 
>
> You can see I've built a modular navigation system on the left. The platform is broken down into four core micro-apps:
> 1. **Projects:** Where datasets are stored and managed.
> 2. **Analytics:** Where we track user usage and platform statistics.
> 3. **Data Cleaner:** To sanitize raw CSV/Excel files.
> 4. **Report Builder:** To dynamically generate charts."

---

## 🕒 4. Analytics: Tracking Usage (1 minute)
**What to show:** Click on the **Analytics** sidebar link. Show the progress bars and statistics.

**What to say:**
> "Before we look at the data processing, let's briefly look at the Analytics app. 
>
> As an administrator or user, it's important to track platform usage. I built this section to query the database and calculate real-time statistics—like the total number of projects created, files uploaded, and the percentage of limits reached. 
>
> This demonstrates how to use Django's ORM (Object-Relational Mapping) to dynamically calculate and visualize backend metrics on the frontend using Bootstrap progress bars."

---

## 🕒 5. The Data Cleaner: Real-time processing (2 minutes)
**What to show:** Click into the **Data Cleaner**. Drag and drop a messy CSV file into the drop zone. Show the dirty data preview.

**What to say:**
> "Let's look at the Data Cleaner. Often, real-world data has missing rows, blank spaces, or messy headers. 
> 
> I built this tool using Javascript (`PapaParse` and `SheetJS`) to parse data directly in the browser for maximum speed and security. 
>
> *[Show the checkboxes]* Here, the user can visually select cleaning parameters like removing nulls or trimming whitespace. When I hit 'Clean', the algorithm processes the array, drops the bad rows, shows the final stats, and immediately downloads a sanitized CSV ready for analysis."

---

## 🕒 6. The Magic: Report Builder & Plotly Charts (2 minutes)
**What to show:** Click on **Report Builder**. Click on an uploaded project to load the charts. Hover over the charts to show they are interactive.

**What to say:**
> "Now for the core feature: The Report Builder. 
> 
> Once a user uploads their cleaned data to a Project, they can click on it here. The backend analyzes the columns—detecting which are numbers and which are categories—and sends that metadata back to the frontend.
> 
> I used **Plotly.js** to dynamically render these charts. As you can see, they aren't static images—they are fully interactive. 
> 
> Furthermore, I built dynamic slicers. *[Select a dropdown filter]*. When I filter the data here, it recalculates the arrays and updates the entire dashboard instantly."

---

## 🕒 7. PDF Export (30 seconds)
**What to show:** Click the **Download PDF** button. Open the downloaded PDF.

**What to say:**
> "Finally, a great analysis is only useful if it can be shared. I implemented `html2pdf.js` to allow users to capture their customized dashboard state and instantly compile it into a professional, printable PDF report for their stakeholders."

---

## 🕒 8. Challenges & Conclusion (1 minute)
**What to show:** Leave the screen on the beautiful Report Builder dashboard.

**What to say:**
> "Building this wasn't without hurdles. 
> 
> One of the biggest challenges was dealing with Missing Data (`NaN` in Python). When sending data from the Pandas backend to the Javascript frontend, the JSON encoder would crash because JSON doesn't understand `NaN`. I had to build a sanitation layer to convert those to Python `None` types first.
>
> We also had to battle strict Django template syntax errors and CSRF token security issues. 
> 
> Ultimately, I'm really proud of this platform. It successfully bridges complex backend data processing with a clean, responsive front-end UI. 
>
> Thank you! Are there any questions?"
