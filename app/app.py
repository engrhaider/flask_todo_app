from flask import Flask, render_template, request, redirect, url_for, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
import sys

migrate = Migrate()
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
db = SQLAlchemy(app)
# Initialize Flask-SQLAlchemy extension
db.init_app(app)
# Initialize Flask-Migrate
migrate.init_app(app, db)


class Todo(db.Model):
    __tablename__ = 'todos'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(), nullable=False)
    completed = db.Column(db.Boolean, default=False, nullable=False)
    list_id = db.Column(db.Integer, db.ForeignKey('todolists.id'), nullable=True)

    def __repr__(self):
        return f'<Todo {self.id} {self.description}>'


class TodoList(db.Model):
    __tablename__ = 'todolists'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    todos = db.relationship('Todo', backref='list', lazy=True)

    def __repr__(self):
        return f'<TodoList {self.id} {self.name}>'


@app.route("/todos/create", methods=['POST'])
def create_todo():
    error = False
    response = {}
    request_data = request.get_json()
    try:
        task_description = request_data.get('description', '')
        new_todo = Todo(description=task_description, completed=False, list_id=request_data.get('list_id', 1))
        db.session.add(new_todo)
        db.session.commit()
        response['success'] = True
        response['id'] = new_todo.id
        response['completed'] = new_todo.completed
        response['description'] = new_todo.description
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        abort(400)
    else:
        return jsonify(response)


@app.route("/todo-list/create", methods=['POST'])
def create_todo_list():
    new_todolist_id = 1
    try:
        list_name = request.form.get('list_name', '')
        todo_list = TodoList(name=list_name)
        db.session.add(todo_list)
        db.session.commit()
        new_todolist_id = todo_list.id
    except:
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()

    return redirect(url_for('get_list_todos', list_id=new_todolist_id))


@app.route("/todos/<todo_id>/update", methods=["POST"])
def updated_todo_item(todo_id):
    error = False
    try:
        todo = Todo.query.get(todo_id)
        todo.completed = request.json.get('is_completed')
        db.session.commit()
    except:
        error = True
        db.session.rollback()
    finally:
        db.session.close()

    if error:
        abort(400)
    else:
        return jsonify({
            'success': True
        })


@app.route("/todos/<todo_id>/delete", methods=["POST"])
def delete_todo_item(todo_id):
    error = False
    try:
        todo = Todo.query.filter_by(id=todo_id).delete()
        db.session.commit()
    except:
        error = True
        db.session.rollback()
    finally:
        db.session.close()

    if error:
        abort(400)
    else:
        return jsonify({
            'success': True
        })


@app.route('/lists/<list_id>')
def get_list_todos(list_id):
    return render_template('index.html',
                           lists=TodoList.query.all(),
                           active_list=TodoList.query.get(list_id),
                           todos=Todo.query.filter_by(list_id=list_id).order_by('id').all()
                           )


@app.route('/')
def index():
    return redirect(url_for('get_list_todos', list_id=1))


# always include this at the bottom of your code
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=3000)
