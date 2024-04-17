from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from dateutil import parser

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///eightyhd.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Bounties(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.String(150), nullable=False)
    reward = db.Column(db.Integer, nullable=False)
    entry_date = db.Column(db.DateTime, default=datetime.utcnow)
    expiration_date = db.Column(db.DateTime, nullable=True)
    task_type = db.Column(db.String(50), nullable=False) # 'single' or 'recurring'
    status = db.Column(db.String(50), nullable=False) # 'pending', 'completed'

class Completed(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.String(150), nullable=False)
    reward = db.Column(db.Integer, nullable=False)
    complete_date = db.Column(db.DateTime, default=datetime.utcnow)

@app.route('/')
def index():
    # Show all bounties
    bounties = Bounties.query.filter(Bounties.status == 'pending').all()
    total_points = get_total_points()
    return render_template('index.html', bounties=bounties, total_points=total_points)

@app.route('/add', methods=['POST'])
def add_task():
    task = request.form.get('task')
    reward = request.form.get('reward')
    expiration_date = request.form.get('expiration_date') or None
    task_type = request.form.get('task_type')

    if expiration_date:
        expiration_date = parser.parse(expiration_date)
    
    new_task = Bounties(task=task, reward=int(reward), expiration_date=expiration_date, task_type=task_type, status='pending')
    db.session.add(new_task)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/complete/<int:task_id>')
def complete_task(task_id):
    task = Bounties.query.get(task_id)
    completed_task = Completed(task=task.task, reward=task.reward)
    db.session.add(completed_task)
    if task.task_type == 'single':
        task.status = 'completed'
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/completed')
def completed_tasks():
    # Query all completed tasks
    completed = Completed.query.order_by(Completed.complete_date.desc()).all()
    return render_template('completed.html', completed=completed)

@app.route('/add-completed', methods=['POST'])
def add_completed():
    task_description = request.form['task']
    reward_points = int(request.form['reward'])
    completed_task = Completed(task=task_description, reward=reward_points)
    db.session.add(completed_task)
    db.session.commit()
    return redirect(url_for('index'))

def get_total_points():
    total_points = db.session.query(db.func.sum(Completed.reward)).scalar() or 0
    return total_points

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)