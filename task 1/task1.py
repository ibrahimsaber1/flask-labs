from flask import Flask, render_template, redirect, url_for


app = Flask(__name__)
students = [{"id":1, "name":"Ahmed"}, {"id":2, "name":"Mohamed"}, {"id":3, "name":"Youssef"}]

@app.route("/")
def home_page():
    # global students # for modification

    # return {"id": 1, "name":"Ahmed"}
    # return "<h1>Home Page</h1>"
    return render_template("index.html", students_data=students)

@app.route("/search/<int:id>") # search/1 => data in table of user that has id=1
def search(id):
    is_found = False
    target_student = None
    for student in students:
        if student['id'] == id:
            is_found = True
            target_student = student

    return render_template("search.html", is_found=is_found, target_student=target_student)


if __name__ == "__main__":
    # print(app.url_map)
    app.run(debug=True, port=5000)