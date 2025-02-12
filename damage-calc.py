import math

def calculate_damage_option1(true_answer, bid, ask, player_action):
    market_width = ask - bid #not used
    if bid <= true_answer <= ask:
        if player_action == 'buy':
            error = abs(true_answer - ask)
        else:  # player_action == 'sell'
            error = abs(true_answer - bid)
    else:
        error = abs(true_answer - (bid if true_answer < bid else ask))

    percentage_error = (error / true_answer) * 100
    damage = int(round(percentage_error * 10))  #factor can be improved
    return damage

def calculate_damage_option2(true_answer, bid, ask, player_action):
    market_width = ask - bid
    if bid <= true_answer <= ask:
        if player_action == 'buy':
            error = abs(true_answer - ask)
        else:  # player_action == 'sell'
            error = abs(true_answer - bid)
    else:
        error = abs(true_answer - (bid if true_answer < bid else ask))

    percentage_error = (error / market_width) * 100
    damage = int(round(percentage_error * 10))
    return damage

def calculate_damage_option3(true_answer, bid, ask, player_action):
    market_width = ask - bid
    if bid <= true_answer <= ask:
        if player_action == 'buy':
            error = abs(true_answer - ask)
        else:
            error = abs(true_answer - bid)
    else:
        error = abs(true_answer - (bid if true_answer < bid else ask))

    normalized_error = error / (true_answer + market_width)
    damage = int(round(normalized_error * 10000))
    return damage

def calculate_damage_option4(true_answer, bid, ask, player_action):
    market_width = ask-bid #still needed for consistency
    if bid <= true_answer <= ask:
        if player_action == 'buy':
            error = abs(true_answer - ask)
        else:
            error = abs(true_answer-bid)
    else:
        error = abs(true_answer - (bid if true_answer < bid else ask))

    normalized_error = error / true_answer  # Using Option 1's normalization
    damage = int(round(10000 * math.log(1 + normalized_error)))  # Scaling factor of 1000, natural log
    return damage

def main():
    print("Trader Titan Damage Calculator")

    while True:
        try:
            true_answer = float(input("Enter the true answer (or 'q' to quit): "))
            if str(true_answer).lower() == 'q':
                break

            bid = float(input("Enter the bid: "))
            ask = float(input("Enter the ask: "))

            if bid >= ask:
                print("Error: Bid must be less than ask.")
                continue

            player_action = input("Enter player action ('buy' or 'sell'): ").lower()
            if player_action not in ('buy', 'sell'):
                print("Error: Invalid player action. Must be 'buy' or 'sell'.")
                continue

            damage1 = calculate_damage_option1(true_answer, bid, ask, player_action)
            damage2 = calculate_damage_option2(true_answer, bid, ask, player_action)
            damage3 = calculate_damage_option3(true_answer, bid, ask, player_action)
            damage4 = calculate_damage_option4(true_answer, bid, ask, player_action)

            print("\nDamage Calculations:")
            print(f"  Option 1 (Percentage of True Answer): {damage1}")
            print(f"  Option 2 (Percentage of Market Width): {damage2}")
            print(f"  Option 3 (Combination): {damage3}")
            print(f"  Option 4 (Logarithmic): {damage4}")
            print("-" * 30)

        except ValueError:
            print("Invalid input. Please enter numeric values.")
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()