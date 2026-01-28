# Beginner's Guide to Vedic Astrology AI FastAPI

Welcome! This guide is designed for anyone with basic Python knowledge who wants to understand, run, and test our new FastAPI application.

---

## 1. What is an API? (The Restaurant Analogy)
Think of an **API** like a **Waiter** in a restaurant:
- **You (The Client)**: Sit at the table with a menu.
- **The Kitchen (The Backend)**: Prepares the food (Astrology calculations).
- **The Waiter (The API)**: Takes your order, tells the kitchen what to do, and brings back your plate.

**FastAPI** is a modern tool that helps us build this "Waiter" extremely fast and with built-in safety checks.

---

## 2. Project Tour: Who does what?

Our project is split into three main parts to keep it clean and organized:

1.  **`fastapi_app.py` (The Receptionist)**:
    - This is the main entrance. It doesn't do "work" itself; it just greets the request and sends it to the right department.
2.  **`astro_api/` (The Specialized Departments)**:
    - `astro_api/v1/routers/`: This is where the actual logic for different features lives.
    - `astro_api/v1/config.py`: This handles "Secrets" like your API keys using a `.env` file.
    - `astro_api/v1/middleware.py`: Handles timing, logging, and security limits.
    - `astro_api/v1/deps.py`: Shared tools, like checking if your API key is valid.
3.  **`backend/` (The Engine Room)**:
    - This contains the heavy-duty astrology calculation code tested for accuracy.

---

## 3. Python "Magic" Used in this App

### **Decorators (`@`)**
- **In plain English**: A "Tag" that tells Python: *"Whenever someone sends data to this URL, run this specific function."*

### **Pydantic Models**
- **In plain English**: Our "Form Police". It checks the data *before* it gets to the kitchen.

### **Async / Await**
- **In plain English**: The "Coffee Machine" analogy. We don't stand still while the coffee brews; we start the toast. This keeps the API responsive.

---

## 4. How to Run the Server

1.  **Activate environment**: `source venv/bin/activate`
2.  **Install tools**: `pip install -r requirements.txt`
3.  **Setup Secrets**: Create a `.env` file with `KEY=your_openai_key`.
4.  **Start server**: `uvicorn fastapi_app:app --reload`

---

## 5. 🚀 THE ULTIMATE MANUAL TESTING GUIDE

This section is for ensuring everything works as expected. We will use three different methods to test the API.

### **5.1. Method A: The Interactive Swagger UI (Best for Beginners)**
FastAPI has a built-in testing website that lets you click buttons instead of writing code.

1.  **Access**: Open [http://localhost:8000/docs](http://localhost:8000/docs) in your browser.
2.  **Explore**: You will see a list under "Chart" and "AI".
3.  **The "Try it out" Flow**:
    -   Click on `POST /api/v1/chart/generate`.
    -   Click the **"Try it out"** button (top right of the section).
    -   **Edit the Request Body**: You'll see a JSON block. Change the `name` or `birth_date`.
    -   **Click "Execute"**: The big blue button at the bottom.
4.  **Reading the Results**:
    -   **Response Body**: This shows the planetary positions. Look for `"status": "success"` (if applicable) and the values for Sun, Moon, etc.
    -   **Headers**: Scroll down to see `X-Process-Time` (how long it took) and `X-Request-ID` (a unique ID for that specific search).

### **5.2. Method B: Power-User Terminal (`curl`)**
For those who like the command line, `curl` is the industry standard.

**Scenario 1: Testing Chart Generation**
Run this command to see a formatted success response:
```bash
curl -X 'POST' \
  'http://localhost:8000/api/v1/chart/generate' \
  -H 'Content-Type: application/json' \
  -d '{
  "name": "Abhishek",
  "gender": "Male",
  "birth_date": "1995-10-10",
  "birth_time": "10:30",
  "birth_place": "New Delhi"
}' | jq .
```
*(Note: Adding `| jq .` at the end makes the JSON look pretty if you have `jq` installed).*

**Scenario 2: Checking Headers & Detailed Connection Info**
Use the `-i` flag to see wait times and correlation IDs:
```bash
curl -i -X 'GET' 'http://localhost:8000/api/v1/health'
```

### **5.3. Method C: Professional GUI (Postman / Insomnia)**
If you are doing serious testing, download [Postman](https://www.postman.com/).
1.  **Create Request**: Set method to `POST` and URL to `http://localhost:8000/api/v1/ai/predict`.
2.  **Set Headers**: Add `Content-Type: application/json`.
3.  **Set Body**: Choose `raw` -> `JSON`. Paste a chart data object and your question.
4.  **Send**: Hit the Send button and view the results in the bottom pane.

---

## 6. 🐒 THE "CHAOS MONKEY" TEST (Negative Testing)
A good tester tries to **break** things. Use these scenarios to verify our safety checks:

| What to test | What to expect | Why? |
|--------------|----------------|------|
| **Wrong Date Format** | Status `422` | We only accept `YYYY-MM-DD`. Sending `10/10/1990` should fail. |
| **Invalid Month** | Status `422` | Sending `1990-25-01` (Month 25) will trigger a "Value Error" we built. |
| **Empty Strings** | Status `422` | Leaving `birth_place` as `""` is caught by our `min_length=1` rule. |
| **Rapid Fire** | Status `429` | Hit refresh/execute 30 times quickly. You should get "Rate limit exceeded". |
| **Payload Overload** | Status `413` | Try to send a massive 2MB text block in the `question` field. Our middleware will block it. |

---

## 7. Troubleshooting Common Issues

-   **"Connection Refused"**: The Uvicorn server is likely not running. Check your terminal.
-   **"Location not found"**: `get_location_data` couldn't find the city you typed. Try a more common name (e.g., "London" instead of a small village).
-   **"422 Detail"**: Read the message! It will literally tell you: `"msg": "Invalid date format"`.
-   **Old Cache**: If you change the `.env` file, you **must** restart the server for it to take effect.

### **How to ask for help?**
If you find a bug, copy the **`X-Request-ID`** from the response headers. This allows us to find your specific request in the server logs instantly.
