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

    def to_dict(self):
        """Converts the bot object to a dictionary."""
        return {
            'true_value': self.true_value,
            'initial_estimate_noise': self.initial_estimate_noise,
            'current_estimate': self.current_estimate,
            'std_dev_multiplier': self.std_dev_multiplier,
            'log': self.log,
            'width_reduction_multiplier': self.width_reduction_multiplier,
            'market_willingness': self.market_willingness,
            '__class__': self.__class__.__name__  # Store the class name!
        }

    @staticmethod
    def from_dict(data):
        """Creates a bot object from a dictionary."""
        class_name = data.pop('__class__')  # Get and remove the class name
        log = data.pop('log') #Get the log, and remove that entry.  <-- **THIS LINE**
        if class_name == 'AggressiveBot':
            return AggressiveBot(**data, log=log)  # Pass log explicitly <-- **AND THIS LINE**
        elif class_name == 'PassiveBot':
            return PassiveBot(**data, log=log) # <-- **AND HERE**
        elif class_name == 'MarketLoverBot':
            return MarketLoverBot(**data, log=log) # <-- **AND HERE**
        elif class_name == 'MarketHaterBot':
            return MarketHaterBot(**data, log=log) # <-- **AND HERE**
        elif class_name == 'RandomBot':
            return RandomBot(**data, log=log) # <-- **AND HERE**
        else:
            raise ValueError(f"Unknown bot class: {class_name}")

class AggressiveBot(Bot):
    def __init__(self, true_value, initial_estimate_noise=0.5, std_dev_multiplier=4.0, width_reduction_multiplier=0.8, market_willingness=0.7, current_estimate=None, log=None):
        super().__init__(true_value, initial_estimate_noise, std_dev_multiplier, width_reduction_multiplier, market_willingness)
        self.current_estimate = current_estimate if current_estimate is not None else self.generate_initial_estimate()
        self.log = log if log is not None else []
    # ... rest of AggressiveBot ...
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
    def __init__(self, true_value, initial_estimate_noise=0.6, std_dev_multiplier=4.0, width_reduction_multiplier=0.95, market_willingness=0.3, current_estimate=None, log=None):
        super().__init__(true_value, initial_estimate_noise, std_dev_multiplier, width_reduction_multiplier, market_willingness)
        self.current_estimate = current_estimate if current_estimate is not None else self.generate_initial_estimate()
        self.log = log if log is not None else []

    def update_belief(self, player_action, player_width):
        if player_action == 'reduce_width':
            # Passive bot updates its belief less aggressively
            self.current_estimate = (self.current_estimate * (player_width + 5) + self.true_value) / (player_width + 6)
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
        bid, ask = self._validate_market(bid, ask)  # Ensure bid < ask
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
    def __init__(self, true_value, initial_estimate_noise=0.4, std_dev_multiplier=4.0, width_reduction_multiplier=0.95, market_willingness=0.9, current_estimate=None, log=None):
        super().__init__(true_value, initial_estimate_noise, std_dev_multiplier, width_reduction_multiplier, market_willingness)
        self.current_estimate = current_estimate if current_estimate is not None else self.generate_initial_estimate()
        self.log = log if log is not None else []

    def update_belief(self, player_action, player_width):
        if player_action == 'reduce_width':
            # Market-loving bot updates its belief very slightly
            self.current_estimate = (self.current_estimate * (player_width + 10) + self.true_value) / (player_width + 11)
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
        # Market-loving bot is *very* willing to make a market
        if potential_loss < risk_threshold * 2:  # Higher tolerance
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

class MarketHaterBot(Bot):
    def __init__(self, true_value, initial_estimate_noise=0.6, std_dev_multiplier=4.0, width_reduction_multiplier=0.8, market_willingness=0.1, current_estimate=None, log=None):
        super().__init__(true_value, initial_estimate_noise, std_dev_multiplier, width_reduction_multiplier, market_willingness)
        self.current_estimate = current_estimate if current_estimate is not None else self.generate_initial_estimate()
        self.log = log if log is not None else []

    def update_belief(self, player_action, player_width):
        if player_action == 'reduce_width':
            # Market-hating bot updates belief somewhat aggressively
            self.current_estimate = (self.current_estimate * (player_width + 2) + self.true_value * 0.8) / (
                        player_width + 2.8)
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

        # Market-hating bot is *very* reluctant to make a market
        if potential_loss < risk_threshold * 0.2:  # Much lower tolerance
            action = 'make_market'
        else:
            action = 'reduce_width'
        self.log.append(f"Choosing action: {action}, Potential Loss: {potential_loss}, Risk Threshold: {risk_threshold:.2f}")
        return action

    def make_market(self, current_width):
        # Market-hating bot makes a wider market
        bid = int(round(self.current_estimate - (current_width * 0.75)))
        ask = int(round(self.current_estimate + (current_width * 0.75)))
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

class RandomBot(Bot):
    def __init__(self, true_value, initial_estimate_noise=0.5, std_dev_multiplier=4.0, width_reduction_multiplier=0.85, market_willingness=0.5, current_estimate=None, log=None):
        super().__init__(true_value, initial_estimate_noise, std_dev_multiplier, width_reduction_multiplier, market_willingness)
        self.current_estimate = current_estimate if current_estimate is not None else self.generate_initial_estimate()
        self.log = log if log is not None else []


    def update_belief(self, player_action, player_width):
        if player_action == 'reduce_width':
            # Random bot updates its belief randomly
            self.current_estimate = (self.current_estimate * (player_width + random.uniform(1,5)) + self.true_value * random.uniform(0.7, 1.3)) / (player_width + random.uniform(1.7, 6.3))
            self.log.append(f"Belief updated. New estimate: {self.current_estimate:.2f}")

    def choose_action(self, current_width):
        self.log.append(f"Current width: {current_width}, Current estimate: {self.current_estimate:.2f}")
        # Random bot chooses an action randomly
        action = random.choice(['reduce_width', 'make_market'])
        self.log.append(f"Choosing action: {action}")
        return action

    def make_market(self, current_width):
        # Random bot makes a somewhat random market
        bid = int(round(self.current_estimate - (current_width * random.uniform(0.4, 0.6))))
        ask = int(round(self.current_estimate + (current_width * random.uniform(0.4, 0.6))))
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