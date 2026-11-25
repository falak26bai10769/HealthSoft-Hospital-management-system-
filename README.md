# HEALTH-SOFT Smart Hospital Management System

A bilingual (English / Hindi) command-line hospital management system built with **Python** and **MySQL**. It supports separate staff and patient logins and covers day-to-day hospital operations, from registration and appointments to billing and payroll.

## Features

- **Authentication** – Staff and patient login with SHA-256 hashed passwords, plus on-the-spot registration
- **Patients** – Registration, search, update, delete, and full medical history
- **Appointments** – Booking, rescheduling, and cancellation
- **Clinical** – Prescriptions, surgeries, patient vitals, lab tests and results
- **Admissions** – OPD and ICU admit / discharge
- **Billing** – Itemised bills (surgery, medicines, lab, room charges) with insurance claims
- **Administration** – Departments, staff, beds, attendance, and salary generation
- **Inventory** – Pharmacy stock, blood bank, canteen sales
- **Emergency** – Emergency ICU admission and ambulance dispatch
- **Feedback** – Doctor and hospital ratings (1–5)
- **Symptom chatbot** – Basic symptom advice and quick access to appointments, vitals, bills, and lab tests
- **Reports** – Hospital summary and daily summary

## Requirements

- Python 3.8+
- MySQL Server 8.0+
- [`mysql-connector-python`](https://pypi.org/project/mysql-connector-python/)

## Setup

1. **Clone the repository**

   ```bash
   git clone <your-repo-url>
   cd <your-repo-folder>
   ```

2. **Install the dependency**

   ```bash
   pip install mysql-connector-python
   ```

3. **Create the database** – run the schema file in MySQL (rename `hospital_management_project.txt` to `.sql` if you prefer):

   ```bash
   mysql -u root -p < hospital_management_project.txt
   ```

4. **Configure the connection** – edit the `db()` function in `Hospital_management_project.py`:

   ```python
   mysql.connector.connect(
       host="localhost",
       user="root",
       password="your_password",
       database="hospital"
   )
   ```

5. **Run the application**

   ```bash
   python Hospital_management_project.py
   ```

   Choose a language at the prompt (`E` for English, `H` for Hindi), then log in or register.

## Usage

| Role    | Access |
|---------|--------|
| Staff   | Administration, doctor tools, billing, pharmacy, canteen, emergency, blood bank, feedback, search |
| Patient | Book appointments, view vitals / bills / history, book lab tests, chatbot, feedback |

New users who aren't found at login are offered registration as a patient or staff member. Before registering staff, make sure at least one department exists (the app will prompt you to add one).

## Database Schema

The schema (`hospital_management_project.txt`) defines these tables:

`departments`, `patients`, `staff`, `attendance`, `appointments`, `opd_records`, `icu_records`, `lab_tests`, `patient_lab_results`, `surgeries`, `prescriptions`, `bills`, `insurance_claims`, `patient_vitals`, `pharmacy`, `blood_bank`, `canteen`, `feedback`, `beds`, `salaries`

## Configuration Notes

- **Salary rates** are defined by role in the `SALARY_RATES` dictionary, with a 10% attendance-based bonus (`BONUS_RATE`).
- **Billing rates** (surgery ₹5,000 each, OPD ₹1,000/day, ICU ₹5,000/day) are set inside `generate_bill()`.
- Doctors and lab technicians are identified by the staff roles `Doctor` and `Technician`.

## Project Structure

```
├── Hospital_management_project.py       # Main application
└── hospital_management_project.txt      # MySQL schema
```
