import os

from dotenv import load_dotenv

load_dotenv()  # reads .env if present (never committed)

from app import create_app  # noqa: E402

app = create_app()

if __name__ == "__main__":
    # debug stays off: Flask's debugger would let anyone run code on the server.
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")), debug=False)
