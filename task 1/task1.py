from flask import Flask, render_template, redirect, url_for


app = Flask(__name__)
students = [{"id":1, "name":"ibrahim"}, {"id":2, "name":"mostafa"}, {"id":3, "name":"zaky"},{"id":3, "name":"nour"}]

@app.route("/")
def home_page():
    return render_template("home.html", students=students)

@app.route("/search/<int:id>")
def search(id):
    is_found = False
    target_student = None
    for student in students:
        if student['id'] == id:
            is_found = True
            target_student = student

    return render_template("search.html", is_found=is_found, target_student=target_student)


if __name__ == "__main__":
    app.run(debug=True, port=5000)