from app import create_app

app = create_app()

if __name__ == "__main__":
    # debug=False en producción; nunca exponer el debugger
    app.run(debug=False, host="127.0.0.1", port=5001)
