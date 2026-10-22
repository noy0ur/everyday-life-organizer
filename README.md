# Everyday Life Organizer 🗓️

A practical personal productivity web app for organizing everyday tasks, notes, shopping lists, and bills in one place.

## Why this project?
Many people need a simple place to remember what to do, save useful notes, prepare shopping lists, and keep track of upcoming payments. This app brings those small everyday workflows together in a lightweight dashboard.

## Features
- **Task manager:** add tasks, categories, due dates, priorities, and statuses
- **Notes:** save and review text notes
- **Shopping list:** add items and quantities, mark items as purchased, and export the remaining list
- **Bill tracker:** record payment amounts and due dates, mark bills as paid/unpaid
- **Dashboard:** see open tasks, overdue tasks, unpaid bills, and bills due in the next seven days
- **CSV exports:** download tasks, shopping items, and bills
- **SQLite storage:** data is stored in a local database file

## Tech stack
- Python
- Streamlit
- Pandas
- SQLite

## Run locally
Requires Python 3.10+.

```bash
pip install -r requirements.txt
streamlit run app.py
```

Open the local URL printed in your terminal.

## Deploy
1. Push the project files to a GitHub repository.
2. Open Streamlit Community Cloud and connect your GitHub account.
3. Select this repository and use `app.py` as the main file.
4. Deploy.

## Important limitations
This is a portfolio/demo project. It does not include user accounts, authentication, encrypted storage, notifications, or cloud synchronization. The local SQLite database may not persist on some cloud hosts after a restart or redeployment. Do not store passwords, bank credentials, or other sensitive information.

## Suggested GitHub repository description
A Python productivity app to manage daily tasks, notes, shopping lists, and bill payments with a Streamlit dashboard and SQLite storage.

## Ideas for future improvements
- User login and private accounts
- Email or push reminders
- Recurring tasks and bills
- Cloud database and multi-device sync
- Mobile-friendly PWA support
- Automated tests and CI
