from flask import Flask, redirect, url_for, session, request, jsonify, render_template, flash
import discord_auth
import os
import csv
import datetime as dt

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')  # Set this key securely

USERS_FILE = 'users.csv'
RUNS_FILE = 'runs.csv'

@app.route('/')
def home():
    return render_template('leaderboard.html')

@app.route('/login')
def login():
    discord_login_url = discord_auth.get_discord_login_url()
    return redirect(discord_login_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    token_info = discord_auth.get_token(code)
    session['discord_token'] = token_info['access_token']
    user_info = discord_auth.get_user_info(session['discord_token'])
    
    # Write to users.csv
    user_id = user_info['id']
    username = user_info['username']
    discriminator = user_info['discriminator']
    avatar = user_info['avatar']
    
    # Check if user already exists
    user_exists = False
    with open(USERS_FILE, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            if row[0] == user_id:
                user_exists = True
                break

    if not user_exists:
        with open(USERS_FILE, 'a') as f:
            writer = csv.writer(f)
            writer.writerow([user_id, username, discriminator, avatar])
    
    session['user_info'] = user_info
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    if 'user_info' in session:
        return redirect(url_for('submit'))
    return redirect(url_for('login'))

@app.route('/submit', methods=['GET', 'POST'])
def submit():
    if request.method == 'POST':
        if 'user_info' not in session:
            flash('You need to be logged in to submit a run.')
            return redirect(url_for('login'))
        
        user_id = session['user_info']['id']
        time = request.form.get('time')
        video_url = request.form.get('video_url')
        game = request.form.get('game')

        if not time or not video_url or not game:
            flash('All fields are required.')
            return redirect(url_for('submit'))

        now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # read the last run id, which is number of lines in the file + 1
        with open(RUNS_FILE, 'r') as f:
            run_id = len(f.readlines()) + 1

        with open(RUNS_FILE, 'a') as f:
            writer = csv.writer(f)
            writer.writerow([run_id, user_id, time, video_url, game, now])

        flash('Run submitted successfully.')
        return redirect(url_for('home'))

    if 'user_info' not in session:
        return redirect(url_for('login'))
    return render_template('submit.html')

@app.route('/leaderboard', methods=['GET'])
def leaderboard():
    game = request.args.get('game')
    leaderboard = []
    with open(RUNS_FILE, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) < 6 or row[4] != game:
                continue
            run_id, user_id, time, video_url, game, timestamp = row
            with open(USERS_FILE, 'r') as uf:
                user_reader = csv.reader(uf)
                for user_row in user_reader:
                    if user_row[0] == user_id:
                        username = f"{user_row[1]}#{user_row[2]}"
                        time = dt.timedelta(seconds=float(time))
                        time = round(time.total_seconds(), 2)
                        time = str(time)
                        if len(time.split('.')[1]) < 2:
                            time += '0'
                        leaderboard.append({"id": run_id, "username": username, "time": time, "video_url": video_url, "timestamp": timestamp})
                        break
    return jsonify(leaderboard)

@app.route('/run')
def run():
    run_id = request.args.get('id')
    if not run_id:
        return "Run ID is required", 400
    
    with open(RUNS_FILE, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            if row[0] == run_id:
                run_id, user_id, time, video_url, game, timestamp = row
                with open(USERS_FILE, 'r') as uf:
                    user_reader = csv.reader(uf)
                    for user_row in user_reader:
                        if user_row[0] == user_id:
                            username = f"{user_row[1]}#{user_row[2]}"
                            # convert time to HH:MM:SS.ms
                            time = dt.timedelta(seconds=float(time))
                            time = round(time.total_seconds(), 2)
                            time = str(time)
                            if len(time.split('.')[1]) < 2:
                                time += '0'
                            run = {"username": username, "time": time, "video_url": video_url, "game": game, "timestamp": timestamp}
                            return render_template('run.html', run=run)
    return "Run not found", 404

if __name__ == '__main__':
    app.run(debug=True)
