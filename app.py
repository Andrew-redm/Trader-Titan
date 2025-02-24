import mysql.connector
from flask import Flask, render_template, request, redirect, url_for, flash, session
import random
from bot_strategies import AggressiveBot, PassiveBot, MarketLoverBot, MarketHaterBot, RandomBot, Bot
import os
from dotenv import load_dotenv
import logging
import math  # Import math for rounding

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

bot_types = {
        'AggressiveBot': AggressiveBot,
        'PassiveBot': PassiveBot,
        'MarketLoverBot': MarketLoverBot,
        'MarketHaterBot': MarketHaterBot,
        'RandomBot': RandomBot,
    }

def create_bot(true_answer, bot_type_name=None, bot_params=None):
    

    if bot_type_name is None:
        bot_type_name = random.choice(list(bot_types.keys()))

    if bot_params is None:
        bot_params = {
            'initial_estimate_noise': 0.5,
            'width_reduction_multiplier': 0.9,
            'market_willingness': 0.5,
            'std_dev_multiplier': 4.0
        }

    if bot_type_name in bot_types:
        bot = bot_types[bot_type_name](true_answer, **bot_params)
        return bot
    else:
        logging.error(f"Unknown bot type: {bot_type_name}")
        return None
    
def initialize_game_battle(selected_bot_type):
    question_data = get_random_question()

    if question_data:
        question = f"{question_data['question']} (in {question_data['units']})"
        true_answer = question_data['answer']
        units = question_data['units']

        bot = create_bot(true_answer, bot_type_name=selected_bot_type)
        if bot is None:
            return False

        game_state = {
            'mode': 'battle',
            'question': question,
            'true_answer': true_answer,
            'units': units,
            'current_mover': random.choice(['player', 'bot']),
            'current_width': None,
            'game_over': False,
            'market_made': False,
            'market_maker': None,
            'bid': None,
            'ask': None,
            'bot_type_name': type(bot).__name__,
            'bot': bot.to_dict(),
            'bot_log': [],
            'player_capital': 10000,
            'bot_capital': 10000,
        }
        return game_state

    else:
        return False
            
def calculate_damage(true_answer, bid, ask, trade_action, game_state):
    #this is going to need a lot of work
    market_width = ask - bid
    if bid <= true_answer <= ask:
        if trade_action == 'buy':
            error = abs(true_answer - ask)
        else:  # 'sell'
            error = abs(true_answer - bid)
    else:  
        error = abs(true_answer - (ask if true_answer > ask else bid))

    normalized_error = error / (true_answer + market_width)
    damage = int(round(normalized_error * 10000)) 
    damage = round(damage, 0)
    logging.debug(f"Damage calculated: {damage}") 

    if (trade_action == 'buy' and true_answer > ask) or \
       (trade_action == 'sell' and true_answer < bid):
        game_state['bot_capital'] -= damage
        game_state['winner'] = 'player'
    else:
        game_state['player_capital'] -= damage
        game_state['winner'] = 'bot'

    return damage
def initialize_game_single():
    question_data = get_random_question()

    if question_data:
        question = f"{question_data['question']} (in {question_data['units']})"
        true_answer = question_data['answer']
        units = question_data['units']

        bot = create_bot(true_answer)
        if bot is None:
            return False

        game_state = {
            'mode': 'single', 
            'question': question,
            'true_answer': true_answer,
            'units': units,
            'current_mover': 'player',#not needed
            'current_width': None,
            'game_over': False,
            'market_made': False,
            'market_maker': None,
            'bid': None,
            'ask': None,
            'bot_type_name': type(bot).__name__,
            'bot': bot.to_dict(),
            'bot_log': [],
            'player_capital': 10000,
            'bot_capital': 10000,
        }
        return game_state
    else:
        return {
            'question': "No question found",
            'game_over': True,
            'mode': 'single',
            'bot_type_name': None,
            'bot': None,
            'bot_log': [],
            'player_capital': 10000,
            'bot_capital': 10000,
        }

def reset_battle_round(game_state):
    """Reset game state for a new battle round while preserving scores and bot type."""
    question_data = get_random_question()
    if not question_data:
        return False

    logging.debug(f"Old question: {game_state.get('question')}")
    logging.debug(f"New question data: {question_data}")

    bot_type_name = game_state['bot_type_name']
    player_capital = game_state['player_capital']
    bot_capital = game_state['bot_capital']
    mode = game_state['mode']
    
    game_state.clear()
    #no way this is the right way to do this
    game_state['mode'] = mode
    game_state['bot_type_name'] = bot_type_name
    game_state['player_capital'] = player_capital
    game_state['bot_capital'] = bot_capital
    game_state['question'] = str(question_data['question']) + f" (in {question_data['units']})"
    game_state['true_answer'] = float(question_data['answer'])
    game_state['units'] = str(question_data['units'])
    game_state['current_mover'] = random.choice(['player', 'bot'])
    game_state['current_width'] = None
    game_state['market_made'] = False
    game_state['market_maker'] = None
    game_state['bid'] = None
    game_state['ask'] = None
    game_state['bot'] = create_bot(question_data['answer'], bot_type_name=bot_type_name).to_dict()
    game_state['bot_log'] = []
    game_state['game_over'] = False
    
    logging.debug(f"Reset complete. New question: {game_state['question']}")
    
    return True

@app.route('/')
def home():
    bot_types_list = list(bot_types.keys())
    return render_template('home.html', bot_types=bot_types_list)

@app.route('/how-to-play')
def how_to_play():
    return render_template('how_to_play.html')

@app.route('/start_game', methods=['POST'])
def start_game():
    game_mode = request.form['game_mode']
    bot_type = request.form['bot_type']

    if game_mode == 'single':
        game_state = initialize_game_single()
    elif game_mode == 'battle':
        game_state = initialize_game_battle(bot_type)
    else:
        flash("Invalid game mode selected.", 'error')
        return redirect(url_for('home'))

    if not game_state:
        flash("Failed to initialize game.", 'error')
        return redirect(url_for('home'))

    session['game_state'] = game_state
    return redirect(url_for('game'))

@app.route('/battle', methods=['GET', 'POST'])
def battle():
    if request.method == 'POST':
        selected_bot_type = request.form.get('bot_type')
        valid_bot_types = ['AggressiveBot', 'PassiveBot', 'MarketLoverBot', 'MarketHaterBot', 'RandomBot']
        if selected_bot_type not in valid_bot_types:
            flash("Invalid bot type selected.", 'error')
            return redirect(url_for('home'))

        game_state = initialize_game_battle(selected_bot_type)
        if not game_state:
            flash("Failed to initialize game.", 'error')
            return redirect(url_for('home'))
        session['game_state'] = game_state
        return redirect(url_for('game'))

    return render_template('home.html')

@app.route('/game', methods=['GET', 'POST'])
def game():
    if 'game_state' not in session:
        logging.debug("No game state in session")
        return redirect(url_for('home'))
    
    game_state = session['game_state']
    logging.debug(f"Game State: {game_state}")
    
    if game_state.get('game_over', False):
        return redirect(url_for('result'))

    if game_state.get('round_ended'):
        flash(f"Round Complete! {game_state['winner']} won. Damage: {game_state['last_round_damage']}", 'info')
        
        game_state['round_ended'] = False
        game_state['last_round_damage'] = None
        game_state['last_round_winner'] = None
        game_state['market_made'] = False
        game_state['market_maker'] = None
        game_state['bid'] = None
        game_state['ask'] = None
        game_state['current_width'] = None
        game_state['waiting_for_market'] = False

        if not reset_battle_round(game_state):
            flash("Could not load a new question!", 'error')
            game_state['game_over'] = True
            session['game_state'] = game_state
            return redirect(url_for('result'))

    if game_state['current_mover'] == 'player' and request.method == 'POST':
        action = request.form.get('action')
        
        if game_state['current_width'] is None:
            try:
                initial_width = int(request.form['initial_width'])
                if initial_width < 1:
                    flash("Initial width must be at least 1.", 'error')
                else:
                    game_state['current_width'] = initial_width
                    game_state['current_mover'] = 'bot'
                    session['game_state'] = game_state
                    return redirect(url_for('bot_turn'))
            except ValueError:
                flash("Invalid initial width.", 'error')

        elif action == 'reduce_width':
            try:
                new_width = int(request.form['width'])
                if new_width < 1:
                    flash("Width cannot be less than 1.", 'error')
                elif new_width > int(game_state['current_width'] * 0.9):
                    flash("Width reduction must be at least 10%.", 'error')
                else:
                    game_state['current_width'] = new_width
                    game_state['current_mover'] = 'bot'
                    session['game_state'] = game_state
                    return redirect(url_for('bot_turn'))
            except ValueError:
                flash("Invalid width value.", 'error')
        
        elif action == 'make_market':
            game_state['market_maker'] = 'player'
            game_state['current_mover'] = 'bot'
            session['game_state'] = game_state
            return redirect(url_for('bot_turn'))

        elif action == 'provide_market':
            try:
                bid = float(request.form['bid'])
                ask = float(request.form['ask'])
                if ask - bid != game_state['current_width']:
                    flash("The spread must equal the current width!", 'error')
                else:
                    game_state['bid'] = bid
                    game_state['ask'] = ask
                    game_state['market_made'] = True
                    game_state['current_mover'] = 'bot'
                    session['game_state'] = game_state
                    return redirect(url_for('bot_turn'))
            except ValueError:
                flash("Invalid bid or ask values.", 'error')

        # bot has made market
        elif action == 'trade':
            trade_action = request.form.get('trade_action')
            if trade_action not in ['buy', 'sell']:
                flash("Invalid trade action.", 'error')
            else:
                correct_price = game_state['true_answer']
                if trade_action == 'buy':
                    trade_price = game_state['ask']
                    damage = abs(correct_price - trade_price)
                else:  # sell
                    trade_price = game_state['bid']
                    damage = abs(trade_price - correct_price)

                # Calculate who won this round
                if (trade_action == 'buy' and correct_price < trade_price) or \
                   (trade_action == 'sell' and correct_price > trade_price):
                    game_state['player_capital'] -= damage
                    game_state['winner'] = 'bot'
                    game_state['last_round_winner'] = 'bot'
                else:
                    game_state['bot_capital'] -= damage
                    game_state['winner'] = 'player'
                    game_state['last_round_winner'] = 'player'

                game_state['last_round_damage'] = damage
                game_state['round_ended'] = True

                if game_state['player_capital'] <= 0:
                    game_state['game_over'] = True
                
                session['game_state'] = game_state
                return redirect(url_for('game'))

    elif game_state['current_mover'] == 'bot':
        return redirect(url_for('bot_turn'))

    show_initial_width_form = (game_state['current_width'] is None and 
                             game_state['current_mover'] == 'player')
    
    show_reduce_width_option = (game_state['current_width'] is not None and 
                              game_state['current_mover'] == 'player' and 
                              not game_state['market_made'])
    
    waiting_for_bot = game_state['current_mover'] == 'bot'

    session['game_state'] = game_state
    return render_template('game.html', 
                         game_state=game_state,
                         show_initial_width_form=show_initial_width_form,
                         show_reduce_width_option=show_reduce_width_option,
                         waiting_for_bot=waiting_for_bot)

@app.route('/bot_turn')
def bot_turn():
    game_state = session.get('game_state')
    if not game_state:
        return redirect(url_for('home'))

    bot = Bot.from_dict(game_state['bot'])

    # bot to trade
    if game_state['market_made'] and game_state['market_maker'] == 'bot':
        trade_action = bot.trade(game_state['bid'], game_state['ask'])
        correct_price = game_state['true_answer']
        
        if trade_action == 'buy':
            trade_price = game_state['ask']
            if trade_price > correct_price:
                damage = abs(correct_price - trade_price)
                game_state['bot_capital'] -= damage
                game_state['winner'] = 'player'
                game_state['bot_log'].append(f"Bot bought at {trade_price} (above true value {correct_price})")
                game_state['bot_log'].append(f"Bot takes damage: {damage}")
            else:
                damage = abs(correct_price - trade_price)
                game_state['player_capital'] -= damage
                game_state['winner'] = 'bot'
                game_state['bot_log'].append(f"Bot bought at {trade_price} (below true value {correct_price})")
                game_state['bot_log'].append(f"Player takes damage: {damage}")
        else:  # sell
            trade_price = game_state['bid']
            if trade_price < correct_price:
                damage = abs(trade_price - correct_price)
                game_state['bot_capital'] -= damage
                game_state['winner'] = 'player'
                game_state['bot_log'].append(f"Bot sold at {trade_price} (below true value {correct_price})")
                game_state['bot_log'].append(f"Bot takes damage: {damage}")
            else:
                damage = abs(trade_price - correct_price)
                game_state['player_capital'] -= damage
                game_state['winner'] = 'bot'
                game_state['bot_log'].append(f"Bot sold at {trade_price} (above true value {correct_price})")
                game_state['bot_log'].append(f"Player takes damage: {damage}")

        game_state['last_round_damage'] = damage
        game_state['round_summary'] = {
            'true_answer': correct_price,
            'trade_action': trade_action,
            'trade_price': trade_price,
            'damage': damage,
            'winner': game_state['winner']
        }
        
        flash(f"""Round Summary:
        True Answer: {correct_price}
        Bot {trade_action} at {trade_price}
        Damage Dealt: {damage}
        Winner: {game_state['winner']}
        New Player Capital: {game_state['player_capital']}
        New Bot Capital: {game_state['bot_capital']}""", 'info')

        #game over
        if game_state['bot_capital'] <= 0 or game_state['player_capital'] <= 0:
            game_state['game_over'] = True
            session['game_state'] = game_state
            return redirect(url_for('result'))
        
        #new round
        game_state['round_ended'] = True
        session['game_state'] = game_state
        return redirect(url_for('game'))

    if game_state['current_width'] is None:
        game_state['current_width'] = bot.generate_initial_width()
        game_state['current_mover'] = 'player'
        game_state['bot_log'].append(f"Bot set initial width: {game_state['current_width']}")
        
    elif game_state['market_maker'] == 'player' and not game_state['market_made']:
        game_state['bid'], game_state['ask'] = bot.make_market(game_state['current_width'])
        game_state['market_made'] = True
        game_state['bot_log'].append(f"Bot made market: Bid={game_state['bid']}, Ask={game_state['ask']}")
        game_state['current_mover'] = 'player'

    else:
        action = bot.choose_action(game_state['current_width'])
        game_state['bot_log'].append(f"Bot chooses to: {action}")

        if action == 'make_market':
            game_state['market_maker'] = 'bot'
            game_state['market_made'] = False 
            game_state['current_mover'] = 'player'
            game_state['waiting_for_market'] = True
            
        else: 
            new_width = int(round(game_state['current_width'] * bot.width_reduction_multiplier))
            game_state['current_width'] = max(1, new_width)
            game_state['current_mover'] = 'player'

    game_state['bot'] = bot.to_dict()
    session['game_state'] = game_state
    return redirect(url_for('game'))

@app.route('/result')
def result():
    game_state = session.get('game_state')
    if not game_state:
        flash("Game state not found.  Please start a new game.", 'error')
        return redirect(url_for('home'))

    winner = game_state.get('winner', 'unknown')
    true_answer = game_state.get('true_answer')
    units = game_state.get('units')
    bot_log = game_state.get('bot_log', [])
    damage = game_state.get('damage')
    player_capital = game_state.get('player_capital')
    bot_capital = game_state.get('bot_capital')
    market_maker = game_state.get('market_maker')
    bid = game_state.get('bid')
    ask = game_state.get('ask')

    session.clear()
    return render_template('result.html', winner=winner, answer=true_answer, units=units,
                           bot_log=bot_log, damage=damage, player_capital=player_capital,
                           bot_capital=bot_capital, market_maker=market_maker, bid=bid, ask=ask)

if __name__ == '__main__':
    app.run(debug=True)