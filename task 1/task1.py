from flask import Flask, render_template, redirect, url_for


app = Flask(__name__)
students = [{"id":1, "name":"Ahmed"}, {"id":2, "name":"Mohamed"}, {"id":3, "name":"Youssef"}]

@app.route("/")
def home_page():

    return render_template("index.html", students_data=students)

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