import mysql.connector
from flask import Flask, render_template, request, redirect, url_for, session, flash
import random
from bot_strategies import AggressiveBot, PassiveBot, MarketLoverBot, MarketHaterBot, RandomBot
import os
from dotenv import load_dotenv
import logging

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY')

logging.basicConfig(filename='trader_titan.log', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

db_host = os.environ.get('MYSQL_HOST')
db_user = os.environ.get('MYSQL_USER')
db_password = os.environ.get('MYSQL_PASSWORD')
db_name = os.environ.get('MYSQL_DATABASE')

def get_db_connection():
    mydb = mysql.connector.connect(
        host=db_host,
        user=db_user,
        password=db_password,
        database=db_name
    )
    return mydb

def get_random_question():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM questions ORDER BY RAND() LIMIT 1")
    question_data = cursor.fetchone()
    conn.close()
    return question_data


def choose_first_mover():
    return random.choice(['player', 'bot'])

def initialize_game():
    question_data = get_random_question()

    if question_data:
        question = f"{question_data['question']} (in {question_data['units']})"
        true_answer = question_data['answer']
        units = question_data['units']

        session['question'] = question
        session['true_answer'] = true_answer
        session['units'] = units
        session['first_mover'] = choose_first_mover()
        session['current_mover'] = session['first_mover']
        session['current_width'] = None
        session['game_over'] = False
        session['market_made'] = False
        session['market_maker'] = None
        session['bid'] = None
        session['ask'] = None

        bot_types = {
            'AggressiveBot': AggressiveBot,
            'PassiveBot': PassiveBot,
            'MarketLoverBot': MarketLoverBot,
            'MarketHaterBot': MarketHaterBot,
            'RandomBot': RandomBot,
        }
        bot_type_name = random.choice(list(bot_types.keys()))
        session['bot_type_name'] = bot_type_name

        session['bot_params'] = {
            'initial_estimate_noise': 0.5,
            'width_reduction_multiplier': random.choice([0.8, 0.85, 0.9]),
            'market_willingness': random.choice([0.1, 0.4, 0.9]),
            'std_dev_multiplier': 4.0  #this needs work
        }


        initial_estimate = true_answer * (1 + random.uniform(-session['bot_params']['initial_estimate_noise'], session['bot_params']['initial_estimate_noise']))
        session['bot_initial_estimate'] = initial_estimate
        session['bot_log'] = []

    else:
        session['question'] = "No question found"
        session['true_answer'] = 0
        session['units'] = ""
        session['current_width'] = None
        session['first_mover'] = None
        session['current_mover'] = None
        session['game_over'] = True
        session['market_made'] = False
        session['market_maker'] = None
        session['bid'] = None
        session['ask'] = None
        session['bot_type_name'] = None
        session['bot_initial_estimate'] = None
        session['bot_params'] = None
        session['bot_log'] = []



def create_bot():
    bot_type_name = session['bot_type_name']
    initial_estimate = session['bot_initial_estimate']
    true_answer = session['true_answer']
    bot_params = session['bot_params']

    bot_classes = {
        'AggressiveBot': AggressiveBot,
        'PassiveBot': PassiveBot,
        'MarketLoverBot': MarketLoverBot,
        'MarketHaterBot': MarketHaterBot,
        'RandomBot': RandomBot,
    }

    if bot_type_name in bot_classes:
        bot = bot_classes[bot_type_name](true_answer, **bot_params)
        bot.current_estimate = initial_estimate
        bot.log = session['bot_log']
        return bot
    else:
        logging.error(f"Unknown bot type: {bot_type_name}")
        return None

# --- Flask Routes ----

@app.route('/')
def home():
    return redirect(url_for('game_handler'))

@app.route('/game', methods=['GET', 'POST'])
def game_handler():
    logging.debug("---- game_handler called ----")
    logging.debug(f"  session: {session}")

    if 'question' not in session or session['game_over']:
        initialize_game()

    if session['game_over']:
        return redirect(url_for('result'))

    # Bots turn
    if session['current_mover'] == 'bot' and session['bot_type_name'] is not None and not session['market_made']:
        bot = create_bot()
        if bot is None:
            flash("Error: Bot could not be created", 'error')
            return redirect(url_for('home'))

        if session['current_width'] is None:
            session['current_width'] = bot.generate_initial_width()
            bot.log.append(f"Bot set initial width: {session['current_width']}")
            session['current_mover'] = 'player'
            session['bot_log'] = bot.log
            return redirect(url_for('game_handler'))

        action = bot.choose_action(session['current_width'])

        if action == 'reduce_width':
            new_width = int(round(session['current_width'] * bot.width_reduction_multiplier))
            session['current_width'] = max(0, new_width)
            bot.update_belief('reduce_width', session['current_width'])
            session['bot_initial_estimate'] = bot.current_estimate
            session['current_mover'] = 'player'
            session['bot_log'] = bot.log 
            return redirect(url_for('game_handler'))

        elif action == 'make_market':
            session['market_maker'] = 'player'
            session['bot_log'] = bot.log 
            return redirect(url_for('make_market'))

    # Player turn
    elif session['current_mover'] == 'player' and request.method == 'POST':
        action = request.form['action']

        if action == 'set_initial_width':
            try:
                initial_width = int(request.form['initial_width'])
                if initial_width < 0:
                    flash("Initial width must be non-negative.", 'error')
                    return render_template('index.html', question=session['question'], current_width=session['current_width'])
                min_width = 10
                if initial_width < min_width:
                    flash(f'Initial width must be at least {min_width}', 'error')
                    return render_template('index.html', question=session['question'], current_width=session['current_width'])

                session['current_width'] = initial_width
                session['current_mover'] = 'bot'
                return redirect(url_for('game_handler'))
            except ValueError:
                flash("Invalid input.  Please enter an integer.", 'error')
                return render_template('index.html', question=session['question'], current_width=session['current_width'])

        elif action == 'reduce_width':
            try:
                new_width = int(request.form['width'])
                if new_width > int(round(session['current_width'] * 0.9)):
                    flash("New width cannot be greater than 90% of the current width.", 'error')
                    return render_template('index.html', question=session['question'], current_width=session['current_width'])
                if new_width < 0:
                    flash("New width cannot be negative", 'error')
                    return render_template('index.html', question=session['question'], current_width=session['current_width'])
                min_width = 1 #this is a problem if you think about it. So we will not be thinking about it
                if new_width < min_width:
                    flash(f'Width must be at least {min_width}', 'error')
                    return render_template('index.html', question=session['question'], current_width=session['current_width'])
                session['current_width'] = new_width

                if session['bot_type_name'] is not None:
                    bot = create_bot()
                    if bot is None: #Error
                        flash('Error creating bot', 'error')
                        return redirect(url_for('home'))
                    bot.update_belief('reduce_width', session['current_width'])
                    session['bot_initial_estimate'] = bot.current_estimate
                    session['bot_log'] = bot.log


                session['current_mover'] = 'bot'
                return redirect(url_for('game_handler'))
            except ValueError:
                flash("Invalid input.  Please enter a valid integer.", 'error')
                return render_template('index.html', question=session['question'], current_width=session['current_width'])

        elif action == 'make_market':
            session['market_maker'] = 'bot'
            bot = create_bot()
            if bot is None:
                flash("Error occurred creating bot", 'error')
                return redirect(url_for('home'))
            session['bid'], session['ask'] = bot.make_market(session['current_width'])
            session['market_made'] = True
            session['bot_log'] = bot.log
            return redirect(url_for('trade'))

    elif session['current_mover'] == 'bot' and session['market_made'] and session['market_maker'] == 'player' and session['bot_type_name'] is not None:
        bot = create_bot()
        if bot is None:
          flash("Error occurred when creating bot", 'error')
          return redirect(url_for('home'))

        action = bot.trade(session['bid'], session['ask'])
        session['bot_trade_action'] = action
        session['bot_log'] = bot.log


        if action == 'buy':
            winner = 'bot' if session['true_answer'] > session['ask'] else 'player'
        else:  # action == 'sell'
            winner = 'bot' if session['true_answer'] < session['bid'] else 'player'

        session['game_over'] = True
        session['winner'] = winner
        return redirect(url_for('result'))

    return render_template('index.html', question=session.get('question'), current_width=session.get('current_width'))

@app.route('/make_market', methods=['GET', 'POST'])
def make_market():
    if request.method == 'POST':
        try:
            bid = float(request.form.get('bid'))
            ask = float(request.form.get('ask'))
        except ValueError:
            flash("Invalid input for bid or ask.  Please enter numbers.", 'error')
            return render_template('make_market.html', current_width=session['current_width'])

        if bid >= ask:
            flash("Bid must be less than ask.", 'error')
            return render_template('make_market.html', current_width=session['current_width'], bid=bid, ask=ask)

        if bid < 1:
            flash("Bid must be at least 1.", 'error')
            return render_template('make_market.html', current_width=session['current_width'], bid=bid, ask=ask)

        session['bid'] = int(round(bid))
        session['ask'] = int(round(ask))
        session['market_made'] = True
        session['current_mover'] = 'bot'
        return redirect(url_for('game_handler'))

    else:
        bid = None
        ask = None
        return render_template('make_market.html', current_width=session['current_width'], bid=bid, ask=ask)
@app.route('/trade', methods=['GET','POST'])
def trade():
    if request.method == 'POST':
        # Player must trade
        action = request.form['action']
        if action == 'buy':
            winner = 'player' if session['true_answer'] > session['ask'] else 'bot'
        else:  # action == 'sell'
            winner = 'player' if session['true_answer'] < session['bid'] else 'bot'

        session['game_over'] = True
        session['winner'] = winner
        return redirect(url_for('result'))

    else: # request.method == 'GET'
        # market_maker == 'bot'
        # Player must trade
        bid = session['bid']
        ask = session['ask']
        return render_template('trade.html', bid=bid, ask=ask, market_maker=session['market_maker'])

@app.route('/result')
def result():
    winner = session.get('winner', 'unknown')
    true_answer = session.get('true_answer')
    units = session.get('units')
    bot_log = session.get('bot_log', [])
    bot_trade_action = session.get('bot_trade_action')
    market_maker = session.get('market_maker')

    session.clear()
    return render_template('result.html', answer=true_answer, units=units, winner=winner, bot_log=bot_log, bot_trade_action=bot_trade_action, market_maker=market_maker)

if __name__ == '__main__':
    app.run(debug=True)