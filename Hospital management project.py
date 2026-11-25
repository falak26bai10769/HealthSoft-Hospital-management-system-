import mysql.connector
from datetime import datetime
import hashlib

# =====================================================
# DATABASE CONNECTION
# =====================================================
def db():
    try:
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="admin",
            database="hospital"
        )
    except mysql.connector.Error as e:
        print(f"Database connection failed: {e}")
        return None

# =====================================================
# LANGUAGE SELECTION & TRANSLATION SUPPORT
# =====================================================
lang = input("Choose Language / भाषा चुनें (ENGLISH(E)/HINDI(H)): ").upper()
def T(en, hi):
    return en if lang == "E" else hi
print(T("Hello", "नमस्ते"))

# =====================================================
# UTILITIES
# =====================================================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()
def _validate_input(value, type_func, min_val=None, max_val=None):
    """Helper for input validation."""
    try:
        val = type_func(value)
        if min_val is not None and val < min_val:
            raise ValueError("Value too small.")
        if max_val is not None and val > max_val:
            raise ValueError("Value too large.")
        return val
    except (ValueError, TypeError):
        raise ValueError("Invalid input.")

# =====================================================
# USER AUTHENTICATION
# =====================================================
def login():
    con = db()
    if con is None:
        return None, None  # Return role and user_id
    cur = con.cursor()
    try:
        username = input(T("Enter username: ", "उपयोगकर्ता नाम दर्ज करें: "))
        password = input(T("Enter password: ", "पासवर्ड दर्ज करें: "))
        hashed_pass = hash_password(password)
        
        # Check staff table first
        cur.execute("SELECT staff_id FROM staff WHERE username=%s AND password_hash=%s", (username, hashed_pass))
        staff_result = cur.fetchone()
        if staff_result:
            print(T("Login successful as Staff.", "स्टाफ के रूप में लॉगिन सफल।"))
            return 'staff', staff_result[0]  # role, user_id
        
        # Check patients table
        cur.execute("SELECT patient_id FROM patients WHERE username=%s AND password_hash=%s", (username, hashed_pass))
        patient_result = cur.fetchone()
        if patient_result:
            print(T("Login successful as Patient.", "रोगी के रूप में लॉगिन सफल।"))
            return 'patient', patient_result[0]  # role, user_id
        
        # Not found, offer to register
        print(T("User not found. Would you like to register? (Y/N): ", "उपयोगकर्ता नहीं मिला। क्या आप पंजीकरण करना चाहेंगे? (Y/N): "))
        register_choice = input().upper()
        if register_choice == "Y":
            reg_role = input(T("Register as Patient or Staff? (P/S): ", "रोगी या स्टाफ के रूप में पंजीकरण करें? (P/S): ")).upper()
            if reg_role == "P":
                # Register as patient
                name = input(T("Enter your name: ", "अपना नाम दर्ज करें: "))
                age = input(T("Age: ", "आयु: "))
                gender = input(T("Gender: ", "लिंग: "))
                contact_no = input(T("Contact: ", "संपर्क: "))
                insurance = input(T("Insurance Company: ", "बीमा कंपनी: "))
                try:
                    age = int(age)
                except ValueError:
                    print(T("Invalid age. Setting to 0.", "अमान्य आयु। 0 पर सेट किया गया।"))
                    age = 0
                cur.execute("INSERT INTO patients(name, age, gender, contact_no, insurance, username, password_hash) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                            (name, age, gender.upper(), contact_no, insurance, username, hashed_pass))
                con.commit()
                cur.execute("SELECT LAST_INSERT_ID()")
                new_pid = cur.fetchone()[0]
                print(T("Patient registered. Your Patient ID is: ", "रोगी पंजीकृत। आपका रोगी आईडी है: ") + str(new_pid))
                return 'patient', new_pid
            elif reg_role == "S":
                # Register as staff
                name = input(T("Enter your name: ", "अपना नाम दर्ज करें: "))
                role = input(T("Role (e.g., Doctor, Nurse): ", "भूमिका (जैसे, डॉक्टर, नर्स): "))
                
                # Check for departments
                cur.execute("SELECT dept_id, name FROM departments")
                departments = cur.fetchall()
                if not departments:
                    print(T("No departments available. Would you like to add a new department? (Y/N): ", "कोई विभाग उपलब्ध नहीं। क्या आप एक नया विभाग जोड़ना चाहेंगे? (Y/N): "))
                    add_dept_choice = input().upper()
                    if add_dept_choice == "Y":
                        while True:
                            dept_name = input(T("Enter new department name: ", "नए विभाग का नाम दर्ज करें: ")).strip()
                            if not dept_name:
                                print(T("Department name cannot be empty. Please try again.", "विभाग का नाम खाली नहीं हो सकता। पुनः प्रयास करें।"))
                                continue
                            if len(dept_name) > 100:  # Arbitrary limit; adjust as needed
                                print(T("Department name too long. Please try again.", "विभाग का नाम बहुत लंबा है। पुनः प्रयास करें।"))
                                continue
                            # Check if department name already exists (case-insensitive)
                            cur.execute("SELECT 1 FROM departments WHERE LOWER(name) = LOWER(%s)", (dept_name,))
                            if cur.fetchone():
                                print(T("Department name already exists. Please choose a different name.", "विभाग का नाम पहले से मौजूद है। कृपया एक अलग नाम चुनें।"))
                                continue
                            break
                        # Insert new department
                        cur.execute("INSERT INTO departments(name) VALUES (%s)", (dept_name,))
                        con.commit()
                        cur.execute("SELECT LAST_INSERT_ID()")
                        did = cur.fetchone()[0]
                        print(T(f"Department '{dept_name}' added successfully with ID {did}.", f"विभाग '{dept_name}' सफलतापूर्वक जोड़ा गया, आईडी {did} के साथ।"))
                    else:
                        print(T("Cannot register staff without a department. Registration canceled.", "विभाग के बिना स्टाफ पंजीकरण नहीं किया जा सकता। पंजीकरण रद्द किया गया।"))
                        return None, None
                else:
                    # Departments exist; proceed to select one
                    for dept in departments:
                        print(f"{dept[0]}: {dept[1]}")
                    while True:
                        try:
                            did = int(input(T("Select Department ID: ", "विभाग आईडी चुनें: ")))
                            cur.execute("SELECT 1 FROM departments WHERE dept_id = %s", (did,))
                            if cur.fetchone() is None:
                                print(T("Invalid Department ID. Please try again.", "अमान्य विभाग आईडी। पुनः प्रयास करें।"))
                                continue
                            break
                        except ValueError:
                            print(T("Please enter a valid number.", "कृपया एक मान्य संख्या दर्ज करें।"))
                
                # Now register the staff with the selected/added department ID
                cur.execute("INSERT INTO staff(name, role, department_id, username, password_hash) VALUES(%s, %s, %s, %s, %s)", (name, role, did, username, hashed_pass))
                con.commit()
                cur.execute("SELECT LAST_INSERT_ID()")
                new_sid = cur.fetchone()[0]
                print(T("Staff registered. Your Staff ID is: ", "स्टाफ पंजीकृत। आपका स्टाफ आईडी है: ") + str(new_sid))
                return 'staff', new_sid
            else:
                print(T("Invalid choice. Registration canceled.", "अमान्य विकल्प। पंजीकरण रद्द किया गया।"))
                return None, None
        else:
            print(T("Registration declined. Exiting.", "पंजीकरण अस्वीकार किया गया। बाहर निकल रहे हैं।"))
            return None, None
    
    except mysql.connector.Error as e:
        print(f"Database error: {e}")
        con.rollback()
        return None, None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None, None
    finally:
        con.close()

# =====================================================
# ATTENDANCE MANAGEMENT
# =====================================================
def attendance():
    con = db()
    if con is None:
        return
    cur = con.cursor()
    try:
        cur.execute("SELECT staff_id,name FROM staff")
        for s in cur.fetchall():
            print(f"{s[0]}: {s[1]}")
        sid = int(input(T("Enter Staff ID: ", "कर्मचारी आईडी दर्ज करें: ")))
        status = input(T("Status (P/A): ", "स्थिति (P/A): ")).upper()
        cur.execute("INSERT INTO attendance(staff_id,date,status) VALUES(%s,%s,%s)", (sid, datetime.now().date(), status))
        con.commit()
        print(T("Attendance recorded", "हाजिरी दर्ज"))
    except ValueError:
        print(T("Invalid input. Please enter a valid number for Staff ID.", "अमान्य इनपुट। कृपया स्टाफ आईडी के लिए एक मान्य संख्या दर्ज करें।"))
    except mysql.connector.Error as e:
        print(f"Database error: {e}")
        con.rollback()
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        con.close()

# =====================================================
# STAFF MANAGEMENT
# =====================================================
def manage_staff():
    con = db()
    if con is None:
        return
    cur = con.cursor()

    while True:
        print("\n---", T("Staff Management", "स्टाफ प्रबंधन"), "---")
        print("1.", T("View Staff", "स्टाफ देखें"))
        print("2.", T("Add Staff", "स्टाफ जोड़ें"))
        print("3.", T("Update Staff", "स्टाफ अपडेट करें"))
        print("4.", T("Delete Staff", "स्टाफ हटाएं"))
        print("5.", T("Back to Main Menu", "मुख्य मेनू पर लौटें"))

        choice = input(T("Enter choice: ", "विकल्प दर्ज करें: "))

        try:
            if choice == "1":
                cur.execute("""
                           SELECT s.staff_id, s.name, s.role, d.name AS department_name
                           FROM staff s
                           LEFT JOIN departments d ON s.department_id = d.dept_id
                        """)
                rows = cur.fetchall()
                for s in rows:
                    print(f"ID: {s[0]}| Name: {s[1]}| Role: {s[2]}| Department: {s[3] if s[3] else 'N/A'}")

            elif choice == "2":
                name = input(T("Name: ", "नाम: "))
                role = input(T("Role: ", "भूमिका: "))
                cur.execute("SELECT dept_id, name FROM departments")
                departments = cur.fetchall()
                if not departments:
                    print(T("No departments available. Please add departments first.", "कोई विभाग उपलब्ध नहीं। कृपया पहले विभाग जोड़ें।"))
                    return

                for dept in departments:
                    print(f"{dept[0]}: {dept[1]}")

                while True:
                    try:
                        did = int(input(T("Department ID: ", "विभाग आईडी: ")))
                        cur.execute("SELECT 1 FROM departments WHERE dept_id = %s", (did,))
                        if cur.fetchone() is None:
                            print(T("Invalid Department ID. Please try again.", "अमान्य विभाग आईडी। पुनः प्रयास करें।"))
                            continue
                        break
                    except ValueError:
                        print(T("Please enter a valid number.", "कृपया एक मान्य संख्या दर्ज करें।"))
                cur.execute("INSERT INTO staff(name, role, department_id) VALUES(%s, %s, %s)", (name, role, did))
                con.commit()

            elif choice == "3":
                sid = int(input(T("Enter Staff ID to update: ", "अपडेट करने के लिए स्टाफ आईडी दर्ज करें: ")))
                name = input(T("New Name: ", "नया नाम: "))
                role = input(T("New Role: ", "नई भूमिका: "))
                cur.execute("UPDATE staff SET name=%s, role=%s WHERE staff_id=%s", (name, role, sid))
                con.commit()
                print(T("Staff updated.", "स्टाफ अपडेट किया गया।"))

            elif choice == "4":
                sid = int(input(T("Enter Staff ID to delete: ", "हटाने के लिए स्टाफ आईडी दर्ज करें: ")))
                cur.execute("DELETE FROM staff WHERE staff_id=%s", (sid,))
                con.commit()
                print(T("Staff deleted.", "स्टाफ हटाया गया।"))

            elif choice == "5":
                break
            else:
                print(T("Invalid choice.", "गलत विकल्प।"))
        except ValueError:
            print(T("Invalid input. Please enter valid data.", "अमान्य इनपुट। कृपया मान्य डेटा दर्ज करें।"))
        except mysql.connector.Error as e:
            print(f"Database error: {e}")
            con.rollback()
        except Exception as e:
            print(f"Unexpected error: {e}")

    con.close()

def search_staff():
    con = db()
    if con is None:
        return
    cur = con.cursor()
    try:
        keyword = input(T("Enter Staff Name or ID: ", "कर्मचारी का नाम या आईडी दर्ज करें: ")).strip()

        if keyword.isdigit():
            cur.execute("SELECT staff_id, name, role, department_id FROM staff WHERE staff_id = %s", (int(keyword),))
        else:
            cur.execute("SELECT staff_id, name, role, department_id FROM staff WHERE name LIKE %s", ('%' + keyword + '%',))

        results = cur.fetchall()
        if results:
            print(T(f"\nFound {len(results)} staff member(s):", f"\n{len(results)} कर्मचारी पाए गए:"))
            for staff in results:
                cur.execute("SELECT name FROM departments WHERE dept_id=%s", (staff[3],))
                dept = cur.fetchone()
                dept_name = dept[0] if dept else T("N/A", "उपलब्ध नहीं")
                print(f"ID: {staff[0]}| Name: {staff[1]}| Role: {staff[2]}| Department: {dept_name}")
        else:
            print(T("No matching staff found.", "कोई मेल खाता कर्मचारी नहीं मिला।"))
    except mysql.connector.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        con.close()

# =====================================================
# DEPARTMENTS & DOCTORS MANAGEMENT
# =====================================================
def manage_departments_full():
    con = db()
    if con is None:
        return
    cur = con.cursor()

    while True:
        print("\n---", T("Department Management", "विभाग प्रबंधन"), "---")
        print("1.", T("View Departments", "विभाग देखें"))
        print("2.", T("Add Department", "विभाग जोड़ें"))
        print("3.", T("Update Department", "विभाग अपडेट करें"))
        print("4.", T("Delete Department", "विभाग हटाएं"))
        print("5.", T("Back to Main Menu", "मुख्य मेनू पर लौटें"))

        choice = input(T("Enter choice: ", "विकल्प दर्ज करें: "))

        try:
            if choice == "1":
                cur.execute("SELECT * FROM departments")
                rows = cur.fetchall()
                if not rows:
                    print(T("No departments found.", "कोई विभाग नहीं मिला।"))
                for d in rows:
                    print(f"ID: {d[0]}| Name: {d[1]}")

            elif choice == "2":
                name = input(T("Enter Department Name: ", "विभाग का नाम दर्ज करें: "))
                cur.execute("INSERT INTO departments(name) VALUES(%s)", (name,))
                con.commit()
                print(T("Department added.", "विभाग जोड़ा गया।"))

            elif choice == "3":
                cur.execute("SELECT * FROM departments")
                for d in cur.fetchall():
                    print(f"{d[0]}: {d[1]}")
                did = int(input(T("Enter Department ID to update: ", "अपडेट करने के लिए विभाग आईडी दर्ज करें: ")))
                new_name = input(T("Enter new name: ", "नया नाम दर्ज करें: "))
                cur.execute("UPDATE departments SET name=%s WHERE dept_id=%s", (new_name, did))
                con.commit()
                print(T("Department updated.", "विभाग अपडेट किया गया।"))

            elif choice == "4":
                did = int(input(T("Enter Department ID to delete: ", "हटाने के लिए विभाग आईडी दर्ज करें: ")))
                cur.execute("DELETE FROM departments WHERE dept_id=%s", (did,))
                con.commit()
                print(T("Department deleted.", "विभाग हटाया गया।"))

            elif choice == "5":
                break
            else:
                print(T("Invalid choice.", "गलत विकल्प।"))
        except ValueError:
            print(T("Invalid input. Please enter valid data.", "अमान्य इनपुट। कृपया मान्य डेटा दर्ज करें।"))
        except mysql.connector.Error as e:
            print(f"Database error: {e}")
            con.rollback()
        except Exception as e:
            print(f"Unexpected error: {e}")

    con.close()

# =====================================================
# BEDS MANAGEMENT
# =====================================================
def manage_beds():
    con = db()
    if con is None:
        return
    cur = con.cursor()

    while True:
        print("\n---", T("Beds Management", "बिस्तर प्रबंधन"), "---")
        print("1.", T("View Beds", "बिस्तर देखें"))
        print("2.", T("Add Bed Type", "बिस्तर प्रकार जोड़ें"))
        print("3.", T("Update Bed Type", "बिस्तर प्रकार अपडेट करें"))
        print("4.", T("Delete Bed Type", "बिस्तर प्रकार हटाएं"))
        print("5.", T("Back to Main Menu", "मुख्य मेनू पर लौटें"))

        choice = input(T("Enter choice: ", "विकल्प दर्ज करें: "))

        try:
            if choice == "1":
                cur.execute("SELECT * FROM beds")
                rows = cur.fetchall()
                if not rows:
                    print(T("No beds found.", "कोई बिस्तर नहीं मिला।"))
                for b in rows:
                    print(f"ID: {b[0]}| Type: {b[1]}| Total Count: {b[2]}")

            elif choice == "2":
                bed_type = input(T("Bed Type (e.g., ICU, General): ", "बिस्तर प्रकार (जैसे, ICU, सामान्य): "))
                try:
                    total_count = int(input(T("Total Count: ", "कुल संख्या: ")))
                except ValueError:
                    print(T("Invalid count. Please enter a number.", "अमान्य संख्या। कृपया एक संख्या दर्ज करें।"))
                    continue
                cur.execute("INSERT INTO beds(type, total_count) VALUES(%s, %s)", (bed_type, total_count))
                con.commit()
                print(T("Bed type added.", "बिस्तर प्रकार जोड़ा गया।"))

            elif choice == "3":
                cur.execute("SELECT * FROM beds")
                for b in cur.fetchall():
                    print(f"{b[0]}: {b[1]} | Count: {b[2]}")
                try:
                    bid = int(input(T("Enter Bed ID to update: ", "अपडेट करने के लिए बिस्तर आईडी दर्ज करें: ")))
                except ValueError:
                    print(T("Invalid Bed ID. Please enter a number.", "अमान्य बिस्तर आईडी। कृपया एक संख्या दर्ज करें।"))
                    continue
                new_type = input(T("New Bed Type: ", "नया बिस्तर प्रकार: "))
                try:
                    new_count = int(input(T("New Total Count: ", "नई कुल संख्या: ")))
                except ValueError:
                    print(T("Invalid count. Please enter a number.", "अमान्य संख्या। कृपया एक संख्या दर्ज करें।"))
                    continue
                cur.execute("UPDATE beds SET type=%s, total_count=%s WHERE bed_id=%s", (new_type, new_count, bid))
                con.commit()
                print(T("Bed type updated.", "बिस्तर प्रकार अपडेट किया गया।"))

            elif choice == "4":
                try:
                    bid = int(input(T("Enter Bed ID to delete: ", "हटाने के लिए बिस्तर आईडी दर्ज करें: ")))
                except ValueError:
                    print(T("Invalid Bed ID. Please enter a number.", "अमान्य बिस्तर आईडी। कृपया एक संख्या दर्ज करें।"))
                    continue
                cur.execute("DELETE FROM beds WHERE bed_id=%s", (bid,))
                con.commit()
                print(T("Bed type deleted.", "बिस्तर प्रकार हटाया गया।"))

            elif choice == "5":
                break
            else:
                print(T("Invalid choice.", "गलत विकल्प।"))
        except ValueError:
            print(T("Invalid input. Please enter valid data.", "अमान्य इनपुट। कृपया मान्य डेटा दर्ज करें।"))
        except mysql.connector.Error as e:
            print(f"Database error: {e}")
            con.rollback()
        except Exception as e:
            print(f"Unexpected error: {e}")

    con.close()

# =====================================================
# SALARY GENERATOR
# =====================================================

SALARY_RATES = {
    'MANAGER': 50000.00,  
    'DEVELOPER': 40000.00,  
    'INTERN': 15000.00,  
    'DOCTOR': 80000.00,
    'ADMIN': 30000.00,
    'TECHNICAL': 45000.00,
    
}
BONUS_RATE = 0.10  

def generate_salary():
    """
    Generates monthly salaries for staff based on role, base salary, and attendance.
    Can generate for a specific staff or all staff for a given month.
    Inserts into the 'salaries' table with month as VARCHAR(7) (e.g., '2023-10').
    """
    con = db()
    if con is None:
        return
    cur = con.cursor()
    try:
        # Get month input (validate format)
        month_str = input(T("Enter month (YYYY-MM): ", "माह दर्ज करें (YYYY-MM): ")).strip()
        try:
            # Validate and format to YYYY-MM
            month = datetime.strptime(month_str, '%Y-%m').strftime('%Y-%m')
        except ValueError:
            raise ValueError("Invalid month format. Use YYYY-MM (e.g., 2023-10).")
        
        # Option to generate for specific staff or all
        choice = input(T("Generate for (1) Specific Staff or (2) All Staff: ", "के लिए जनरेट करें (1) विशिष्ट स्टाफ या (2) सभी स्टाफ: ")).strip()
        if choice == "1":
            cur.execute("SELECT staff_id, name FROM staff")
            all_staff = cur.fetchall()
            if not all_staff:
                print(T("No staff found in the database.", "डेटाबेस में कोई स्टाफ नहीं मिला।"))
                return
            print(T("Available Staff:", "उपलब्ध स्टाफ:"))
            for sid, name in all_staff:
                print(T(f"ID: {sid} | Name: {name}",f"आईडी: {sid} | नाम: {name}"))
            staff_id = _validate_input(input(T("Enter Staff ID from the list above: ", "ऊपर दी गई सूची से स्टाफ आईडी दर्ज करें: ")), int, 1)
            staff_list = [staff_id]
            cur.execute("SELECT name FROM staff WHERE staff_id = %s", (staff_id,))
            name_row = cur.fetchone()
            if name_row:
                print(T(f"Selected Staff: ID {staff_id}, Name: {name_row[0]}", f"चयनित स्टाफ: आईडी {staff_id}, नाम: {name_row[0]}"))
            else:
                print(T(f"No staff found with ID {staff_id}.", f"आईडी {staff_id} वाला कोई स्टाफ नहीं मिला।"))

        elif choice == "2":
            cur.execute("SELECT staff_id FROM staff")
            staff_list = [row[0] for row in cur.fetchall()]
        else:
            raise ValueError("Invalid choice. Enter 1 or 2.")
        
        # Print the list of staff IDs being processed
        print(T(f"Processing salaries for staff IDs: {', '.join(map(str, staff_list))}", 
                f"स्टाफ आईडी के लिए वेतन प्रोसेसिंग: {', '.join(map(str, staff_list))}"))
        
        for sid in staff_list:
            # Get staff role
            cur.execute("SELECT role FROM staff WHERE staff_id = %s", (sid,))
            role_row = cur.fetchone()
            if not role_row:
                print(T(f"No staff found with ID {sid}. Skipping.", f"आईडी {sid} वाला कोई स्टाफ नहीं मिला। छोड़ रहा हूँ।"))
                continue
            original_role = role_row[0]  # Keep original case for display
            role_lower = original_role.lower()  # Use lowercase for case-insensitive matching
            
            # Get base salary from config (case-insensitive lookup)
            base_salary = 0.00
            for key, value in SALARY_RATES.items():
                if key.lower() == role_lower:
                    base_salary = value
                    break
            if base_salary == 0:
                print(T(f"No salary rate defined for role '{original_role}'. Skipping.", f"भूमिका '{original_role}' के लिए कोई वेतन दर परिभाषित नहीं। छोड़ रहा हूँ।"))
                continue
            
            # Calculate attendance bonus (present days and total working days in the month)
            # Assuming attendance is only recorded for working days
            cur.execute("""
                SELECT 
                    COUNT(CASE WHEN status = 'P' THEN 1 END) AS present_days,
                    COUNT(*) AS total_working_days
                FROM attendance 
                WHERE staff_id = %s AND DATE_FORMAT(date, '%Y-%m') = %s
            """, (sid, month))
            result = cur.fetchone()
            present_days = result[0]
            total_working_days = result[1]
            
            if total_working_days > 0:
                attendance_bonus = (present_days / total_working_days) * base_salary * BONUS_RATE
            else:
                attendance_bonus = 0.00
            
            total_salary = base_salary + attendance_bonus
            
            # Insert into salaries (use ON DUPLICATE KEY UPDATE to avoid duplicates)
            cur.execute("""
                INSERT INTO salaries (staff_id, month, base_salary, attendance_bonus, total_salary) 
                VALUES (%s, %s, %s, %s, %s) 
                ON DUPLICATE KEY UPDATE base_salary = VALUES(base_salary), 
                                         attendance_bonus = VALUES(attendance_bonus), 
                                         total_salary = VALUES(total_salary)
            """, (sid, month, base_salary, attendance_bonus, total_salary))
            
            print(T(f"Salary for Staff ID {sid} ({original_role}): Base ₹{base_salary:.2f}, Bonus ₹{attendance_bonus:.2f}, Total ₹{total_salary:.2f}", 
                    f"स्टाफ आईडी {sid} ({original_role}) के लिए वेतन: आधार ₹{base_salary:.2f}, बोनस ₹{attendance_bonus:.2f}, कुल ₹{total_salary:.2f}"))
        
        con.commit()
        print(T("Salary generation completed successfully.", "वेतन जनरेशन सफलतापूर्वक पूरा हुआ।"))
    
    except mysql.connector.Error as e:
        logging.error(f"DB error in generate_salary: {e}")
        con.rollback()
        print(T("Database error occurred.", "डेटाबेस त्रुटि हुई।"))
    except ValueError as e:
        logging.warning(f"Validation error in generate_salary: {e}")
        print(T(f"Input error: {e}", f"इनपुट त्रुटि: {e}"))
    finally:
        if con:
            con.close()

# =====================================================
# PATIENT MANAGEMENT
# =====================================================
def register_patient():
    con = db()
    if con is None:
        return
    cur = con.cursor()

    try:
        name = input(T("Name: ", "नाम: "))
        age = input(T("Age: ", "आयु: "))
        gender = input(T("Gender: ", "लिंग: "))
        contact_no = input(T("Contact: ", "संपर्क: "))
        insurance = input(T("Insurance Company: ", "बीमा कंपनी: "))

        # Validate age input
        try:
            age = int(age)
        except ValueError:
            print(T("Invalid age entered. Please enter a number.", "अमान्य आयु दर्ज की गई। कृपया एक संख्या दर्ज करें।"))
            return

        cur.execute(
            "INSERT INTO patients(name, age, gender, contact_no, insurance) VALUES (%s, %s, %s, %s, %s)",
            (name, age, gender.upper(), contact_no, insurance)
        )
        con.commit()
        print(T("Patient registered", "रोगी पंजीकृत"))
    except mysql.connector.Error as e:
        print(f"Database error: {e}")
        con.rollback()
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        con.close()

def manage_patients():
    con = db()
    if con is None:
        return
    cur = con.cursor()

    while True:
        print("\n---", T("Patient Management", "रोगी प्रबंधन"), "---")
        print("1.", T("Register Patient", "रोगी पंजीकरण"))
        print("2.", T("View Patients", "रोगी देखें"))
        print("3.", T("Update Patient", "रोगी अपडेट करें"))
        print("4.", T("Delete Patient", "रोगी हटाएं"))
        print("5.", T("Back to Main Menu", "मुख्य मेनू पर लौटें"))

        choice = input(T("Enter choice: ", "विकल्प दर्ज करें: "))
        try:
            if choice == "1":
                register_patient()

            elif choice == "2":
                cur.execute("SELECT * FROM patients")
                rows = cur.fetchall()
                for p in rows:
                    print(f"ID: {p[0]}| Name: {p[1]}| Age: {p[2]}| Gender: {p[3]}| Contact: {p[4]}| Insurance: {p[5]}")

            elif choice == "3":
                pid = int(input(T("Enter Patient ID to update: ", "अपडेट करने के लिए रोगी आईडी दर्ज करें: ")))
                name = input(T("New Name: ", "नया नाम: "))
                age = input(T("New Age: ", "नई आयु: "))
                gender = input(T("Gender: ", "लिंग: "))
                contact_no = input(T("New Contact: ", "नया संपर्क: "))
                insurance = input(T("New Insurance Company: ", "नई बीमा कंपनी: "))
                cur.execute("UPDATE patients SET name=%s, age=%s, gender=%s, contact_no=%s, insurance=%s WHERE patient_id=%s", (name, age, gender, contact_no, insurance, pid))
                con.commit()
                print(T("Patient updated.", "रोगी अपडेट किया गया।"))

            elif choice == "4":
                pid = int(input(T("Enter Patient ID to delete: ", "हटाने के लिए रोगी आईडी दर्ज करें: ")))
                cur.execute("DELETE FROM patients WHERE patient_id=%s", (pid,))
                con.commit()
                print(T("Patient deleted.", "रोगी हटाया गया।"))

            elif choice == "5":
                break
            else:
                print(T("Invalid choice.", "गलत विकल्प।"))
        except ValueError:
            print(T("Invalid input. Please enter valid data.", "अमान्य इनपुट। कृपया मान्य डेटा दर्ज करें।"))
        except mysql.connector.Error as e:
            print(f"Database error: {e}")
            con.rollback()
        except Exception as e:
            print(f"Unexpected error: {e}")

    con.close()

def search_patient():
    con = db()
    if con is None:
        return
    cur = con.cursor()
    try:
        keyword = input(T("Enter Patient Name or ID: ", "रोगी का नाम या आईडी दर्ज करें: ")).strip()

        if keyword.isdigit():
            cur.execute("SELECT patient_id, name, age, gender, contact_no, insurance FROM patients WHERE patient_id = %s", (int(keyword),))
        else:
            cur.execute("SELECT patient_id, name, age, gender, contact_no, insurance FROM patients WHERE name LIKE %s", ('%' + keyword + '%',))

        results = cur.fetchall()
        if results:
            print(T(f"\nFound {len(results)} patient(s):", f"\n{len(results)} रोगी पाए गए:"))
            for patient in results:
                print(f"ID: {patient[0]}| Name: {patient[1]}| Age: {patient[2]}| Gender: {patient[3]}| Contact: {patient[4]}| Insurance: {patient[5]}")
        else:
            print(T("No matching patient found.", "कोई मेल खाता रोगी नहीं मिला।"))
    except mysql.connector.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        con.close()

# =====================================================
# APPOINTMENTS
# =====================================================
def book_appointment():
    try:
        con = db()
        cur = con.cursor()
        
        # Fetch and display patients
        cur.execute("SELECT patient_id, name FROM patients")
        patients = cur.fetchall()
        if not patients:
            print(T("No patients found.", "कोई रोगी नहीं मिला।"))
            con.close()
            return
        for p in patients:
            print(f"{p[0]}: {p[1]}")
        
        # Select Patient ID with error handling
        try:
            pid = int(input(T("Select Patient ID: ", "रोगी आईडी चुनें: ")))
        except ValueError:
            print(T("Invalid Patient ID. Please enter a number.", "अमान्य रोगी आईडी। कृपया एक संख्या दर्ज करें।"))
            con.close()
            return
        
        # Check if patient exists
        cur.execute("SELECT 1 FROM patients WHERE patient_id = %s", (pid,))
        if not cur.fetchone():
            print(T("Patient not found.", "रोगी नहीं मिला।"))
            con.close()
            return
        
        # Fetch and display doctors
        cur.execute("SELECT staff_id, name FROM staff WHERE role = 'Doctor'")
        docs = cur.fetchall()
        if not docs:
            print(T("No doctors found.", "कोई डॉक्टर नहीं मिला।"))
            con.close()
            return
        for d in docs:
            print(f"{d[0]}: {d[1]}")
        
        # Select Doctor ID with error handling
        try:
            did = int(input(T("Select Doctor ID: ", "डॉक्टर आईडी चुनें: ")))
        except ValueError:
            print(T("Invalid Doctor ID. Please enter a number.", "अमान्य डॉक्टर आईडी। कृपया एक संख्या दर्ज करें।"))
            con.close()
            return
        
        # Check if doctor exists
        cur.execute("SELECT 1 FROM staff WHERE staff_id = %s AND role = 'Doctor'", (did,))
        if not cur.fetchone():
            print(T("Doctor not found.", "डॉक्टर नहीं मिला।"))
            con.close()
            return
        
        # Input and validate appointment date
        date_str = input(T("Appointment Date (YYYY-MM-DD): ", "अपॉइंटमेंट तिथि (YYYY-MM-DD): "))
        try:
            appointment_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            print(T("Invalid date format. Please use YYYY-MM-DD.", "अमान्य तिथि प्रारूप। कृपया YYYY-MM-DD का उपयोग करें।"))
            con.close()
            return
        
        # Insert appointment
        cur.execute("INSERT INTO appointments(patient_id, doctor_id, appointment_date) VALUES(%s, %s, %s)", (pid, did, appointment_date))
        con.commit()
        print(T("Appointment booked successfully.", "अपॉइंटमेंट सफलतापूर्वक बुक किया गया।"))
        
    except mysql.connector.Error as e:
        print(T(f"Database error: {e}", f"डेटाबेस त्रुटि: {e}"))
    except Exception as e:
        print(T(f"An unexpected error occurred: {e}", f"एक अप्रत्याशित त्रुटि हुई: {e}"))
    finally:
        if 'con' in locals() and con.is_connected():
            con.close()

# =====================================================
# ADMISSIONS & DISCHARGE
# =====================================================
def admit_patient(area):
    try:
        con = db()
        cur = con.cursor()
        
        # Fetch and display patients
        cur.execute("SELECT patient_id, name FROM patients")
        patients = cur.fetchall()
        if not patients:
            print(T("No patients found.", "कोई रोगी नहीं मिला।"))
            con.close()
            return
        for p in patients:
            print(f"{p[0]}: {p[1]}")
        
        # Select Patient ID with error handling
        try:
            pid = int(input(T("Select Patient ID: ", "रोगी आईडी चुनें: ")))
        except ValueError:
            print(T("Invalid Patient ID. Please enter a number.", "अमान्य रोगी आईडी। कृपया एक संख्या दर्ज करें।"))
            con.close()
            return
        
        # Check if patient exists
        cur.execute("SELECT 1 FROM patients WHERE patient_id = %s", (pid,))
        if not cur.fetchone():
            print(T("Patient not found.", "रोगी नहीं मिला।"))
            con.close()
            return
        
        # Insert admission record
        cur.execute(f"INSERT INTO {area}_records(patient_id, admit_date) VALUES(%s, %s)", (pid, datetime.now()))
        con.commit()
        print(T(f"Patient admitted to {area.upper()} successfully.", f"रोगी का दाखिला {area.upper()} में सफलतापूर्वक किया गया।"))
        
    except mysql.connector.Error as e:
        print(T(f"Database error: {e}", f"डेटाबेस त्रुटि: {e}"))
    except Exception as e:
        print(T(f"An unexpected error occurred: {e}", f"एक अप्रत्याशित त्रुटि हुई: {e}"))
    finally:
        if 'con' in locals() and con.is_connected():
            con.close()

def discharge_patient(area):
    try:
        con = db()
        cur = con.cursor()
        
        # Fetch records for discharge
        cur.execute(f"SELECT record_id, patient_id FROM {area}_records WHERE discharge_date IS NULL")
        records = cur.fetchall()
        if not records:
            print(T(f"No active records in {area.upper()}.", f"{area.upper()} में कोई सक्रिय रिकॉर्ड नहीं।"))
            con.close()
            return
        for r in records:
            cur.execute("SELECT name FROM patients WHERE patient_id = %s", (r[1],))
            name = cur.fetchone()
            if name:
                print(f"{r[0]}: {name[0]}")
        
        # Select Record ID with error handling
        try:
            rid = int(input(T("Select Record ID for discharge: ", "डिस्चार्ज के लिए रिकॉर्ड आईडी चुनें: ")))
        except ValueError:
            print(T("Invalid Record ID. Please enter a number.", "अमान्य रिकॉर्ड आईडी। कृपया एक संख्या दर्ज करें।"))
            con.close()
            return
        
        # Check if record exists and is active
        cur.execute(f"SELECT 1 FROM {area}_records WHERE record_id = %s AND discharge_date IS NULL", (rid,))
        if not cur.fetchone():
            print(T("Record not found or already discharged.", "रिकॉर्ड नहीं मिला या पहले ही डिस्चार्ज किया गया।"))
            con.close()
            return
        
        # Update discharge date
        cur.execute(f"UPDATE {area}_records SET discharge_date = %s WHERE record_id = %s", (datetime.now(), rid))
        con.commit()
        print(T("Patient discharged successfully.", "रोगी को सफलतापूर्वक डिस्चार्ज किया गया।"))
        
    except mysql.connector.Error as e:
        print(T(f"Database error: {e}", f"डेटाबेस त्रुटि: {e}"))
    except Exception as e:
        print(T(f"An unexpected error occurred: {e}", f"एक अप्रत्याशित त्रुटि हुई: {e}"))
    finally:
        if 'con' in locals() and con.is_connected():
            con.close()

# =====================================================
# LAB TESTS
# =====================================================
def manage_lab_tests():
    try:
        con = db()
        cur = con.cursor()

        while True:
            print("\n---", T("Lab Test Management", "लैब टेस्ट प्रबंधन"), "---")
            print("1.", T("View Lab Tests", "लैब टेस्ट देखें"))
            print("2.", T("Add Lab Test", "लैब टेस्ट जोड़ें"))
            print("3.", T("Update Lab Test", "लैब टेस्ट अपडेट करें"))
            print("4.", T("Delete Lab Test", "लैब टेस्ट हटाएं"))
            print("5.", T("Assign Test to Patient", "रोगी को टेस्ट असाइन करें"))
            print("6.", T("Update Patient Test Result", "रोगी टेस्ट परिणाम अपडेट करें"))
            print("7.", T("View Patient Test Results", "रोगी टेस्ट परिणाम देखें"))
            print("8.", T("Back to Main Menu", "मुख्य मेनू पर लौटें"))

            choice = input(T("Enter choice: ", "विकल्प दर्ज करें: "))

            # -----------------------------
            # 1. View Tests
            # -----------------------------
            if choice == "1":
                cur.execute("SELECT * FROM lab_tests")
                rows = cur.fetchall()
                if not rows:
                    print(T("No lab tests found.", "कोई लैब टेस्ट नहीं मिला।"))
                for t in rows:
                    print(f"ID: {t[0]}| Name: {t[1]}| Cost: {t[2]}")

            # -----------------------------
            # 2. Add New Test
            # -----------------------------
            elif choice == "2":
                name = input(T("Test Name: ", "टेस्ट का नाम: "))
                try:
                    cost = float(input(T("Cost: ", "कीमत: ")))
                except ValueError:
                    print(T("Invalid cost. Please enter a number.", "अमान्य कीमत। कृपया एक संख्या दर्ज करें।"))
                    continue
                cur.execute("INSERT INTO lab_tests(name, cost) VALUES(%s, %s)", (name, cost))
                con.commit()
                print(T("Lab test added.", "लैब टेस्ट जोड़ा गया।"))

            # -----------------------------
            # 3. Update Test
            # -----------------------------
            elif choice == "3":
                cur.execute("SELECT * FROM lab_tests")
                for t in cur.fetchall():
                    print(f"{t[0]}: {t[1]}| Cost: {t[2]}")
                try:
                    tid = int(input(T("Enter Test ID to update: ", "अपडेट करने के लिए टेस्ट आईडी दर्ज करें: ")))
                except ValueError:
                    print(T("Invalid Test ID. Please enter a number.", "अमान्य टेस्ट आईडी। कृपया एक संख्या दर्ज करें।"))
                    continue
                new_name = input(T("New Name: ", "नया नाम: "))
                try:
                    new_cost = float(input(T("New Cost: ", "नई कीमत: ")))
                except ValueError:
                    print(T("Invalid cost. Please enter a number.", "अमान्य कीमत। कृपया एक संख्या दर्ज करें।"))
                    continue
                cur.execute("UPDATE lab_tests SET name=%s, cost=%s WHERE test_id=%s", (new_name, new_cost, tid))
                con.commit()
                print(T("Lab test updated.", "लैब टेस्ट अपडेट किया गया।"))

            # -----------------------------
            # 4. Delete Test
            # -----------------------------
            elif choice == "4":
                try:
                    tid = int(input(T("Enter Test ID to delete: ", "हटाने के लिए टेस्ट आईडी दर्ज करें: ")))
                except ValueError:
                    print(T("Invalid Test ID. Please enter a number.", "अमान्य टेस्ट आईडी। कृपया एक संख्या दर्ज करें।"))
                    continue
                cur.execute("DELETE FROM lab_tests WHERE test_id=%s", (tid,))
                con.commit()
                print(T("Lab test deleted.", "लैब टेस्ट हटाया गया।"))

            # -----------------------------
            # 5. Assign Test to Patient
            # -----------------------------
            elif choice == "5":
                cur.execute("SELECT patient_id, name FROM patients")
                for p in cur.fetchall():
                    print(f"{p[0]}: {p[1]}")
                try:
                    pid = int(input(T("Select Patient ID: ", "रोगी आईडी चुनें: ")))
                except ValueError:
                    print(T("Invalid Patient ID. Please enter a number.", "अमान्य रोगी आईडी। कृपया एक संख्या दर्ज करें।"))
                    continue

                cur.execute("SELECT * FROM lab_tests")
                for t in cur.fetchall():
                    print(f"{t[0]}: {t[1]} (₹{t[2]})")
                try:
                    tid = int(input(T("Select Test ID: ", "टेस्ट आईडी चुनें: ")))
                except ValueError:
                    print(T("Invalid Test ID. Please enter a number.", "अमान्य टेस्ट आईडी। कृपया एक संख्या दर्ज करें।"))
                    continue

                # Assign Technician
                cur.execute("SELECT staff_id, name FROM staff WHERE role='Technician'")
                techs = cur.fetchall()
                tech_id = None
                if techs:
                    print(T("\nAvailable Technicians:", "उपलब्ध तकनीशियन:"))
                    for t in techs:
                        print(f"{t[0]}: {t[1]}")
                    try:
                        tech_id = int(input(T("Assign Technician ID: ", "तकनीशियन आईडी असाइन करें: ")))
                    except ValueError:
                        print(T("Invalid Technician ID. Assigning NULL.", "अमान्य तकनीशियन आईडी। NULL असाइन किया गया।"))
                        tech_id = None
                else:
                    print(T("No technician found. Assigning NULL.", "कोई तकनीशियन नहीं मिला, NULL असाइन किया गया।"))

                cur.execute("""INSERT INTO patient_lab_results(patient_id, test_id, technician_id, test_date)
                               VALUES(%s,%s,%s,%s)""",
                            (pid, tid, tech_id, datetime.now()))
                con.commit()
                print(T("Lab test assigned to patient.", "लैब टेस्ट रोगी को असाइन किया गया।"))

            # -----------------------------
            # 6. Update Test Result
            # -----------------------------
            elif choice == "6":
                cur.execute("""SELECT r.record_id, p.name, t.name
                               FROM patient_lab_results r
                               JOIN patients p ON r.patient_id=p.patient_id
                               JOIN lab_tests t ON r.test_id=t.test_id
                               WHERE r.result IS NULL""")
                records = cur.fetchall()
                if not records:
                    print(T("No pending test results.", "कोई लंबित टेस्ट परिणाम नहीं।"))
                else:
                    for r in records:
                        print(f"{r[0]}: {r[1]} - {r[2]}")
                    try:
                        rid = int(input(T("Enter Record ID to update: ", "अपडेट करने के लिए रिकॉर्ड आईडी दर्ज करें: ")))
                    except ValueError:
                        print(T("Invalid Record ID. Please enter a number.", "अमान्य रिकॉर्ड आईडी। कृपया एक संख्या दर्ज करें।"))
                        continue
                    result = input(T("Enter Result: ", "परिणाम दर्ज करें: "))
                    cur.execute("UPDATE patient_lab_results SET result=%s, result_date=%s WHERE record_id=%s",
                                (result, datetime.now(), rid))
                    con.commit()
                    print(T("Result updated.", "परिणाम अपडेट किया गया।"))

            # -----------------------------
            # 7. View Patient Test Results
            # -----------------------------
            elif choice == "7":
                try:
                    pid = int(input(T("Enter Patient ID: ", "रोगी आईडी दर्ज करें: ")))
                except ValueError:
                    print(T("Invalid Patient ID. Please enter a number.", "अमान्य रोगी आईडी। कृपया एक संख्या दर्ज करें।"))
                    continue
                cur.execute("""SELECT r.record_id, t.name, r.result, r.result_date
                               FROM patient_lab_results r
                               JOIN lab_tests t ON r.test_id=t.test_id
                               WHERE r.patient_id=%s""", (pid,))
                rows = cur.fetchall()
                if not rows:
                    print(T("No test results for this patient.", "इस रोगी के लिए कोई टेस्ट परिणाम नहीं।"))
                for r in rows:
                    print(f"Record ID: {r[0]}| Test: {r[1]}| Result: {r[2]}| Date: {r[3]}")

            # -----------------------------
            # 8. Exit
            # -----------------------------
            elif choice == "8":
                break

            else:
                print(T("Invalid choice.", "गलत विकल्प।"))

    except mysql.connector.Error as e:
        print(T(f"Database error: {e}", f"डेटाबेस त्रुटि: {e}"))
    except Exception as e:
        print(T(f"An unexpected error occurred: {e}", f"एक अप्रत्याशित त्रुटि हुई: {e}"))
    finally:
        if 'con' in locals() and con.is_connected():
            con.close()

# =====================================================
# SURGERIES
# =====================================================
def register_surgery():
    try:
        con = db()
        cur = con.cursor()
        
        # Fetch and display patients
        cur.execute("SELECT patient_id, name FROM patients")
        patients = cur.fetchall()
        if not patients:
            print(T("No patients found.", "कोई रोगी नहीं मिला।"))
            con.close()
            return
        for p in patients:
            print(f"{p[0]}: {p[1]}")
        
        # Select Patient ID
        try:
            pid = int(input(T("Patient ID: ", "रोगी आईडी: ")))
        except ValueError:
            print(T("Invalid Patient ID. Please enter a number.", "अमान्य रोगी आईडी। कृपया एक संख्या दर्ज करें।"))
            con.close()
            return
        
        # Check if patient exists
        cur.execute("SELECT 1 FROM patients WHERE patient_id = %s", (pid,))
        if not cur.fetchone():
            print(T("Patient not found.", "रोगी नहीं मिला।"))
            con.close()
            return
        
        # Fetch and display doctors
        cur.execute("SELECT staff_id, name FROM staff WHERE role = 'Doctor'")
        docs = cur.fetchall()
        if not docs:
            print(T("No doctors found.", "कोई डॉक्टर नहीं मिला।"))
            con.close()
            return
        for d in docs:
            print(f"{d[0]}: {d[1]}")
        
        # Select Surgeon ID
        try:
            did = int(input(T("Surgeon ID: ", "सर्जन आईडी: ")))
        except ValueError:
            print(T("Invalid Surgeon ID. Please enter a number.", "अमान्य सर्जन आईडी। कृपया एक संख्या दर्ज करें।"))
            con.close()
            return
        
        # Check if surgeon exists
        cur.execute("SELECT 1 FROM staff WHERE staff_id = %s AND role = 'Doctor'", (did,))
        if not cur.fetchone():
            print(T("Surgeon not found.", "सर्जन नहीं मिला।"))
            con.close()
            return
        
        surgery_type = input(T("Surgery Type: ", "सर्जरी का प्रकार: "))
        
        # Insert surgery record
        cur.execute("INSERT INTO surgeries(patient_id, surgeon_id, surgery_type, date) VALUES(%s, %s, %s, %s)",
                    (pid, did, surgery_type, datetime.now()))
        con.commit()
        print(T("Surgery registered successfully.", "सर्जरी सफलतापूर्वक पंजीकृत।"))
        
    except mysql.connector.Error as e:
        print(T(f"Database error: {e}", f"डेटाबेस त्रुटि: {e}"))
    except Exception as e:
        print(T(f"An unexpected error occurred: {e}", f"एक अप्रत्याशित त्रुटि हुई: {e}"))
    finally:
        if 'con' in locals() and con.is_connected():
            con.close()

# =====================================================
# PRESCRIPTIONS
# =====================================================
def add_prescription():
    try:
        con = db()
        cur = con.cursor()
        
        # Fetch and display patients
        cur.execute("SELECT patient_id, name FROM patients")
        patients = cur.fetchall()
        if not patients:
            print(T("No patients found.", "कोई रोगी नहीं मिला।"))
            con.close()
            return
        for p in patients:
            print(f"{p[0]}: {p[1]}")
        
        # Select Patient ID
        try:
            pid = int(input(T("Patient ID: ", "रोगी आईडी: ")))
        except ValueError:
            print(T("Invalid Patient ID. Please enter a number.", "अमान्य रोगी आईडी। कृपया एक संख्या दर्ज करें।"))
            con.close()
            return
        
        # Check if patient exists
        cur.execute("SELECT 1 FROM patients WHERE patient_id = %s", (pid,))
        if not cur.fetchone():
            print(T("Patient not found.", "रोगी नहीं मिला।"))
            con.close()
            return
        
        # Fetch and display doctors
        cur.execute("SELECT staff_id, name FROM staff WHERE role = 'Doctor'")
        docs = cur.fetchall()
        if not docs:
            print(T("No doctors found.", "कोई डॉक्टर नहीं मिला।"))
            con.close()
            return
        for d in docs:
            print(f"{d[0]}: {d[1]}")
        
        # Select Doctor ID
        try:
            did = int(input(T("Doctor ID: ", "डॉक्टर आईडी: ")))
        except ValueError:
            print(T("Invalid Doctor ID. Please enter a number.", "अमान्य डॉक्टर आईडी। कृपया एक संख्या दर्ज करें।"))
            con.close()
            return
        
        # Check if doctor exists
        cur.execute("SELECT 1 FROM staff WHERE staff_id = %s AND role = 'Doctor'", (did,))
        if not cur.fetchone():
            print(T("Doctor not found.", "डॉक्टर नहीं मिला।"))
            con.close()
            return
        
        medicines = input(T("Medicines: ", "दवाइयाँ: "))
        vitals = input(T("Vitals: ", "वाइटल्स: "))
        notes = input(T("Clinical Notes: ", "क्लिनिकल नोट्स: "))
        
        # Insert prescription
        cur.execute("INSERT INTO prescriptions(patient_id, doctor_id, medicines, vitals, notes, date) VALUES(%s, %s, %s, %s, %s, %s)",
                    (pid, did, medicines, vitals, notes, datetime.now()))
        con.commit()
        print(T("Prescription added successfully.", "प्रिस्क्रिप्शन सफलतापूर्वक जोड़ी गई।"))
        
    except mysql.connector.Error as e:
        print(T(f"Database error: {e}", f"डेटाबेस त्रुटि: {e}"))
    except Exception as e:
        print(T(f"An unexpected error occurred: {e}", f"एक अप्रत्याशित त्रुटि हुई: {e}"))
    finally:
        if 'con' in locals() and con.is_connected():
            con.close()

# =====================================================
# BILLING & INSURANCE
# =====================================================
def generate_bill():
    try:
        con = db()
        cur = con.cursor()

        # -----------------------------
        # Select Patient
        # -----------------------------
        cur.execute("SELECT patient_id, name FROM patients")
        patients = cur.fetchall()
        if not patients:
            print(T("No patients found.", "कोई रोगी नहीं मिला।"))
            con.close()
            return
        for p in patients:
            print(f"{p[0]}: {p[1]}")
        try:
            pid = int(input(T("Select Patient ID: ", "रोगी आईडी चुनें: ")))
        except ValueError:
            print(T("Invalid Patient ID. Please enter a number.", "अमान्य रोगी आईडी। कृपया एक संख्या दर्ज करें।"))
            con.close()
            return
        
        # Check if patient exists
        cur.execute("SELECT 1 FROM patients WHERE patient_id = %s", (pid,))
        if not cur.fetchone():
            print(T("Patient not found.", "रोगी नहीं मिला।"))
            con.close()
            return

        total_amount = 0

        # -----------------------------
        # 1️⃣ Surgeries
        # -----------------------------
        cur.execute("SELECT COUNT(*), COUNT(*)*5000 FROM surgeries WHERE patient_id=%s", (pid,))
        surgery_count, surgery_charge = cur.fetchone()
        surgery_charge = surgery_charge or 0
        total_amount += surgery_charge

        # -----------------------------
        # 2️⃣ Medicines
        # -----------------------------
        cur.execute("""
            SELECT SUM(ph.price)
            FROM prescriptions p
            JOIN pharmacy ph ON FIND_IN_SET(ph.name, p.medicines)
            WHERE p.patient_id=%s
        """, (pid,))
        meds_charge = cur.fetchone()[0] or 0
        total_amount += meds_charge

        # -----------------------------
        # 3️⃣ Lab Tests
        # -----------------------------
        cur.execute("""
            SELECT SUM(t.cost)
            FROM patient_lab_results r
            JOIN lab_tests t ON r.test_id = t.test_id
            WHERE r.patient_id = %s
        """, (pid,))
        lab_charge = cur.fetchone()[0] or 0
        total_amount += lab_charge

        # -----------------------------
        # 4️⃣ Room Charges (OPD + ICU)
        # -----------------------------
        opd_rate = 1000
        icu_rate = 5000
        opd_charge = 0
        icu_charge = 0

        # OPD stay
        cur.execute("""
            SELECT admit_date, discharge_date 
            FROM opd_records WHERE patient_id=%s
        """, (pid,))
        for a_date, d_date in cur.fetchall():
            if d_date is None:
                d_date = datetime.now()
            days = (d_date - a_date).days + 1
            opd_charge += days * opd_rate

        # ICU stay
        cur.execute("""
            SELECT admit_date, discharge_date 
            FROM icu_records WHERE patient_id=%s
        """, (pid,))
        for a_date, d_date in cur.fetchall():
            if d_date is None:
                d_date = datetime.now()
            days = (d_date - a_date).days + 1
            icu_charge += days * icu_rate

        total_amount += opd_charge + icu_charge

        # -----------------------------
        # Show Billing Breakdown
        # -----------------------------
        print(T(
            f"""
--- Billing Breakdown ---
Surgeries: ₹{surgery_charge}
Medicines: ₹{meds_charge}
Lab Tests: ₹{lab_charge}
OPD Stay: ₹{opd_charge}
ICU Stay: ₹{icu_charge}
--------------------------
Total Before Insurance: ₹{total_amount}
""",
            f"""
--- बिल विवरण ---
सर्जरी: ₹{surgery_charge}
दवाइयाँ: ₹{meds_charge}
लैब टेस्ट: ₹{lab_charge}
OPD ठहराव: ₹{opd_charge}
ICU ठहराव: ₹{icu_charge}
--------------------------
बीमा से पहले कुल: ₹{total_amount}
"""
        ))

        # -----------------------------
        # 5️⃣ Insurance
        # -----------------------------
        insurance = input(T("Insurance used? (Y/N): ", "बीमा उपयोग किया? (Y/N): ")).upper()
        ins_amt = 0
        if insurance == "Y":
            ins_name = input(T("Insurance Company: ", "बीमा कंपनी: "))
            try:
                ins_amt = float(input(T("Insurance covers amount: ", "बीमा द्वारा कवर राशि: ")))
            except ValueError:
                print(T("Invalid insurance amount. Setting to 0.", "अमान्य बीमा राशि। 0 पर सेट किया गया।"))
                ins_amt = 0
            cur.execute(
                "INSERT INTO insurance_claims(patient_id,insurance_company,claim_amount,date) VALUES(%s,%s,%s,%s)",
                (pid, ins_name, ins_amt, datetime.now()),
            )

        # -----------------------------
        # 6️⃣ Final Bill
        # -----------------------------
        final_amount = total_amount - ins_amt
        cur.execute(
            "INSERT INTO bills(patient_id,amount,insurance_covered,date) VALUES(%s,%s,%s,%s)",
            (pid, final_amount, ins_amt, datetime.now()),
        )
        con.commit()

        print(T(
            f"\n✅ Bill generated successfully!\nPayable Amount: ₹{final_amount}",
            f"\n✅ बिल सफलतापूर्वक तैयार!\nदेय राशि: ₹{final_amount}"
        ))

    except mysql.connector.Error as e:
        print(T(f"Database error: {e}", f"डेटाबेस त्रुटि: {e}"))
    except Exception as e:
        print(T(f"An unexpected error occurred: {e}", f"एक अप्रत्याशित त्रुटि हुई: {e}"))
    finally:
        if 'con' in locals() and con.is_connected():
            con.close()

def view_patient_bill():
    try:
        con = db()
        cur = con.cursor()
        try:
            pid = int(input(T("Enter Patient ID to view bill: ","रोगी आईडी दर्ज करें बिल देखने के लिए: ")))
        except ValueError:
            print(T("Invalid Patient ID. Please enter a number.", "अमान्य रोगी आईडी। कृपया एक संख्या दर्ज करें।"))
            con.close()
            return

        cur.execute("SELECT name FROM patients WHERE patient_id=%s",(pid,))
        patient = cur.fetchone()
        if not patient:
            print(T("Patient not found.","रोगी नहीं मिला।"))
            con.close()
            return

        print(T(f"\n--- Bill Summary for {patient[0]} ---", f"\n--- {patient[0]} के लिए बिल सारांश ---"))

        # Surgeries
        cur.execute("SELECT COUNT(*), COUNT(*)*5000 FROM surgeries WHERE patient_id=%s",(pid,))
        surgery_count, surgery_charge = cur.fetchone()
        print(T(f"Surgeries: {surgery_count} (₹{surgery_charge})", f"सर्जरी: {surgery_count} (₹{surgery_charge})"))

        # Lab Tests
        cur.execute("""
            SELECT COUNT(*), SUM(t.cost)
            FROM patient_lab_results r
            JOIN lab_tests t ON r.test_id=t.test_id
            WHERE r.patient_id=%s
        """,(pid,))
        lab_count, lab_charge = cur.fetchone()
        lab_charge = lab_charge or 0
        print(T(f"Lab Tests: {lab_count} (₹{lab_charge})", f"लैब टेस्ट: {lab_count} (₹{lab_charge})"))

        # Medicines
        cur.execute("""
            SELECT SUM(ph.price)
            FROM prescriptions p
            JOIN pharmacy ph ON FIND_IN_SET(ph.name, p.medicines)
            WHERE p.patient_id=%s
        """,(pid,))
        meds_charge = cur.fetchone()[0] or 0
        print(T(f"Medicines: ₹{meds_charge}", f"दवाइयाँ: ₹{meds_charge}"))

        # Total and Final Bill
        cur.execute("SELECT amount, insurance_covered, date FROM bills WHERE patient_id=%s ORDER BY date DESC LIMIT 1",(pid,))
        bill = cur.fetchone()
        if bill:
            print(T(f"\nFinal Amount: ₹{bill[0]} (Insurance: ₹{bill[1]})\nDate: {bill[2]}",
                    f"\nअंतिम राशि: ₹{bill[0]} (बीमा: ₹{bill[1]})\nदिनांक: {bill[2]}"))
        else:
            print(T("No bill found for this patient.","इस रोगी का कोई बिल नहीं मिला।"))

        # Room Charges
        cur.execute("SELECT admit_date, discharge_date FROM opd_records WHERE patient_id=%s", (pid,))
        opd_days = 0
        for a, d in cur.fetchall():
            if d is None:
                d = datetime.now()
            opd_days += (d - a).days + 1
        cur.execute("SELECT admit_date, discharge_date FROM icu_records WHERE patient_id=%s", (pid,))
        icu_days = 0
        for a, d in cur.fetchall():
            if d is None:
                d = datetime.now()
            icu_days += (d - a).days + 1
            print(T(f"Room Charges (OPD): ₹{opd_days*1000}, ICU: ₹{icu_days*5000}",
                f"कमरा शुल्क (OPD): ₹{opd_days*1000}, ICU: ₹{icu_days*5000}"))

    except mysql.connector.Error as e:
        print(T(f"Database error: {e}", f"डेटाबेस त्रुटि: {e}"))
    except Exception as e:
        print(T(f"An unexpected error occurred: {e}", f"एक अप्रत्याशित त्रुटि हुई: {e}"))
    finally:
        if 'con' in locals() and con.is_connected():
            con.close()

# ----------------------
# Vitals Functions
# ----------------------
def add_vitals(patient_id):
    try:
        print("\nEnter patient vitals:")
        try:
            temperature = float(input("Temperature (°C): "))
            heart_rate = int(input("Heart Rate (bpm): "))
            blood_pressure = input("Blood Pressure (e.g., 120/80): ")
            respiratory_rate = int(input("Respiratory Rate: "))
        except ValueError:
            print("Invalid input. Please enter numeric values for temperature, heart rate, and respiratory rate.")
            return
        
        con = db()
        cur = con.cursor()
        query = """
        INSERT INTO patient_vitals (patient_id, temperature, heart_rate, blood_pressure, respiratory_rate)
        VALUES (%s, %s, %s, %s, %s)
        """
        values = (patient_id, temperature, heart_rate, blood_pressure, respiratory_rate)
        cur.execute(query, values)
        con.commit()
        print(f"Vitals added for patient ID {patient_id}.\n")
        
    except mysql.connector.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if 'con' in locals() and con.is_connected():
            con.close()

def view_vitals(patient_id):
    try:
        con = db()
        cur = con.cursor(dictionary=True)  # Changed to dictionary cursor for easy access
        query = """
        SELECT * FROM patient_vitals 
        WHERE patient_id = %s
        ORDER BY date_recorded DESC
        """
        cur.execute(query, (patient_id,))
        records = cur.fetchall()
        
        if not records:
            print(f"No vitals found for patient ID {patient_id}.\n")
            return
        
        print(f"\nVitals for patient ID {patient_id}:")
        for rec in records:
            print(f"Date: {rec[6]} | Temp: {rec[2]}°C | HR: {rec[3]} bpm | BP: {rec[4]} | Resp Rate: {rec[5]}")
            print()
        
    except mysql.connector.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if 'con' in locals() and con.is_connected():
            con.close()

# =====================================================
# PHARMACY, BLOOD BANK & CANTEEN
# =====================================================
def pharmacy_management():
    try:
        con = db()
        cur = con.cursor()
        choice = input(T("Add Medicine? (Y/N): ","दवा जोड़ें? (Y/N): ")).upper()
        if choice == "Y":
            name = input(T("Medicine Name: ","दवा का नाम: "))
            try:
                qty = int(input(T("Quantity: ","मात्रा: ")))
            except ValueError:
                print(T("Invalid quantity. Please enter a number.", "अमान्य मात्रा। कृपया एक संख्या दर्ज करें।"))
                con.close()
                return
            try:
                price = float(input(T("Price per unit: ","प्रति इकाई मूल्य: ")))
            except ValueError:
                print(T("Invalid price. Please enter a number.", "अमान्य मूल्य। कृपया एक संख्या दर्ज करें।"))
                con.close()
                return
            cur.execute("INSERT INTO pharmacy(name,quantity,price) VALUES(%s,%s,%s)",(name,qty,price))
            con.commit()
        
        choice = input(T("Dispense Medicine? (Y/N): ","दवा देना? (Y/N): ")).upper()
        if choice == "Y":
            cur.execute("SELECT med_id,name,quantity,price FROM pharmacy")
            meds = cur.fetchall()
            if not meds:
                print(T("No medicines available.", "कोई दवाइयाँ उपलब्ध नहीं।"))
                con.close()
                return
            for m in meds: 
                print(f"{m[0]}: {m[1]}| Qty: {m[2]}| Price/unit: {m[3]}")
            
            try:
                mid = int(input(T("Select Medicine ID: ","दवा आईडी चुनें: ")))
            except ValueError:
                print(T("Invalid Medicine ID. Please enter a number.", "अमान्य दवा आईडी। कृपया एक संख्या दर्ज करें।"))
                con.close()
                return
            
            try:
                qty = int(input(T("Quantity to dispense: ","मात्रा: ")))
            except ValueError:
                print(T("Invalid quantity. Please enter a number.", "अमान्य मात्रा। कृपया एक संख्या दर्ज करें।"))
                con.close()
                return
            
            # Fetch unit price and available qty
            cur.execute("SELECT price, quantity FROM pharmacy WHERE med_id=%s",(mid,))
            result = cur.fetchone()
            if not result:
                print(T("Medicine not found.", "दवा नहीं मिली।"))
                con.close()
                return
            unit_price, available_qty = result
            if qty > available_qty:
                print(T("Not enough stock.","स्टॉक पर्याप्त नहीं है।"))
                con.close()
                return
            total_price = unit_price * qty
            cur.execute("UPDATE pharmacy SET quantity=quantity-%s WHERE med_id=%s",(qty,mid))
            con.commit()
            print(T(f"Medicine dispensed. Total Price: {total_price}","दवा दी गई। कुल कीमत: {total_price}"))
    
    except mysql.connector.Error as e:
        print(T(f"Database error: {e}", f"डेटाबेस त्रुटि: {e}"))
    except Exception as e:
        print(T(f"An unexpected error occurred: {e}", f"एक अप्रत्याशित त्रुटि हुई: {e}"))
    finally:
        if 'con' in locals() and con.is_connected():
            con.close()

def blood_bank_management():
    try:
        con = db()
        cur = con.cursor()
        choice = input(T("Add Blood Unit? (Y/N): ","रक्त यूनिट जोड़ें? (Y/N): ")).upper()
        if choice == "Y":
            blood_type = input(T("Blood Type: ","रक्त प्रकार: "))
            try:
                qty = int(input(T("Units: ","यूनिट: ")))
            except ValueError:
                print(T("Invalid units. Please enter a number.", "अमान्य यूनिट। कृपया एक संख्या दर्ज करें।"))
                con.close()
                return
            cur.execute("INSERT INTO blood_bank(blood_type,quantity) VALUES(%s,%s)",(blood_type,qty))
            con.commit()
        print(T("Blood Bank updated","ब्लड बैंक अपडेट"))
    
    except mysql.connector.Error as e:
        print(T(f"Database error: {e}", f"डेटाबेस त्रुटि: {e}"))
    except Exception as e:
        print(T(f"An unexpected error occurred: {e}", f"एक अप्रत्याशित त्रुटि हुई: {e}"))
    finally:
        if 'con' in locals() and con.is_connected():
            con.close()

def canteen_sales():
    try:
        con = db()
        cur = con.cursor()
        item = input(T("Item sold: ","विक्रय आइटम: "))
        try:
            amount = float(input(T("Amount: ","राशि: ")))
        except ValueError:
            print(T("Invalid amount. Please enter a number.", "अमान्य राशि। कृपया एक संख्या दर्ज करें।"))
            con.close()
            return
        cur.execute("INSERT INTO canteen(item,amount,date) VALUES(%s,%s,%s)",(item,amount,datetime.now()))
        con.commit()
        print(T("Canteen sale recorded","कैंटीन बिक्री दर्ज"))
    
    except mysql.connector.Error as e:
        print(T(f"Database error: {e}", f"डेटाबेस त्रुटि: {e}"))
    except Exception as e:
        print(T(f"An unexpected error occurred: {e}", f"एक अप्रत्याशित त्रुटि हुई: {e}"))
    finally:
        if 'con' in locals() and con.is_connected():
            con.close()

# =====================================================
# DOCTOR MANAGEMENT
# =====================================================
def doctor_management():
    try:
        con = db()
        cur = con.cursor()
        
        # Assume doctor ID is provided (in a real system, get from login session)
        did = int(input(T("Enter your Doctor ID: ", "अपना डॉक्टर आईडी दर्ज करें: ")))
        cur.execute("SELECT 1 FROM staff WHERE staff_id = %s AND role = 'Doctor'", (did,))
        if not cur.fetchone():
            print(T("Doctor not found. Would you like to register as a new doctor? (Y/N): ", "डॉक्टर नहीं मिला। क्या आप नए डॉक्टर के रूप में पंजीकरण करना चाहेंगे? (Y/N): "))
            register_choice = input().upper()
            if register_choice == "Y":
                # Register as new doctor
                try:
                    name = input(T("Enter your Name: ", "अपना नाम दर्ज करें: "))
                    cur.execute("SELECT dept_id, name FROM departments")
                    departments = cur.fetchall()
                    if not departments:
                        print(T("No departments available. Please add departments first.", "कोई विभाग उपलब्ध नहीं। कृपया पहले विभाग जोड़ें।"))
                        con.close()
                        return
                    
                    for dept in departments:
                        print(f"{dept[0]}: {dept[1]}")
                    
                    while True:
                        try:
                            did_new = int(input(T("Select Department ID: ", "विभाग आईडी चुनें: ")))
                            cur.execute("SELECT 1 FROM departments WHERE dept_id = %s", (did_new,))
                            if cur.fetchone() is None:
                                print(T("Invalid Department ID. Please try again.", "अमान्य विभाग आईडी। पुनः प्रयास करें।"))
                                continue
                            break
                        except ValueError:
                            print(T("Please enter a valid number.", "कृपया एक मान्य संख्या दर्ज करें।"))
                    
                    cur.execute("INSERT INTO staff(name, role, department_id) VALUES(%s, 'Doctor', %s)", (name, did_new))
                    con.commit()
                    print(T("You have been registered as a new doctor. Your Doctor ID is the new staff ID.", "आप नए डॉक्टर के रूप में पंजीकृत हो गए हैं। आपका डॉक्टर आईडी नया स्टाफ आईडी है।"))
                    # Optionally, retrieve and display the new ID
                    cur.execute("SELECT LAST_INSERT_ID()")
                    new_did = cur.fetchone()[0]
                    print(T(f"Your new Doctor ID is: {new_did}", f"आपका नया डॉक्टर आईडी है: {new_did}"))
                    did = new_did  # Set did to the new ID for further use
                except ValueError:
                    print(T("Invalid input. Please enter valid data.", "अमान्य इनपुट। कृपया मान्य डेटा दर्ज करें।"))
                    con.close()
                    return
                except mysql.connector.Error as e:
                    print(f"Database error: {e}")
                    con.rollback()
                    con.close()
                    return
            else:
                print(T("Registration declined. Exiting.", "पंजीकरण अस्वीकार किया गया। बाहर निकल रहे हैं।"))
                con.close()
                return
        
        while True:
            print("\n---", T("Doctor Management", "डॉक्टर प्रबंधन"), "---")
            print("1.", T("View My Schedule/Appointments", "मेरा शेड्यूल/अपॉइंटमेंट देखें"))
            print("2.", T("Update Availability", "उपलब्धता अपडेट करें"))
            print("3.", T("Manage Appointments", "अपॉइंटमेंट प्रबंधित करें"))
            print("4.", T("Add New Doctor", "नया डॉक्टर जोड़ें"))
            print("5.", T("Back to Main Menu", "मुख्य मेनू पर लौटें"))
            
            choice = input(T("Enter choice: ", "विकल्प दर्ज करें: "))
            
            if choice == "1":
                # View schedule/appointments
                cur.execute("SELECT a.appointment_id, p.name, a.appointment_date FROM appointments a JOIN patients p ON a.patient_id = p.patient_id WHERE a.doctor_id = %s ORDER BY a.appointment_date", (did,))
                apps = cur.fetchall()
                if not apps:
                    print(T("No appointments found.", "कोई अपॉइंटमेंट नहीं मिला।"))
                else:
                    print(T("Your Appointments:", "आपके अपॉइंटमेंट:"))
                    for app in apps:
                        print(f"ID: {app[0]} | Patient: {app[1]} | Date: {app[2]}")
            
            elif choice == "2":
                # Update availability (simple text update; assumes a 'availability' column in staff table)
                availability = input(T("Update your availability status: ", "अपनी उपलब्धता स्थिति अपडेट करें: "))
                cur.execute("UPDATE staff SET availability = %s WHERE staff_id = %s", (availability, did))
                con.commit()
                print(T("Availability updated.", "उपलब्धता अपडेट की गई।"))
            
            elif choice == "3":
                # Manage appointments (e.g., cancel or reschedule)
                cur.execute("SELECT a.appointment_id, p.name, a.appointment_date FROM appointments a JOIN patients p ON a.patient_id = p.patient_id WHERE a.doctor_id = %s AND a.appointment_date >= CURDATE() ORDER BY a.appointment_date", (did,))
                apps = cur.fetchall()
                if not apps:
                    print(T("No upcoming appointments.", "कोई आगामी अपॉइंटमेंट नहीं।"))
                    continue
                for app in apps:
                    print(f"{app[0]}: {app[1]} on {app[2]}")
                
                try:
                    aid = int(input(T("Enter Appointment ID to manage (e.g., cancel): ", "प्रबंधित करने के लिए अपॉइंटमेंट आईडी दर्ज करें (जैसे, रद्द करें): ")))
                    action = input(T("Enter action (cancel/reschedule): ", "कार्रवाई दर्ज करें (cancel/reschedule): ")).lower()
                    if action == "cancel":
                        cur.execute("DELETE FROM appointments WHERE appointment_id = %s AND doctor_id = %s", (aid, did))
                        con.commit()
                        print(T("Appointment canceled.", "अपॉइंटमेंट रद्द किया गया।"))
                    elif action == "reschedule":
                        new_date = input(T("New date (YYYY-MM-DD): ", "नई तिथि (YYYY-MM-DD): "))
                        cur.execute("UPDATE appointments SET appointment_date = %s WHERE appointment_id = %s AND doctor_id = %s", (new_date, aid, did))
                        con.commit()
                        print(T("Appointment rescheduled.", "अपॉइंटमेंट पुनर्निर्धारित किया गया।"))
                    else:
                        print(T("Invalid action.", "अमान्य कार्रवाई।"))
                except ValueError:
                    print(T("Invalid input.", "अमान्य इनपुट।"))
                except mysql.connector.Error as e:
                    print(f"Database error: {e}")
                    con.rollback()
            
            elif choice == "4":
                # Add New Doctor
                try:
                    name = input(T("Enter Doctor Name: ", "डॉक्टर का नाम दर्ज करें: "))
                    cur.execute("SELECT dept_id, name FROM departments")
                    departments = cur.fetchall()
                    if not departments:
                        print(T("No departments available. Please add departments first.", "कोई विभाग उपलब्ध नहीं। कृपया पहले विभाग जोड़ें।"))
                        continue
                    
                    for dept in departments:
                        print(f"{dept[0]}: {dept[1]}")
                    
                    while True:
                        try:
                            did_new = int(input(T("Select Department ID for the new doctor: ", "नए डॉक्टर के लिए विभाग आईडी चुनें: ")))
                            cur.execute("SELECT 1 FROM departments WHERE dept_id = %s", (did_new,))
                            if cur.fetchone() is None:
                                print(T("Invalid Department ID. Please try again.", "अमान्य विभाग आईडी। पुनः प्रयास करें।"))
                                continue
                            break
                        except ValueError:
                            print(T("Please enter a valid number.", "कृपया एक मान्य संख्या दर्ज करें।"))
                    
                    cur.execute("INSERT INTO staff(name, role, department_id) VALUES(%s, 'Doctor', %s)", (name, did_new))
                    con.commit()
                    print(T("New doctor added successfully.", "नया डॉक्टर सफलतापूर्वक जोड़ा गया।"))
                
                except ValueError:
                    print(T("Invalid input. Please enter valid data.", "अमान्य इनपुट। कृपया मान्य डेटा दर्ज करें।"))
                except mysql.connector.Error as e:
                    print(f"Database error: {e}")
                    con.rollback()
            
            elif choice == "5":
                break
            else:
                print(T("Invalid choice.", "गलत विकल्प।"))
    
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        if 'con' in locals() and con.is_connected():
            con.close()

# ------------------------------
# VIEW PATIENT HISTORY
# ------------------------------
def view_patient_history():
    """
    Displays a patient's history including appointments, surgeries, prescriptions, lab tests, and vitals.
    """
    try:
        con = db()
        cur = con.cursor()
        try:
            pid = int(input(T("Enter Patient ID to view history: ", "इतिहास देखने के लिए रोगी आईडी दर्ज करें: ")))
        except ValueError:
            print(T("Invalid Patient ID. Please enter a number.", "अमान्य रोगी आईडी। कृपया एक संख्या दर्ज करें।"))
            return
        
        cur.execute("SELECT name FROM patients WHERE patient_id = %s", (pid,))
        patient = cur.fetchone()
        if not patient:
            print(T("Patient not found.", "रोगी नहीं मिला।"))
            return
        
        print(T(f"\n--- History for Patient: {patient[0]} (ID: {pid}) ---", f"\n--- रोगी के लिए इतिहास: {patient[0]} (आईडी: {pid}) ---"))
        
        # Appointments
        cur.execute("SELECT appointment_date, doctor_id FROM appointments WHERE patient_id = %s ORDER BY appointment_date DESC", (pid,))
        apps = cur.fetchall()
        print(T("\nAppointments:", "\nअपॉइंटमेंट:"))
        if apps:
            for app in apps:
                cur.execute("SELECT name FROM staff WHERE staff_id = %s", (app[1],))
                doc = cur.fetchone()
                print(f"Date: {app[0]} | Doctor: {doc[0] if doc else 'N/A'}")
        else:
            print(T("No appointments found.", "कोई अपॉइंटमेंट नहीं मिला।"))
        
        # Surgeries
        cur.execute("SELECT surgery_type, date FROM surgeries WHERE patient_id = %s ORDER BY date DESC", (pid,))
        surgeries = cur.fetchall()
        print(T("\nSurgeries:", "\nसर्जरी:"))
        if surgeries:
            for surg in surgeries:
                print(f"Type: {surg[0]} | Date: {surg[1]}")
        else:
            print(T("No surgeries found.", "कोई सर्जरी नहीं मिली।"))
        
        # Prescriptions
        cur.execute("SELECT medicines, notes, date FROM prescriptions WHERE patient_id = %s ORDER BY date DESC", (pid,))
        pres = cur.fetchall()
        print(T("\nPrescriptions:", "\nप्रिस्क्रिप्शन:"))
        if pres:
            for p in pres:
                print(f"Medicines: {p[0]} | Notes: {p[1]} | Date: {p[2]}")
        else:
            print(T("No prescriptions found.", "कोई प्रिस्क्रिप्शन नहीं मिला।"))
        
        # Lab Tests
        cur.execute("SELECT t.name, r.result, r.test_date FROM patient_lab_results r JOIN lab_tests t ON r.test_id = t.test_id WHERE r.patient_id = %s ORDER BY r.test_date DESC", (pid,))
        tests = cur.fetchall()
        print(T("\nLab Tests:", "\nलैब टेस्ट:"))
        if tests:
            for test in tests:
                print(f"Test: {test[0]} | Result: {test[1]} | Date: {test[2]}")
        else:
            print(T("No lab tests found.", "कोई लैब टेस्ट नहीं मिला।"))
        
        # Vitals
        cur.execute("SELECT temperature, heart_rate, blood_pressure, respiratory_rate, date_recorded FROM patient_vitals WHERE patient_id = %s ORDER BY date_recorded DESC", (pid,))
        vitals = cur.fetchall()
        print(T("\nVitals:", "\nवाइटल्स:"))
        if vitals:
            for vit in vitals:
                print(f"Temp: {vit[0]}°C | HR: {vit[1]} bpm | BP: {vit[2]} | Resp: {vit[3]} | Date: {vit[4]}")
        else:
            print(T("No vitals found.", "कोई वाइटल्स नहीं मिला।"))
        
    except mysql.connector.Error as e:
        print(T(f"Database error: {e}", f"डेटाबेस त्रुटि: {e}"))
    except Exception as e:
        print(T(f"An unexpected error occurred: {e}", f"एक अप्रत्याशित त्रुटि हुई: {e}"))
    finally:
        if 'con' in locals() and con.is_connected():
            con.close()

# =====================================================
# CHATBOT
# =====================================================
def hospital_chatbot(patient_id=None):
    """
    Chatbot that:
    - Asks patient symptoms
    - Suggests medicine
    - Automatically logs vitals if relevant
    - Performs hospital tasks
    """
    print("\n" + T("Hello! I am your hospital assistant.", "नमस्ते! मैं आपका हॉस्पिटल असिस्टेंट हूँ।"))

    while True:
        print("\n" + T("Please tell me your symptoms (or type 'exit' to quit):", 
                      "कृपया अपने लक्षण बताएं (या 'exit' टाइप करें बाहर निकलने के लिए):"))
        symptom_input = input(T("You: ", "आप: ")).strip().lower()

        if symptom_input in ["exit", "quit", "bye", "बाहर निकलें"]:
            print(T("Chatbot: Goodbye! Take care.", "चैटबोट: अलविदा! अपना ख्याल रखें।"))
            break

        # Symptom-based medicine suggestion & logging
        if "fever" in symptom_input or "temperature" in symptom_input or "बुखार" in symptom_input:
            medicine = "Paracetamol 500mg"
            advice = T(
                f"You have a fever. You may take {medicine}. Consult your doctor if persistent.",
                f"आपको बुखार है। आप {medicine} ले सकते हैं। अगर लक्षण बने रहें तो डॉक्टर से सलाह लें।"
            )
            print(advice)
            
        elif "headache" in symptom_input or "सिर दर्द" in symptom_input:
            medicine = "Ibuprofen or Paracetamol"
            advice = T(
                f"For headache, you may take {medicine}. Stay hydrated.",
                f"सिर दर्द के लिए, आप {medicine} ले सकते हैं। पर्याप्त पानी पिएँ।"
            )
            print(advice)

        elif "cold" in symptom_input or "flu" in symptom_input or "जुकाम" in symptom_input:
            medicine = "Antihistamines if needed"
            advice = T(
                f"Rest, fluids, and {medicine}.",
                f"आराम करें, तरल पदार्थ पिएँ और जरूरत पर {medicine} लें।"
            )
            print(advice)
            
        elif "cough" in symptom_input or "खाँसी" in symptom_input:
            medicine = "Cough syrup if persistent"
            advice = T(
                f"Drink warm fluids. Use {medicine}.",
                f"गर्म पेय पिएँ। अगर लगातार खाँसी हो तो {medicine} लें।"
            )
            print(advice)

        # Task-oriented functionality
        elif "book appointment" in symptom_input or "अपॉइंटमेंट" in symptom_input:
            book_appointment()
        elif "view vitals" in symptom_input or "वाइटल्स" in symptom_input:
            if patient_id:
                view_vitals(patient_id)
            else:
                print(T("Patient ID not available.", "रोगी आईडी उपलब्ध नहीं।"))
        elif "view bills" in symptom_input or "बिल" in symptom_input:
            view_patient_bill()
        elif "book lab test" in symptom_input or "लैब टेस्ट" in symptom_input:
            manage_lab_tests()
        elif "help" in symptom_input or "सहायता" in symptom_input:
            print(T(
                "You can ask me to suggest medicines, book appointments, view vitals, view bills, or book lab tests.", 
                "आप मुझसे दवा सुझाव, अपॉइंटमेंट बुक, वाइटल्स देखें, बिल देखें या लैब टेस्ट बुक करने के लिए पूछ सकते हैं।"))

        else:
            print(T(
                "Sorry, I cannot understand. Please describe your symptoms or task in detail.", 
                "क्षमा करें, मैं समझ नहीं पा रहा। कृपया अपने लक्षण या कार्य विस्तार से बताएं।"))

# =====================================================
# FEEDBACK AND RATING SYSTEM
# =====================================================
def manage_feedback():
    try:
        con = db()
        cur = con.cursor()
        
        while True:
            print("\n---", T("Feedback and Rating System", "फीडबैक और रेटिंग सिस्टम"), "---")
            print("1.", T("Submit Feedback for Doctor", "डॉक्टर के लिए फीडबैक सबमिट करें"))
            print("2.", T("Submit Feedback for Hospital Services", "हॉस्पिटल सेवाओं के लिए फीडबैक सबमिट करें"))
            print("3.", T("View Feedback for a Doctor", "डॉक्टर के लिए फीडबैक देखें"))
            print("4.", T("Back to Main Menu", "मुख्य मेनू पर लौटें"))
            
            choice = input(T("Enter choice: ", "विकल्प दर्ज करें: "))
            
            if choice == "1":
                # Submit feedback for a doctor
                try:
                    pid = int(input(T("Enter your Patient ID: ", "अपना रोगी आईडी दर्ज करें: ")))
                    cur.execute("SELECT 1 FROM patients WHERE patient_id = %s", (pid,))
                    if not cur.fetchone():
                        print(T("Patient not found.", "रोगी नहीं मिला।"))
                        continue
                    
                    cur.execute("SELECT staff_id, name FROM staff WHERE role = 'Doctor'")
                    docs = cur.fetchall()
                    if not docs:
                        print(T("No doctors found.", "कोई डॉक्टर नहीं मिला।"))
                        continue
                    for d in docs:
                        print(f"{d[0]}: {d[1]}")
                    
                    did = int(input(T("Select Doctor ID: ", "डॉक्टर आईडी चुनें: ")))
                    cur.execute("SELECT 1 FROM staff WHERE staff_id = %s AND role = 'Doctor'", (did,))
                    if not cur.fetchone():
                        print(T("Doctor not found.", "डॉक्टर नहीं मिला।"))
                        continue
                    
                    rating = int(input(T("Rate the doctor (1-5): ", "डॉक्टर को रेट करें (1-5): ")))
                    if not (1 <= rating <= 5):
                        print(T("Invalid rating. Please enter 1-5.", "अमान्य रेटिंग। कृपया 1-5 दर्ज करें।"))
                        continue
                    
                    comment = input(T("Enter your comment: ", "अपना कमेंट दर्ज करें: "))
                    cur.execute("INSERT INTO feedback(patient_id, doctor_id, rating, comment, date) VALUES(%s, %s, %s, %s, %s)",
                                (pid, did, rating, comment, datetime.now()))
                    con.commit()
                    print(T("Feedback submitted successfully.", "फीडबैक सफलतापूर्वक सबमिट किया गया।"))
                
                except ValueError:
                    print(T("Invalid input. Please enter numbers where required.", "अमान्य इनपुट। कृपया आवश्यक स्थानों पर संख्या दर्ज करें।"))
                except mysql.connector.Error as e:
                    print(f"Database error: {e}")
                    con.rollback()
            
            elif choice == "2":
                # Submit feedback for hospital services (no doctor_id)
                try:
                    pid = int(input(T("Enter your Patient ID: ", "अपना रोगी आईडी दर्ज करें: ")))
                    cur.execute("SELECT 1 FROM patients WHERE patient_id = %s", (pid,))
                    if not cur.fetchone():
                        print(T("Patient not found.", "रोगी नहीं मिला।"))
                        continue
                    
                    rating = int(input(T("Rate hospital services (1-5): ", "हॉस्पिटल सेवाओं को रेट करें (1-5): ")))
                    if not (1 <= rating <= 5):
                        print(T("Invalid rating. Please enter 1-5.", "अमान्य रेटिंग। कृपया 1-5 दर्ज करें।"))
                        continue
                    
                    comment = input(T("Enter your comment: ", "अपना कमेंट दर्ज करें: "))
                    cur.execute("INSERT INTO feedback(patient_id, rating, comment, date) VALUES(%s, %s, %s, %s)",
                                (pid, rating, comment, datetime.now()))
                    con.commit()
                    print(T("Feedback submitted successfully.", "फीडबैक सफलतापूर्वक सबमिट किया गया।"))
                
                except ValueError:
                    print(T("Invalid input. Please enter numbers where required.", "अमान्य इनपुट। कृपया आवश्यक स्थानों पर संख्या दर्ज करें।"))
                except mysql.connector.Error as e:
                    print(f"Database error: {e}")
                    con.rollback()
            
            elif choice == "3":
                # View feedback for a doctor
                try:
                    cur.execute("SELECT staff_id, name FROM staff WHERE role = 'Doctor'")
                    docs = cur.fetchall()
                    if not docs:
                        print(T("No doctors found.", "कोई डॉक्टर नहीं मिला।"))
                        continue
                    for d in docs:
                        print(f"{d[0]}: {d[1]}")
                    
                    did = int(input(T("Select Doctor ID to view feedback: ", "फीडबैक देखने के लिए डॉक्टर आईडी चुनें: ")))
                    cur.execute("SELECT f.rating, f.comment, f.date, p.name FROM feedback f JOIN patients p ON f.patient_id = p.patient_id WHERE f.doctor_id = %s ORDER BY f.date DESC", (did,))
                    feedbacks = cur.fetchall()
                    if not feedbacks:
                        print(T("No feedback found for this doctor.", "इस डॉक्टर के लिए कोई फीडबैक नहीं मिला।"))
                    else:
                        print(T(f"\nFeedback for Doctor ID {did}:", f"डॉक्टर आईडी {did} के लिए फीडबैक:"))
                        for fb in feedbacks:
                            print(f"Rating: {fb[0]} | Comment: {fb[1]} | Date: {fb[2]} | Patient: {fb[3]}")
                
                except ValueError:
                    print(T("Invalid input. Please enter a number.", "अमान्य इनपुट। कृपया एक संख्या दर्ज करें।"))
                except mysql.connector.Error as e:
                    print(f"Database error: {e}")
            
            elif choice == "4":
                break
            else:
                print(T("Invalid choice.", "गलत विकल्प।"))
    
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        if 'con' in locals() and con.is_connected():
            con.close()

# =====================================================
# EMERGENCY SERVICES
# =====================================================
def emergency_services():
    try:
        con = db()
        cur = con.cursor()
        
        while True:
            print("\n---", T("Emergency Services", "आपातकालीन सेवाएँ"), "---")
            print("1.", T("Emergency ICU Admission", "आपातकालीन ICU दाखिला"))
            print("2.", T("Ambulance Dispatch", "एम्बुलेंस डिस्पैच"))
            print("3.", T("Back to Main Menu", "मुख्य मेनू पर लौटें"))
            
            choice = input(T("Enter choice: ", "विकल्प दर्ज करें: "))
            
            if choice == "1":
                # Emergency ICU admission
                try:
                    pid = int(input(T("Enter Patient ID for emergency admission: ", "आपातकालीन दाखिले के लिए रोगी आईडी दर्ज करें: ")))
                    cur.execute("SELECT 1 FROM patients WHERE patient_id = %s", (pid,))
                    if not cur.fetchone():
                        print(T("Patient not found.", "रोगी नहीं मिला।"))
                        continue
                    
                    # Check if already admitted
                    cur.execute("SELECT 1 FROM icu_records WHERE patient_id = %s AND discharge_date IS NULL", (pid,))
                    if cur.fetchone():
                        print(T("Patient already in ICU.", "रोगी पहले से ICU में है।"))
                        continue
                    
                    cur.execute("INSERT INTO icu_records(patient_id, admit_date) VALUES(%s, %s)", (pid, datetime.now()))
                    con.commit()
                    print(T("Emergency ICU admission recorded.", "आपातकालीन ICU दाखिला दर्ज किया गया।"))
                
                except ValueError:
                    print(T("Invalid Patient ID.", "अमान्य रोगी आईडी।"))
                except mysql.connector.Error as e:
                    print(f"Database error: {e}")
                    con.rollback()
            
            elif choice == "2":
                # Ambulance dispatch simulation
                location = input(T("Enter pickup location: ", "पिकअप स्थान दर्ज करें: "))
                destination = input(T("Enter destination (e.g., hospital): ", "गंतव्य दर्ज करें (जैसे, हॉस्पिटल): "))
                print(T(f"Ambulance dispatched from {location} to {destination}. ETA: 10 minutes.", f"एम्बुलेंस {location} से {destination} तक डिस्पैच की गई। ETA: 10 मिनट।"))
                # In a real system, log to a table like 'ambulance_dispatches'
            
            elif choice == "3":
                break
            else:
                print(T("Invalid choice.", "गलत विकल्प।"))
    
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        if 'con' in locals() and con.is_connected():
            con.close()
            
# ================================
# REPORTS & SUMMARY
# ================================
def full_hospital_summary():
    try:
        con = db()
        cur = con.cursor()

        cur.execute("SELECT COUNT(*) FROM patients")
        patients = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM staff")
        staff = cur.fetchone()[0]

        cur.execute("SELECT sum(total_count) FROM beds")
        beds = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM appointments")
        appointments = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM surgeries")
        surgeries = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM lab_tests")
        lab_tests = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM pharmacy")
        medicines = cur.fetchone()[0]

        print(T(
            f"\nTotal Patients: {patients}\nStaff: {staff}\nBeds: {beds}\nAppointments: {appointments}\nSurgeries: {surgeries}\nLab Tests: {lab_tests}\nMedicines: {medicines}",
            f"कुल रोगी: {patients}\nस्टाफ: {staff}\nबिस्तर: {beds}\nअपॉइंटमेंट: {appointments}\nसर्जरी: {surgeries}\nलैब टेस्ट: {lab_tests}\nदवाइयाँ: {medicines}"
        ))

    except mysql.connector.Error as e:
        print(T(f"Database error: {e}", f"डेटाबेस त्रुटि: {e}"))
    except Exception as e:
        print(T(f"An unexpected error occurred: {e}", f"एक अप्रत्याशित त्रुटि हुई: {e}"))
    finally:
        if 'con' in locals() and con.is_connected():
            con.close()

def daily_summary():
    try:
        con = db()
        cur = con.cursor()
        today = datetime.now().date()
        cur.execute("SELECT COUNT(*) FROM appointments WHERE DATE(appointment_date)=%s", (today,))
        app_today = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM patients WHERE DATE(reg_date)=%s", (today,))
        patients_today = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM surgeries WHERE DATE(date)=%s", (today,))
        surgeries_today = cur.fetchone()[0]

        cur.execute("SELECT SUM(amount) FROM bills WHERE DATE(date)=%s", (today,))
        earnings = cur.fetchone()[0] or 0

        cur.execute("SELECT COUNT(*) FROM attendance WHERE DATE(date)=%s AND status='P'", (today,))
        staff_present = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM attendance WHERE DATE(date)=%s AND status='A'", (today,))
        staff_absent = cur.fetchone()[0]

        print(T(
            f"\nToday's Summary:\nAppointments: {app_today}\nNew Patients: {patients_today}\nSurgeries: {surgeries_today}\nEarnings: ₹{earnings}\nStaff Present: {staff_present}\nAbsent: {staff_absent}",
            f"आज का सारांश: अपॉइंटमेंट: {app_today}\nनए रोगी: {patients_today}\nसर्जरी: {surgeries_today}\nकमाई: ₹{earnings}\n स्टाफ उपस्थित: {staff_present}\n अनुपस्थित: {staff_absent}"
        ))

    except mysql.connector.Error as e:
        print(T(f"Database error: {e}", f"डेटाबेस त्रुटि: {e}"))
    except Exception as e:
        print(T(f"An unexpected error occurred: {e}", f"एक अप्रत्याशित त्रुटि हुई: {e}"))
    finally:
        if 'con' in locals() and con.is_connected():
            con.close()

def hospital_facilities():
    print(T("\n--- Hospital Facilities ---\n","--- अस्पताल की सुविधाएँ ---\n"))
    facilities = [
        T("Emergency Services","आपातकालीन सेवाएँ"),
        T("24/7 OPD & ICU","24/7 OPD और ICU"),
        T("Advanced Surgery Rooms","उन्नत सर्जरी कक्ष"),
        T("Pharmacy & Blood Bank","फार्मेसी और ब्लड बैंक"),
        T("Laboratory Services","प्रयोगशाला सेवाएँ"),
        T("Canteen & Cafeteria","कैंटीन और कैफेटेरिया"),
        T("Ambulance Services","एम्बुलेंस सेवाएँ")
    ]
    for f in facilities:
        print("-", f)
    
    print(T("\n--- Important Helpline Numbers ---","--- महत्वपूर्ण हेल्पलाइन नंबर ---"))
    helplines = {
        T("Emergency","आपातकालीन"): "108",
        T("OPD Appointments","OPD अपॉइंटमेंट"): "1800-123-456",
        T("Ambulance","एम्बुलेंस"): "102",
        T("Blood Bank","ब्लड बैंक"): "1800-789-123",
        T("Canteen","कैंटीन"): "1800-555-000"
    }
    for h, num in helplines.items():
        print(f"{h}: {num}")

# ------------------------------
# ADMINISTRATION MENU
# -----------------------------
def administration_menu():
    while True:
        print("\n---", T("Administration Menu", "प्रशासन मेनू"), "---")
        print("1.", T("Manage Departments", "विभाग प्रबंधन"))
        print("2.", T("Manage Staff", "स्टाफ प्रबंधन"))
        print("3.", T("Hospital Summary", "अस्पताल सारांश"))
        print("4.", T("Daily Summary", "दैनिक सारांश"))
        print("5.", T("Attendance", "उपस्थिति"))
        print("6.", T("Manage Beds", "बिस्तर प्रबंधन"))
        print("7.", T("Generate Salaries", "वेतन जनरेट करें"))
        print("8.", T("Back to Main Menu", "मुख्य मेनू पर लौटें"))  

        choice = input(T("Enter choice: ", "विकल्प दर्ज करें: "))

        try:
            if choice == "1":
                manage_departments_full()
            elif choice == "2":
                manage_staff()
            elif choice == "3":
                full_hospital_summary()
            elif choice == "4":
                daily_summary()
            elif choice == "5":
                attendance()
            elif choice == "6":
                manage_beds()
            elif choice == "7":
                generate_salary()
            elif choice == "8": 
                break
            else:
                print(T("Invalid choice.", "गलत विकल्प।"))
        except Exception as e:
            print(T(f"Error: {e}", f"त्रुटि: {e}"))
            
# -----------------------------
# DOCTOR MENU
# -----------------------------
def doctor_menu():
    while True:
        print("\n---", T("Doctor Menu", "डॉक्टर मेनू"), "---")
        print("1.", T("Manage Patients", "रोगी प्रबंधन"))
        print("2.", T("Register Surgery", "सर्जरी पंजीकरण"))
        print("3.", T("Prescription", "प्रिस्क्रिप्शन"))
        print("4.", T("Lab Tests", "लैब टेस्ट"))
        print("5.", T("Add/View Patient Vitals", "रोगी की महत्वपूर्ण जानकारी जोड़ें/देखें"))
        print("6.", T("View Patient History", "रोगी इतिहास देखें"))
        print("7.", T("Doctor Management", "डॉक्टर प्रबंधन"))  
        print("8.", T("Admit Patient", "रोगी दाखिला"))  
        print("9.", T("Discharge Patient", "रोगी डिस्चार्ज"))  
        print("10.", T("Back to Main Menu", "मुख्य मेनू पर लौटें")) 

        choice = input(T("Enter choice: ", "विकल्प दर्ज करें: "))

        try:
            if choice == "1":
                manage_patients()
            elif choice == "2":
                register_surgery()
            elif choice == "3":
                add_prescription()
            elif choice == "4":
                manage_lab_tests()
            elif choice == "5":
                try:
                    pid = int(input(T("Enter Patient ID: ", "रोगी आईडी दर्ज करें: ")))
                except ValueError:
                    print(T("Invalid Patient ID.", "अमान्य रोगी आईडी।"))
                    continue
                while True:
                    print("\n1.", T("Add Vitals", "वाइटल्स जोड़ें"))
                    print("2.", T("View Vitals", "वाइटल्स देखें"))
                    print("3.", T("Back", "वापस"))
                    vit_choice = input(T("Enter choice: ", "विकल्प दर्ज करें: "))
                    if vit_choice == "1":
                        add_vitals(pid)
                    elif vit_choice == "2":
                        view_vitals(pid)
                    elif vit_choice == "3":
                        break
                    else:
                        print(T("Invalid choice.", "गलत विकल्प।"))
            elif choice == "6":
                view_patient_history()
            elif choice == "7":  
                doctor_management()
            elif choice == "8":  # New: Admit Patient
                area = input(T("Enter area (opd/icu): ", "क्षेत्र दर्ज करें (opd/icu): ")).lower()
                if area in ['opd', 'icu']:
                    admit_patient(area)
                else:
                    print(T("Invalid area. Choose 'opd' or 'icu'.", "अमान्य क्षेत्र। 'opd' या 'icu' चुनें।"))
            elif choice == "9":  # New: Discharge Patient
                area = input(T("Enter area (opd/icu): ", "क्षेत्र दर्ज करें (opd/icu): ")).lower()
                if area in ['opd', 'icu']:
                    discharge_patient(area)
                else:
                    print(T("Invalid area. Choose 'opd' or 'icu'.", "अमान्य क्षेत्र। 'opd' या 'icu' चुनें।"))
            elif choice == "10":  # Updated: Back
                break
            else:
                print(T("Invalid choice.", "गलत विकल्प।"))
        except Exception as e:
            print(T(f"Error: {e}", f"त्रुटि: {e}"))
            
# -----------------------------
# BILLING MENU
# -----------------------------
def billing_menu():
    while True:
        print("\n---", T("Billing Menu", "बिलिंग मेनू"), "---")
        print("1.", T("Generate Bill", "बिल बनाएं"))
        print("2.", T("View Patient Bill", "रोगी बिल देखें"))
        print("3.", T("Back to Main Menu", "मुख्य मेनू पर लौटें"))

        choice = input(T("Enter choice: ", "विकल्प दर्ज करें: "))

        try:
            if choice == "1":
                generate_bill()
            elif choice == "2":
                view_patient_bill()
            elif choice == "3":
                break
            else:
                print(T("Invalid choice.", "गलत विकल्प।"))
        except Exception as e:
            print(T(f"Error: {e}", f"त्रुटि: {e}"))
            
# -----------------------------
# PATIENT MENU
# -----------------------------
def patient_menu():
    patient_id = None  
    while True:
        print("\n---", T("Patient Menu", "रोगी मेनू"), "---")
        print("1.", T("Book Appointment", "अपॉइंटमेंट बुक करें"))
        print("2.", T("View Vitals", "वाइटल्स देखें"))
        print("3.", T("View Bills", "बिल देखें"))
        print("4.", T("Book Lab Test", "लैब टेस्ट बुक करें"))
        print("5.", T("Chatbot / Help", "चैटबोट / सहायता"))
        print("6.", T("View Past History", "पिछला इतिहास देखें"))
        print("7.", T("Submit Feedback", "फीडबैक सबमिट करें"))
        print("8.", T("Back", "वापस"))

        choice = input(T("Enter choice: ", "विकल्प दर्ज करें: "))

        try:
            if choice == "1":
                book_appointment()
            elif choice == "2":
                try:
                    pid = int(input(T("Enter Patient ID: ", "रोगी आईडी दर्ज करें: ")))
                    patient_id = pid  
                except ValueError:
                    print(T("Invalid Patient ID.", "अमान्य रोगी आईडी।"))
                    continue
                while True:
                    print("\n1.", T("View Vitals", "वाइटल्स देखें"))
                    print("2.", T("Back", "वापस"))
                    vit_choice = input(T("Enter choice: ", "विकल्प दर्ज करें: "))
                    if vit_choice == "1":
                        view_vitals(pid)
                    elif vit_choice == "2":
                        break
                    else:
                        print(T("Invalid choice.", "गलत विकल्प।"))
            elif choice == "3":
                view_patient_bill()
            elif choice == "4":
                manage_lab_tests()
            elif choice == "5":
                hospital_chatbot(patient_id)
            elif choice == "6":
                view_patient_history()
            elif choice == "7":
                manage_feedback()  
            elif choice == "8":
                break
            else:
                print(T("Invalid choice, try again.", "गलत विकल्प, पुनः प्रयास करें।"))
        except Exception as e:
            print(T(f"Error: {e}", f"त्रुटि: {e}"))
            
# -----------------------------
# HOSPITAL STAFF MENU 
# -----------------------------
def hospital_staff_menu():
    while True:
        print("\n---", T("Hospital Staff Menu", "अस्पताल कर्मचारी मेनू"), "---")
        print("1.", T("Administration", "प्रशासन"))
        print("2.", T("Doctors", "डॉक्टर"))
        print("3.", T("Billing", "बिलिंग"))
        print("4.", T("Pharmacy", "फार्मेसी"))
        print("5.", T("Canteen", "कैंटीन"))
        print("6.", T("Emergency Services", "आपातकालीन सेवाएँ"))
        print("7.", T("Blood Bank", "रक्त बैंक"))
        print("8.", T("Feedback Management", "फीडबैक प्रबंधन"))
        print("9.", T("Search Staff", "स्टाफ खोजें"))
        print("10.", T("Search Patient", "रोगी खोजें"))
        print("11.", T("Doctor Management", "डॉक्टर प्रबंधन"))
        print("12.", T("Back to Main Menu", "मुख्य मेनू पर लौटें"))

        choice = input(T("Enter choice: ", "विकल्प दर्ज करें: "))

        try:
            if choice == "1":
                print("************      ADMINISTRATION      *************")
                administration_menu()
            elif choice == "2":
                print("*************    DOCTOR     **************")
                doctor_menu()
            elif choice == "3":
                print("*************    BILLING   *************")
                billing_menu()
            elif choice == "4":
                print("*************    PHARMACY   *************")
                pharmacy_management()
            elif choice == "5":
                print("*************    CANTEEN   *************")
                canteen_sales()
            elif choice == "6":
                emergency_services()
            elif choice == "7":
                blood_bank_management()
            elif choice == "8":
                manage_feedback()
            elif choice == "9":
                search_staff()
            elif choice == "10":
                search_patient()
            elif choice == "11":
                doctor_management()
            elif choice == "12":
                break
            else:
                print(T("Invalid choice, try again.", "गलत विकल्प, पुनः प्रयास करें।"))
        except Exception as e:
            print(T(f"Error: {e}", f"त्रुटि: {e}"))

# -----------------------------
# MAIN MENU 
# -----------------------------
def main_menu():
    print("**********************************************************************")
    print(T(f"Welcome to HEALTH-SOFT SMART HOSPITAL MANAGEMENT SYSTEM. Today is {datetime.now().date()}, {datetime.now().strftime('%H:%M:%S')}",
            f"सिटी केयर हॉस्पिटल में आपका स्वागत है। आज की तिथि {datetime.now().date()}, समय {datetime.now().strftime('%H:%M:%S')}"))
    print("**********************************************************************")
    print(T("Hospital Facilities", "अस्पताल सुविधाएं"))
    print("**********************************************************************")
    hospital_facilities()
    print("**********************************************************************")
    print(T("LOGGING IN", "लॉगिंग-इन"))
    print("**********************************************************************")
    
    # Call login and get role and user_id
    role, user_id = login()
    
    if role is None:
        print(T("Login failed. Exiting.", "लॉगिन विफल। बाहर निकल रहे हैं।"))
        return
    
    # Based on role, direct to the appropriate menu
    while True:
        if role == 'staff':
            print("*************    HOSPITAL STAFF   *************")
            hospital_staff_menu()
        elif role == 'patient':
            print("*************    PATIENT   *************")
            patient_menu()
        
        # Option to access General Services (accessible to all logged-in users)
        print("\n---", T("General Services", "सामान्य सेवाएँ"), "---")
        print("1.", T("Emergency Services", "आपातकालीन सेवाएँ"))
        print("2.", T("Feedback Management", "फीडबैक प्रबंधन"))
        print("3.", T("Hospital Facilities", "अस्पताल सुविधाएँ"))
        print("4.", T("Logout and Exit", "लॉगआउट और बाहर निकलें"))
        
        gen_choice = input(T("Enter choice: ", "विकल्प दर्ज करें: "))
        if gen_choice == "1":
            emergency_services()
        elif gen_choice == "2":
            manage_feedback()
        elif gen_choice == "3":
            hospital_facilities()
        elif gen_choice == "4":
            print(T("Thank you! Visit again.", "धन्यवाद! फिर मिलेंगे।"))
            print("-------------------------------------------------------")
            print(T("Here is the summary of the day.", "यहाँ दिन का सारांश दिया गया है।"))
            print("-------------------------------------------------------")
            daily_summary()
            break
        else:
            print(T("Invalid choice.", "गलत विकल्प।"))

if __name__ == "__main__":
    main_menu()
