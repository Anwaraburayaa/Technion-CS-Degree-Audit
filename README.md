# Technion CS Degree Audit

A web application developed in Python and Streamlit for auditing graduation requirements for undergraduate Computer Science students in the Technion 3-year B.Sc. program.

## Project Description

Developed an automated system for tracking graduation requirements, with a focus on the elective requirements of List A (רשימה א') and List B (רשימה ב'). The application allows students to enter completed courses and automatically determines remaining mandatory courses and elective credit requirements based on the official departmental requirements.

The system also supports exceptional departmental approvals (אישור חריג), allowing students to manually add approved credits from courses that are not included in the standard course database.

## Main Features

* **Multi-Key Course Resolution:** Course identification using 6-digit course numbers, canonical Hebrew course names, or English course names.

* **Core Audit:** Automatic identification of missing mandatory Computer Science core courses.

* **Elective Deficit Calculation:** Calculation of remaining List A and List B credit requirements.

* **Credit Injection:** Support for manually adding credits received through exceptional departmental approval (אישור חריג).

* **Session Memory:** Persistent session state for maintaining selected courses and manually added credits throughout user interactions.

## Technical Implementation

* **Tech Stack:** Developed using Python 3 and Streamlit.

* **Algorithmic Efficiency:** Course data is indexed using Python dictionaries (Hash Maps) to provide amortized $\mathcal{O}(1)$ average course lookup across all three naming keys.

* **Mathematical Set Operations:** Utilizes pure set subtraction ($\text{Required} \setminus \text{Completed}$) to compare the student's completed courses with the required core courses and identify missing requirements.

* **Software Architecture:** Follows a separation-of-concerns architecture, with the graduation requirement calculations (`core/audit.py`) implemented independently from the Streamlit user interface (`app.py`). The auditing logic can therefore be tested and executed independently of the application interface.

* **Quality Assurance:** Automated tests were implemented using `pytest` to verify credit calculations, course resolution, mandatory-course identification, and relevant edge cases.
