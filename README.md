# KedaiKira

A modern Streamlit cash-counter and transaction-log application for traditional hardware stores. The interface uses `streamlit-shadcn-ui` for navigation, cards, badges, and action buttons.

## Run the application

```bash
pip install -r requirements.txt
streamlit run app.py
```

Keep `database.xlsx` in the same folder as the Python files.

## Files

- `app.py`: main interface and navigation
- `tabs/home.py`: cash counter and transaction entry
- `tabs/summary.py`: transaction cards, details, editing, and deletion
- `database.py`: Excel reading, writing, formatting, and sorting
- `database.xlsx`: prices and logs sheets
