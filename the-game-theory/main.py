class GameTheory:
    def __init__(self):
        self.players = []
        self.payoffs = {}

    def add_player(self, player):
        self.players.append(player)

    def set_payoff(self, player1, player2, payoff):
        self.payoffs[(player1, player2)] = payoff

    def get_payoff(self, player1, player2):
        return self.payoffs.get((player1, player2), None)

    def play(self):
        # Implement the game logic here
        pass

    