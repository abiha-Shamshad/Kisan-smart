from website import create_app, db

app = create_app()

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print("Database initialized!")
    app.run(debug=True, port=5005)
