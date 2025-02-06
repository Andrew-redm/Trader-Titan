import random
import abc

class Bot(abc.ABC):
    def __init__(self, true_value, initial_estimate_noise=0.5, std_dev_multiplier=4.0, width_reduction_multiplier=0.9, market_willingness=0.5):
        self.true_value = true_value
        self.initial_estimate_noise = initial_estimate_noise
        self.current_estimate = self.generate_initial_estimate()
        self.std_dev_multiplier = std_dev_multiplier
        self.log = []
        self.width_reduction_multiplier = width_reduction_multiplier
        self.market_willingness = market_willingness  # Base willingness

    def generate_initial_estimate(self):
        noise = random.uniform(-self.initial_estimate_noise, self.initial_estimate_noise)
        return self.true_value * (1 + noise)

    def generate_initial_width(self):
        initial_width = int(round(abs(self.current_estimate) * 2))
        return initial_width

    def _validate_market(self, bid, ask):
        std_dev = abs(self.current_estimate) * self.initial_estimate_noise
        min_value = max(0, int(round(self.current_estimate - self.std_dev_multiplier * std_dev)))
        bid = max(int(round(bid)), min_value)
        ask = max(int(round(ask)), int(round(min_value + 1)))
        if bid >= ask:
            ask = bid + 1
        return bid, ask

    @abc.abstractmethod
    def update_belief(self, player_action, player_width):
        pass

    @abc.abstractmethod
    def choose_action(self, current_width):
        pass

    @abc.abstractmethod
    def make_market(self, current_width):
        pass

    def get_log(self):
        return self.log

    @abc.abstractmethod
    def trade(self, bid, ask):
        pass



class AggressiveBot(Bot):
    def __init__(self, true_value, width_reduction_multiplier=0.8, market_willingness=0.7, initial_estimate_noise=0.5, std_dev_multiplier=4.0):  # Higher base willingness
        super().__init__(true_value, initial_estimate_noise, std_dev_multiplier, width_reduction_multiplier, market_willingness)

    def update_belief(self, player_action, player_width):
        if player_action == 'reduce_width':
            self.current_estimate = (self.current_estimate * (player_width + 1) + self.true_value) / (player_width + 2)
            self.log.append(f"Belief updated. New estimate: {self.current_estimate:.2f}")

    def choose_action(self, current_width):
        self.log.append(f"Current width: {current_width}, Current estimate: {self.current_estimate:.2f}")
        potential_bid = int(round(self.current_estimate - (current_width / 2)))
        potential_ask = int(round(self.current_estimate + (current_width / 2)))
        if self.current_estimate > self.true_value:
            potential_loss = abs(self.current_estimate - potential_bid)
        elif self.current_estimate < self.true_value:
            potential_loss = abs(potential_ask - self.current_estimate)
        else:
            potential_loss = current_width / 2
        uncertainty = abs(self.current_estimate) * self.initial_estimate_noise
        risk_threshold = uncertainty * self.market_willingness  # Use base willingness

        if potential_loss < risk_threshold:
            action = 'make_market'
        else:
            action = 'reduce_width'
        self.log.append(f"Choosing action: {action}, Potential Loss: {potential_loss}, Risk Threshold: {risk_threshold:.2f}")
        return action

    def make_market(self, current_width):
        bid = int(round(self.current_estimate - (current_width / 2)))
        ask = int(round(self.current_estimate + (current_width / 2)))
        bid, ask = self._validate_market(bid, ask)
        self.log.append(f"Making market: Bid={bid}, Ask={ask}")
        return bid, ask

    def trade(self, bid, ask):
        self.log.append(f"Bot trading after player made market.")
        self.log.append(f"Current estimate: {self.current_estimate:.2f}, Bid: {bid}, Ask: {ask}")
        if bid < 1:  # Handle low bid
            action = 'sell' if self.current_estimate < ask * 2 else 'buy'
        elif self.current_estimate > ask:
            action = 'buy'
        elif self.current_estimate < bid:
            action = 'sell'
        else:
            action = random.choice(['buy', 'sell'])
        self.log.append(f"Bot chooses to: {action}")
        return action


class PassiveBot(Bot):
    def __init__(self, true_value, width_reduction_multiplier=0.9, market_willingness=0.3, initial_estimate_noise=0.5, std_dev_multiplier=4.0):  # Lower base willingness
        super().__init__(true_value, initial_estimate_noise, std_dev_multiplier, width_reduction_multiplier, market_willingness)

    def update_belief(self, player_action, player_width):
        if player_action == 'reduce_width':
           self.current_estimate = (self.current_estimate * (player_width + 1) + self.true_value) / (player_width + 2) #Move towards center
           self.log.append(f"Belief updated. New estimate: {self.current_estimate:.2f}")

    def choose_action(self, current_width):
        self.log.append(f"Current width: {current_width}, Current estimate: {self.current_estimate:.2f}")
        potential_bid = int(round(self.current_estimate - (current_width / 2)))
        potential_ask = int(round(self.current_estimate + (current_width / 2)))
        if self.current_estimate > self.true_value:
            potential_loss = abs(self.current_estimate - potential_bid)
        elif self.current_estimate < self.true_value:
            potential_loss = abs(potential_ask - self.current_estimate)
        else:
            potential_loss = current_width / 2
        uncertainty = abs(self.current_estimate) * self.initial_estimate_noise
        risk_threshold = uncertainty * self.market_willingness * 1.5 # More risk-averse

        if potential_loss < risk_threshold:
            action = 'make_market'
        else:
            action = 'reduce_width'
        self.log.append(f"Choosing action: {action}, Potential Loss: {potential_loss}, Risk Threshold: {risk_threshold:.2f}")
        return action

    def make_market(self, current_width):
        bid = int(round(self.current_estimate - (current_width / 2)))
        ask = int(round(self.current_estimate + (current_width / 2)))
        bid, ask = self._validate_market(bid, ask) #Crucially validate
        self.log.append(f"Making market: Bid={bid}, Ask={ask}")
        return bid, ask

    def trade(self, bid, ask):
        self.log.append(f"Bot trading after player made market.")
        self.log.append(f"Current estimate: {self.current_estimate:.2f}, Bid: {bid}, Ask: {ask}")
        if bid < 1:  # Handle low bid
            action = 'sell' if self.current_estimate < ask * 2 else 'buy'
        elif self.current_estimate > ask:
            action = 'buy'
        elif self.current_estimate < bid:
            action = 'sell'
        else:
            action = random.choice(['buy', 'sell'])
        self.log.append(f"Bot chooses to: {action}")
        return action

class MarketLoverBot(Bot):
    def __init__(self, true_value, width_reduction_multiplier=0.85, market_willingness=0.9, initial_estimate_noise=0.5, std_dev_multiplier=4.0):  # Very high willingness
        super().__init__(true_value, initial_estimate_noise, std_dev_multiplier, width_reduction_multiplier, market_willingness)
        self.player_bias = 0 # Initialize player_bias

    def update_belief(self, player_action, player_width):
        if player_action == 'reduce_width':
            self.player_bias -= (player_width - self.true_value) /4
            self.current_estimate = (self.current_estimate + player_width/2) /2 #move towards the centre of the player's width
            self.log.append(f"Belief updated. New estimate: {self.current_estimate:.2f}, Player bias: {self.player_bias:.2f}")
        return

    def choose_action(self, current_width):
        self.log.append(f"Current width: {current_width}, Current estimate: {self.current_estimate:.2f}, Player Bias: {self.player_bias:.2f}")
        potential_bid = int(round(self.current_estimate - (current_width / 2)))
        potential_ask = int(round(self.current_estimate + (current_width / 2)))
        if self.current_estimate > self.true_value:
            potential_loss = abs(self.current_estimate - potential_bid)
        elif self.current_estimate < self.true_value:
            potential_loss = abs(potential_ask - self.current_estimate)
        else:
            potential_loss = current_width / 2
        uncertainty = abs(self.current_estimate) * self.initial_estimate_noise

        # Still considers risk, but with a very high threshold.
        risk_threshold = uncertainty * self.market_willingness * 0.8

        if potential_loss < risk_threshold:
             action = 'make_market'
        else:
             action = 'reduce_width'  # Still has *some* risk aversion
        self.log.append(f"Choosing action: {action}, Potential Loss: {potential_loss}, Risk Threshold: {risk_threshold:.2f}")

        return action

    def make_market(self, current_width):
        bid = int(round(self.current_estimate - (current_width / 2) - self.player_bias))
        ask = int(round(self.current_estimate + (current_width / 2) - self.player_bias))
        bid, ask = self._validate_market(bid, ask) #Crucially validate
        self.log.append(f"Making market: Bid={bid}, Ask={ask}")
        return bid, ask

    def trade(self, bid, ask):
        self.log.append(f"Bot trading after player made market.")
        self.log.append(f"Current estimate: {self.current_estimate:.2f}, Bid: {bid}, Ask: {ask}")
        if bid < 1:  # Handle low bid
            action = 'sell' if self.current_estimate < ask * 2 else 'buy'
        elif self.current_estimate > ask:
            action = 'buy'
        elif self.current_estimate < bid:
            action = 'sell'
        else:
            action = random.choice(['buy', 'sell'])
        self.log.append(f"Bot chooses to: {action}")
        return action

class MarketHaterBot(Bot):
    def __init__(self, true_value, width_reduction_multiplier=0.95, market_willingness=0.1, initial_estimate_noise = 0.5, std_dev_multiplier=4.0):  # Very low willingness, high reduction
        super().__init__(true_value,initial_estimate_noise, std_dev_multiplier, width_reduction_multiplier, market_willingness)
        self.player_bias = 0

    def update_belief(self, player_action, player_width):
        if player_action == 'reduce_width':
            self.player_bias -= (player_width - self.true_value) /4
            self.current_estimate = (self.current_estimate + player_width/2) /2 #move towards the centre of the player's width
            self.log.append(f"Belief updated. New estimate: {self.current_estimate:.2f}, Player bias: {self.player_bias:.2f}")
        return

    def choose_action(self, current_width):
        self.log.append(f"Current width: {current_width}, Current estimate: {self.current_estimate:.2f}, Player Bias: {self.player_bias:.2f}")
        potential_bid = int(round(self.current_estimate - (current_width / 2)))
        potential_ask = int(round(self.current_estimate + (current_width / 2)))
        if self.current_estimate > self.true_value:
            potential_loss = abs(self.current_estimate - potential_bid)
        elif self.current_estimate < self.true_value:
            potential_loss = abs(potential_ask - self.current_estimate)
        else:
            potential_loss = current_width / 2

        uncertainty = abs(self.current_estimate) * self.initial_estimate_noise

        # Very high risk aversion:
        risk_threshold = uncertainty * self.market_willingness * 2.0

        if potential_loss < risk_threshold:  # Very unlikely
            action = 'make_market'
        else:
            action = 'reduce_width'
        self.log.append(f"Choosing action: {action}, Potential Loss: {potential_loss}, Risk Threshold: {risk_threshold:.2f}")
        return action

    def make_market(self, current_width):
        bid = int(round(self.current_estimate - (current_width / 2)))
        ask = int(round(self.current_estimate + (current_width / 2)))
        bid, ask = self._validate_market(bid, ask) #Crucially validate
        self.log.append(f"Making market: Bid={bid}, Ask={ask}")
        return bid, ask

    def trade(self, bid, ask):
        self.log.append(f"Bot trading after player made market.")
        self.log.append(f"Current estimate: {self.current_estimate:.2f}, Bid: {bid}, Ask: {ask}")
        if bid < 1:  # Handle low bid
            action = 'sell' if self.current_estimate < ask * 2 else 'buy'
        elif self.current_estimate > ask:
            action = 'buy'
        elif self.current_estimate < bid:
            action = 'sell'
        else:
            action = random.choice(['buy', 'sell'])
        self.log.append(f"Bot chooses to: {action}")
        return action

class RandomBot(Bot):
    def __init__(self, true_value, initial_estimate_noise=0.5, std_dev_multiplier=4.0,  width_reduction_multiplier=0.9, market_willingness=0.5):
        super().__init__(true_value, initial_estimate_noise, std_dev_multiplier, width_reduction_multiplier, market_willingness)


    def update_belief(self, player_action, player_width):
        self.log.append("Belief not updated (RandomBot).")
        return

    def choose_action(self, current_width):
        self.log.append(f"Current width: {current_width}, Current estimate: {self.current_estimate:.2f}")
        # Truly random choice:
        action = random.choice(['reduce_width', 'make_market'])
        self.log.append(f"Choosing action: {action}")
        return action

    def make_market(self, current_width):
        bid = int(round(self.current_estimate - (current_width / 2)))
        ask = int(round(self.current_estimate + (current_width / 2)))
        bid, ask = self._validate_market(bid, ask) #Crucially validate
        self.log.append(f"Making market: Bid={bid}, Ask={ask}")
        return bid, ask

    def trade(self, bid, ask):
        self.log.append(f"Bot trading after player made market.")
        self.log.append(f"Current estimate: {self.current_estimate:.2f}, Bid: {bid}, Ask: {ask}")
        if self.current_estimate > ask:
            action = 'buy'
        elif self.current_estimate < bid:
            action = 'sell'
        else:
            action = random.choice(['buy', 'sell'])
        self.log.append(f"Bot chooses to: {action}")
        return action