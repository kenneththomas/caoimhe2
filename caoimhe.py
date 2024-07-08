from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from dateutil import parser
from sqlalchemy import func, Date

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///caoimhe.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Bounties(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.String(150), nullable=False)
    reward = db.Column(db.Integer, nullable=False)
    entry_date = db.Column(db.DateTime, default=datetime.now)
    expiration_date = db.Column(db.DateTime, nullable=True)
    task_type = db.Column(db.String(50), nullable=False) # 'single' or 'recurring'
    status = db.Column(db.String(50), nullable=False) # 'pending', 'completed'

class Completed(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.String(150), nullable=False)
    reward = db.Column(db.Integer, nullable=False)
    complete_date = db.Column(db.DateTime, default=datetime.now)

@app.route('/')
def index():
    recurring_bounties = Bounties.query.filter_by(status='pending', task_type='recurring').all()
    single_bounties = Bounties.query.filter_by(status='pending', task_type='single').all()
    total_points = get_total_points()
    return render_template('index.html', recurring_bounties=recurring_bounties, single_bounties=single_bounties, total_points=total_points)

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

@app.route('/daily-points')
def daily_points():
    today = datetime.now().date()
    seven_days_ago = today - timedelta(days=7)

    # Query to sum points for the last 7 days, grouped by day
    points_per_day = db.session.query(
        func.date(Completed.complete_date).label('day'),
        func.sum(Completed.reward).label('total_points')
    ).filter(Completed.complete_date >= seven_days_ago).group_by(func.date(Completed.complete_date)).all()

    # Create a dictionary to fill in missing days with zero points
    days_points = {today - timedelta(days=i): 0 for i in range(7)}
    for day in points_per_day:
        # Ensure that `day.day` is a datetime.date object
        days_points[day.day] = day.total_points

    # Ensure all dictionary keys are datetime.date objects before sorting
    #sorted_days_points = sorted(days_points.items())
    sorted_days_points = sorted((datetime.strptime(key, '%Y-%m-%d').date() if isinstance(key, str) else key, value) for key, value in days_points.items())

    return render_template('daily_points.html', points=sorted_days_points)

@app.route('/point-balance-data')
def point_balance_data():
    # Get data for the last 30 days
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=29)

    # Query to get daily point balance
    daily_points = db.session.query(
        func.date(Completed.complete_date).label('date'),
        func.sum(Completed.reward).label('points')
    ).filter(Completed.complete_date >= start_date).group_by(func.date(Completed.complete_date)).all()

    # Create a dictionary with all dates
    date_range = {(start_date + timedelta(days=i)).strftime('%Y-%m-%d'): None for i in range(30)}

    # Update the dictionary with actual points
    for date, points in daily_points:
        date_key = date.strftime('%Y-%m-%d') if isinstance(date, datetime) else date
        date_range[date_key] = points

    # Calculate cumulative points
    cumulative_points = 0
    for date in sorted(date_range.keys()):
        if date_range[date] is not None:
            cumulative_points += date_range[date]
        date_range[date] = cumulative_points

    # Convert to list of dictionaries for JSON serialization
    chart_data = [{"date": date, "points": points} for date, points in date_range.items()]

    return jsonify(chart_data)

@app.route('/delete/<int:task_id>')
def delete_task(task_id):
    task = Bounties.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for('index'))

def get_total_points():
    total_points = db.session.query(db.func.sum(Completed.reward)).scalar() or 0
    return total_points

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', debug=True, port=5009)