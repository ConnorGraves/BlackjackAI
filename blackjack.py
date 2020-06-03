import random
import unittest

class Game:
	def __init__(self, deck = None, p_hand = None, d_hand = None, budget = None, winnings = None, d_stay = None, turn = None):
		if deck is None:
			#The index represents the card value, the element represents the number of that card value in the deck
			#Because the cards 10, J, Q, K all have a value of 10, they are aggregated together.
			self.deck = [4,4,4,4,4,4,4,4,4,16]
		else:
			self.deck = deck

		if p_hand is None:
			self.p_hand = []
		else:
			self.p_hand = p_hand

		if d_hand is None:
			self.d_hand = []
		else:
			self.d_hand = d_hand

		if budget is None:
			self.budget = 1.0
		else:
			self.budget = budget

		if winnings is None:
			self.winnings = 0.0
		else:
			self.winnings = winnings

		if d_stay is None:
			self.d_stay = 21
		else:
			self.d_stay = d_stay

		if turn is None:
			self.turn = "Player"
		else:
			self.turn = turn

	def play(self, bet = None):
		doubled_down = 1
		can_double_down = False
		self.p_hand = []
		self.d_hand = []
		self.player_draw()
		self.player_draw()
		self.dealer_draw()
		self.dealer_draw()

		# on first move selection, if player hand is worth 9, 10, or 11 they may double down
		if self.score_p_hand() >= 9 and self.score_p_hand() <= 11:
			can_double_down = True

		if bet is None:
			print("Available Funds: ${0:.2f}\nEnter Bet Amount: ".format(self.budget + self.winnings))
			bet = float(input())
			while bet > self.budget + self.winnings:
				print("You can not bet more than the amount of money you have.\nAvailable Funds: ${}\nEnter Bet Amount: ".format(self.budget + self.winnings))
				bet = float(input())

		if bet > self.budget + self.winnings:
			raise ValueError("You can not bet more than the amount of money you have. \nAttempted Bet: {}\nAvailable Funds: {}".format(bet, self.budget + self.winnings))

		#if first two cards are 21, player automatically wins 1.5x bet instead of 2x
		if self.score_p_hand() == 21:
			self.turn = "End"
			self.print_hands()
			if self.score_d_hand() != 21:
				print("Blackjack! You win 1.5x your bet!")
				self.winnings += bet * 1.5
			else:
				print("Stand-off: Your bet has been returned.")
			self.turn = "Player"
			return
		#if dealer has 21 on first hand and player doesn't, dealer wins
		elif self.score_d_hand() == 21:
			self.turn = "End"
			self.print_hands()
			print("Dealer Blackjack. You Lose.")
			self.winnings -= bet
			self.turn = "Player"
			return


		while self.turn is not "End":
			self.print_hands()

			if self.turn == "Player":
				
				if can_double_down:
					print("\n\nSelect an action:\n1) Hit\n2) Stay\n3) Double Down")
					action = int(input())
					while action < 1 or action > 3:
						print("\n\nSelect an action:\n1) Hit\n2) Stay\n3) Double Down")
						action = int(input())

				else:
					print("\n\nSelect an action:\n1) Hit\n2) Stay")
					action = int(input())
					while action < 1 or action > 2:
						print("\n\nSelect an action:\n1) Hit\n2) Stay")
						action = int(input())

				can_double_down = False

				#~~~~~~~~~~~~~ Hit ~~~~~~~~~~~~~
				if action == 1: 
					self.player_draw()
					if self.score_p_hand() > 21:
						self.turn = 'End'

				#~~~~~~~~~~~~~ Stay ~~~~~~~~~~~~~
				elif action == 2:
					self.turn = 'Dealer'

				#~~~~~~~~~~~~~ Double Down ~~~~~~~~~~~~~
				elif action == 3:
					doubled_down = 2
					self.player_draw()
					if self.score_p_hand() > 21:
						self.turn = 'End'
					else:
						self.turn = 'Dealer'

			elif self.turn == "Dealer":
				# Hit if not bust yet, hand value is less than player's, and dealer stay rule has not been reached
				if self.score_d_hand() < self.d_stay and self.score_d_hand() <= self.score_p_hand() and self.score_d_hand() < 21:
					print("~~~~~~~~ Dealer Hits ~~~~~~~~")
					self.dealer_draw()
				# else stay
				else:
					print("~~~~~~~~ Dealer Stays ~~~~~~~~")
					self.turn = 'End'

			# Failsafe for invalid turn state: Just end the game
			else:
				print("Invalid Turn State: Game Ending")
				self.turn = 'End'

		#Hand has ended: Evaluate Result
		print("\nEnd State Reached")
		self.print_hands()
		print("   Dealer Score: {}\n   Player Score: {}".format(self.score_d_hand(), self.score_p_hand()))

		# Player Loss Condition
		if self.score_p_hand() > 21 or (self.score_p_hand() < self.score_d_hand() and self.score_d_hand() <= 21):
			print("You Lose")
			self.winnings -= bet * doubled_down

		# Draw Condition
		elif self.score_p_hand() == self.score_d_hand():
			print("Draw")

		# Player Win Condition
		elif self.score_p_hand() > self.score_d_hand() or self.score_d_hand() > 21:
			print("You Win")
			self.winnings += bet * doubled_down

		self.turn = "Player"

	def print_hands(self):
		print("\nDealer Hand:\t", end = '')
		# Keep second card facedown
		if self.turn == "Player":
			print(self.convert_value_to_card(self.d_hand[0]), end = ' #')
		else:
			for value in self.d_hand:
				print(self.convert_value_to_card(value), end = ' ')

		print("\nPlayer Hand:\t", end = '')
		for value in self.p_hand:
			print(self.convert_value_to_card(value), end = ' ')

		print("\n")

	@staticmethod
	def convert_value_to_card(value):
		if value == 0:
			return 'A'
		else:
			return str(value + 1)


	def player_draw(self, value = None):
		if value is None:
			if self.deck_is_empty():
				raise ValueError('Deck is empty: Cannot draw a card.')

			eligible_values = []
			for i in range(0,10):
				if self.deck[i] > 0:
					eligible_values.append(i)

			value = random.choice(eligible_values)

		if self.deck[value] <= 0:
			raise ValueError("Deck has no more {}'s to draw.".format(self.convert_value_to_card(value)))

		self.deck[value] = self.deck[value] - 1
		self.p_hand.append(value)

	def dealer_draw(self, value = None):
		if value is None:
			if self.deck_is_empty():
				raise ValueError('Deck is empty: Cannot draw a card.')

			eligible_values = []
			for i in range(0,10):
				if self.deck[i] > 0:
					eligible_values.append(i)

			value = random.choice(eligible_values)

		if self.deck[value] <= 0:
			raise ValueError("Deck has no more {}'s to draw.".format(self.convert_value_to_card(value)))

		self.deck[value] = self.deck[value] - 1
		self.d_hand.append(value)

	def score_p_hand(self):
		numAces = 0
		score = 0

		#score all cards as value except for aces, which must be scored last.
		#track number of aces for later
		for card in self.p_hand:
			if card == 0:
				numAces += 1
			else:
				score += card + 1

		#we will never score more than one ace as 11, so all but one will be worth 1
		if numAces > 1:
			score += numAces - 1
			numAces = 1

		#if score is greater than 10, adding 11 will bust, so we score the last ace as 1.
		#otherwise, we score the final ace as 11
		if numAces == 1:
			if score > 10:
				score += 1
			else:
				score += 11

		return score

	def score_d_hand(self):
		numAces = 0
		score = 0

		#score all cards as value except for aces, which must be scored last.
		#track number of aces for later
		for card in self.d_hand:
			if card == 0:
				numAces += 1
			else:
				score += card + 1

		#we will never score more than one ace as 11, so all but one will be worth 1
		if numAces > 1:
			score += numAces - 1
			numAces = 1

		#if score is greater than 10, adding 11 will bust, so we score the last ace as 1.
		#otherwise, we score the final ace as 11
		if numAces == 1:
			if score > 10:
				score += 1
			else:
				score += 11

		return score
		
	def deck_is_empty(self):
		return self.deck == ([0] * 10)

	def add_deck(self, deck = None):
		if deck is None:
			deck = [4,4,4,4,4,4,4,4,4,16]

		for i in range(0, len(self.deck)):
			self.deck[i] += deck[i]


class TestBlackjackClass(unittest.TestCase):

	def test_add_deck(self):
		game = Game()
		game.add_deck()
		self.assertEqual(game.deck, [8,8,8,8,8,8,8,8,8,32])
		game = Game()
		game.add_deck([1,2,3,0,0,0,0,0,0,100])
		self.assertEqual(game.deck, [5,6,7,4,4,4,4,4,4,116])

	def test_deck_is_empty(self):
		game = Game()
		self.assertFalse(game.deck_is_empty())

		game = Game(deck = [0] * 10)
		self.assertTrue(game.deck_is_empty())

	def test_player_draw(self):
		game = Game()
		game.player_draw()
		self.assertEqual(1, len(game.p_hand))
		self.assertTrue(game.deck[game.p_hand[0]] == 3 or game.deck[game.p_hand[0]] == 15)

		game = Game()
		game.player_draw(3)
		self.assertEqual(3, game.p_hand[0])
		self.assertEqual(3, game.deck[3])

		game = Game(deck = [0] * 10)
		with self.assertRaises(ValueError, msg='Deck is empty: Cannot draw a card.'):
			game.player_draw()

		game = Game(deck = [1,0,0,0,0,0,0,0,0,1])
		with self.assertRaises(ValueError, msg="Deck has no more 2's to draw."):
			game.player_draw(1)

	def test_dealer_draw(self):
		game = Game()
		game.dealer_draw()
		self.assertEqual(1, len(game.d_hand))
		self.assertTrue(game.deck[game.d_hand[0]] == 3 or game.deck[game.d_hand[0]] == 15)

		game = Game()
		game.dealer_draw(3)
		self.assertEqual(3, game.d_hand[0])
		self.assertEqual(3, game.deck[3])

		game = Game(deck = [0] * 10)
		with self.assertRaises(ValueError, msg='Deck is empty: Cannot draw a card.'):
			game.dealer_draw()

		game = Game(deck = [1,0,0,0,0,0,0,0,0,1])
		with self.assertRaises(ValueError, msg="Deck has no more 2's to draw."):
			game.dealer_draw(1)

	def test_score_p_hand(self):
		game = Game()
		self.assertEqual(0, game.score_p_hand())

		game = Game(p_hand = [1, 2, 3, 4, 5, 6, 7, 8, 9])
		self.assertEqual(54, game.score_p_hand())

		game = Game(p_hand = [0, 0, 0, 0])
		self.assertEqual(14, game.score_p_hand())

		game = Game(p_hand = [0, 9])
		self.assertEqual(21, game.score_p_hand())

		game = Game(p_hand = [0, 0, 8])
		self.assertEqual(21, game.score_p_hand())

	def test_score_d_hand(self):
		game = Game()
		self.assertEqual(0, game.score_d_hand())

		game = Game(d_hand = [1, 2, 3, 4, 5, 6, 7, 8, 9])
		self.assertEqual(54, game.score_d_hand())

		game = Game(d_hand = [0, 0, 0, 0])
		self.assertEqual(14, game.score_d_hand())

		game = Game(d_hand = [0, 9])
		self.assertEqual(21, game.score_d_hand())

		game = Game(d_hand = [0, 0, 8])
		self.assertEqual(21, game.score_d_hand())

if __name__ == '__main__':
	#Run Unit Tests
	#unittest.main()

	#Play on loop
	game = Game(budget = 30.00, d_stay = 17)
	for i in range(0, 15):
		print("\n===== GAME {0} of 15 =====\nFunds: ${1:.2f}".format(i+1, game.budget + game.winnings))
		#if deck gets too small (less than 20 cards), add another deck to it and shuffle
		if sum(game.deck) < 20:
			print("Shuffling in a new deck...")
			game.add_deck()
		game.play(bet = 1)

	print("\nALL GAMES PLAYED!\nEnding Funds: ${0:.2f}".format(game.budget + game.winnings))



