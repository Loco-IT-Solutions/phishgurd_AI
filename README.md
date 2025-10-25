PhishGuard AI - demo prototype

1. Create and activate virtualenv:
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Mac/Linux:
   source venv/bin/activate

2. Install dependencies:
   pip install -r requirements.txt

3. Train a demo model:
   python src/train.py

4. Run the API:
   python src/api.py

5. Test:
   curl -X POST http://localhost:5000/predict -H "Content-Type: application/json" -d '{"subject":"Your account is suspended", "from":"support@bank.com","body":"please verify your password"}'
