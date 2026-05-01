import os
from app import create_app

app = create_app()

if __name__ == "__main__":
    debug = os.getenv("FLASK_ENV") != "production"
    app.run(debug=debug, host="0.0.0.0", port=5000)
