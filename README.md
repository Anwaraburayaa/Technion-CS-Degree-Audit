# Technion CS Degree Audit

A web application built in Python and Streamlit to help Technion Computer Science undergraduates (3-year B.Sc.) audit their degree progress and verify graduation requirements.

**🔗 Live Demo:** [technion-cs-degree-audit.streamlit.app](https://technion-cs-degree-audit-8zz3utn44pyn3xjpnshfqd.streamlit.app/)

---

## Overview

Tracking degree requirements at the Technion can get complicated fast—especially when balancing mandatory courses, List A (רשימה א'), List B (רשימה ב'), and special approvals.

This tool gives students an instant, accurate picture of where they stand: add your completed courses (manually or via grade-sheet PDF), see which mandatory courses are still missing, and track exactly how many elective credits remain based on the official CS faculty catalog.

---

## Features

- **Flexible course entry:** Search any course by its 6-digit catalog number, Hebrew name, or English name—or upload an official Technion grade-sheet PDF for automated parsing.
- **Mandatory course audit:** Instantly detects which core Computer Science courses are still unfulfilled.
- **Elective credit tracking:** Accurately tallies remaining credit quotas for List A (רשימה א') and List B (רשימה ב').
- **Faculty approvals (*אישור חריג*):** Manually log approved credits for external or non-standard courses outside the default catalog.
- **Session persistence:** Retains selected courses and manual credits throughout your active session.

---

## How to Use

1. Open the [live demo](https://technion-cs-degree-audit-8zz3utn44pyn3xjpnshfqd.streamlit.app/).
2. Add your completed courses by uploading your grade-sheet PDF or searching by course number/name.
3. Add any credits granted via special faculty approvals (*אישור חריג*).
4. Review your missing mandatory courses and remaining List A / List B credits.

---

## Technical Implementation

- **Decoupled architecture:** All graduation rules and credit logic live in `core/audit.py`, completely separate from the Streamlit UI (`app.py`). The audit engine runs independently and can be unit-tested without launching the web interface.
- **Fast course lookup:** Catalog data is indexed across all three identifiers (course number, Hebrew name, English name) in hash maps, providing $\mathcal{O}(1)$ average-time lookup.
- **Set-based audit logic:** Core requirements are evaluated cleanly using set difference ($\text{Required} \setminus \text{Completed}$).
- **Transcript parsing:** Regular expressions extract course numbers, titles, and credit weights directly from the Technion grade-sheet PDF layout.
- **Automated test suite:** A `pytest` test suite validates credit calculations, multi-key lookups, and edge cases.

---

> **Note:** Requirements are based on the Technion CS faculty catalog for 2024/2025 (תשפ"ה). This is an independent student project, not an official Technion tool. Always verify your official status with the undergraduate office.
