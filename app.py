from flask import Flask, redirect, url_for, session, request, jsonify, render_template, flash
import discord_auth
import os
import csv
import datetime as dt

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')  # Set this key securely

USERS_FILE = 'users.csv'
RUNS_FILE = 'runs.csv'
QUEUE_FILE = 'queue.csv'

ADMIN_USER_ID = ['773996537414942763']

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
    print(token_info)
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

        # Read the last run id, which is the number of lines in the file + 1
        with open(RUNS_FILE, 'r') as f:
            run_id = len(f.readlines()) + 1

        with open(QUEUE_FILE, 'a') as f:
            writer = csv.writer(f)
            writer.writerow([run_id, user_id, time, video_url, game, now])

        # Assign "Speedrunner" role using a separate bot
        guild_id = os.getenv('DISCORD_GUILD_ID')
        role_id = os.getenv('DISCORD_ROLE_ID')

        role_id = {
            "speedrunner": 1268657083310669925,
            "port": 1268665745567518872,
            "tutorial": 1268665919048122563
        }

        print(discord_auth.assign_role(guild_id, user_id, role_id['speedrunner']))
        if game == 'game1':
            print('assigning port role')
            print(discord_auth.assign_role(guild_id, user_id, role_id['port']))
        elif game == 'game2':
            discord_auth.assign_role(guild_id, user_id, role_id['tutorial'])

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

@app.route('/rules')
def rules():
    return render_template('rules.html')

@app.route('/temp')
def temp():
    return "Please wait... Loading..."

@app.route('/admin', methods=['GET'])
def verify():
    # verify they are admin with discord auth
    user_info = session['user_info']
    print('A user has attempted to access the admin page. Outputting user info:')
    print(user_info)
    if user_info['id'] not in ADMIN_USER_ID:
        return "You are not authorized to access this page", 401
    queue = []
    with open(QUEUE_FILE, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            username = 'temp'
            user_id = row[1]
            print(user_id)
            with open(USERS_FILE, 'r') as uf:
                user_reader = csv.reader(uf)
                for user_row in user_reader:
                    if user_row[0] == user_id:
                        username = f"{user_row[1]}"
                        break
            time = row[2]
            video_url = row[3]
            game = row[4]
            timestamp = row[5]
            run_id = row[0]
            user_id = row[1]
            data = [username, time, video_url, game, timestamp, run_id, user_id]
            queue.append(data)
    return render_template('admin.html', queue=queue)

@app.route('/deleterun', methods=['GET'])
def deleterun():
    # is the user logged in?
    if 'user_info' not in session:
        return redirect(url_for('login'))
    # run_id = request.form.get('id')
    run_id = request.args.get('id')
    print("RUN ID:", run_id)
    if not run_id:
        return "Run ID is required", 400
    # now check if they are owner of the run OR admin
    user_info = session['user_info']
    print('A user has attempted to delete a run. Outputting user info:')
    print(user_info)
    if user_info['id'] in ADMIN_USER_ID:
        with open(RUNS_FILE, 'r') as f:
            reader = csv.reader(f)
            runs = []
            for row in reader:
                if row[0] == run_id:
                    continue
                runs.append(row)
        with open(RUNS_FILE, 'w') as f:
            writer = csv.writer(f)
            for row in runs:
                writer.writerow(row)
        return redirect(url_for('home'))
    with open(RUNS_FILE, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            if row[0] == run_id:
                if row[1] == user_info['id']:
                    runs = []
                    with open(RUNS_FILE, 'r') as f:
                        reader = csv.reader(f)
                        for row in reader:
                            if row[0] == run_id:
                                continue
                            runs.append(row)
                    with open(RUNS_FILE, 'w') as f:
                        writer = csv.writer(f)
                        for row in runs:
                            writer.writerow(row)
                    return redirect(url_for('home'))
                return "You are not authorized to delete this run", 401
            
    if user_info['id'] not in ADMIN_USER_ID:
        return "Run not found", 404
    with open(QUEUE_FILE, 'r') as f:
        reader = csv.reader(f)
        runs = []
        for row in reader:
            if row[0] == run_id:
                continue
            runs.append(row)
    with open(QUEUE_FILE, 'w') as f:
        writer = csv.writer(f)
        for row in runs:
            writer.writerow(row)
    return redirect(url_for('home'))

@app.route('/addrun', methods=['GET'])
def addrun():
    # only admin can access this page
    user_info = session['user_info']
    print('A user has attempted to access the addrun page. Outputting user info:')
    print(user_info)
    if user_info['id'] not in ADMIN_USER_ID:
        return "You are not authorized to access this page", 401
    
    # add the run to runs.csv
    # get all run info from the request
    user_id = request.args.get('user_id')
    time = request.args.get('time')
    video_url = request.args.get('video_url')
    game = request.args.get('game')
    timestamp = request.args.get('submission_time')
    run_id = request.args.get('run_id')
    print([run_id, user_id, time, video_url, game, timestamp])
    with open(RUNS_FILE, 'a') as f:
        writer = csv.writer(f)
        writer.writerow([run_id, user_id, time, video_url, game, timestamp])
    # remove from queue.csv
    runs = []
    with open(QUEUE_FILE, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            if row[0] == run_id:
                continue
            runs.append(row)
    with open(QUEUE_FILE, 'w') as f:
        writer = csv.writer(f)
        for row in runs:
            writer.writerow(row)
    return '{"Success": "Run added to leaderboard"}'
    
# 404 special page
@app.errorhandler(404)
def page_not_found(e):
    return "404: Page not found. <a href='/'>Click here to go back to the leaderboard.</a>", 404

if __name__ == '__main__':
    app.run(debug=True, port=5000, host="0.0.0.0")
