# Blackjack Monte Carlo Tree Search
# California Polytechnic State University
# Computer Science Department
# Senior Project Spring 2020
# Connor Graves

# Adapted from Tic-Tac-Toe MCTS Lab designed by 
# Morgan Swanson for Dr. Franz Kurfess's CSC 480

from blackjack import *
import random
import numpy as np 
import math
import copy
from tqdm import tqdm
import csv

aggression = 1.0

def get_possible_actions(game, action_history):
  actions = []
  if game.turn == "Player":
    actions.append(action_history + "Ph")
    actions.append(action_history + "Ps")
    # on first action selection, if player hand is worth 9, 10, or 11 they may double down
    if action_history == "" and game.score_p_hand() >= 9 and game.score_p_hand() <= 11:
      actions.append(action_history + "Pd")

  elif game.turn == "Dealer":
    # dealer follows set rules
    # hits if not bust yet, hand value is less than player's and less than stay limit
    if game.score_d_hand() < game.d_stay and game.score_d_hand() <= game.score_p_hand() and game.score_d_hand() < 21:
      actions.append(action_history + "Dh")
    # otherwise, always stays
    else:
      actions.append(action_history + "Ds")

  return actions

class Metrics:
  def __init__(self):
    self.wins = 0
    self.draws = 0
    self.played = 0

  # update with the result of a simulation
  def update(self, result):
    self.played = self.played + max(1, abs(result))

    # Player Loss Condition
    if result < 0:
      pass

    # Draw Condition
    elif result == 0:
      self.draws = self.draws + 1

    # Player Win Condition
    elif result > 0:
      self.wins = self.wins + result

  # get the win percentage of a metric
  # a draw is worth something, but less than a win, 
  # so we skew to more draws than losses if needed
  def get_win_percentage(self):
    try:
      return (self.wins + (self.draws / 2)) / self.played
    except ZeroDivisionError:
      return -1

  # calculate a component of the UCB to determine viability of option
  def get_explore_term(self, parent, c = 1.41):
    if self.played > 0:
      #c times the square root of natural log of sims run by parent
      #divided by sims run by this state
      return c * (math.log(parent.played) / self.played) ** .5 
    else:
      return 0

  # calculate UCB, or return a very high UCB if never visited before to
  # incentivise trying options at least once
  def get_upper_confidence_bound(self, parent, default = 6):
    if self.played > 0:
      return self.get_win_percentage() + self.get_explore_term(parent)
    else:
      return default

def select_action(game, actions, action_history):
  possible_actions = get_possible_actions(game, actions)

  # initialize policy vector beginning with equal chance for all possible actions
  policy_vector = np.ones(len(possible_actions)) / len(possible_actions)

  # fill policy vector with all UCBs
  i = 0
  for a in possible_actions:
    # if we haven't done this combination of moves yet, init metrics
    if a not in action_history:
      action_history[a] = Metrics()
    policy_vector[i] = action_history[a].get_upper_confidence_bound(action_history[actions])
    
    # adjust policy vector by aggression factor
    if a[-2:] == 'Ph' or a[-2:] == 'Pd':
      policy_vector[i] *= aggression
    elif a[-2:] == 'Ps':
      policy_vector[i] /= aggression

    i += 1

  # convert UCBs to selection probabilities
  policy_sum = np.sum(policy_vector)
  if policy_sum != 0:
    policy_vector = policy_vector / policy_sum
  else:
    # choose randomly if you can't win
    policy_vector = np.ones(len(possible_actions)) / len(possible_actions)

  # randomly select an action based on probabilities stored in policy vector
  selected_action = possible_actions[np.random.choice(np.arange(len(possible_actions), dtype=int),
                                    1, 
                                    p=policy_vector)[0]]
  return selected_action

#   -1: player loss
#    0: draw
#    1: player win
# None: Game incomplete
def get_score(game, actions):
  #only update metrics if game is finished
    if game.turn == "End":
      p_score = game.score_p_hand()
      d_score = game.score_d_hand()

      if "Pd" in actions:
        mod = 2
      else:
        mod = 1

      # Player Loss Condition
      if p_score > 21 or (p_score < d_score and d_score <= 21):
        return -1 * mod

      # Draw Condition
      elif p_score == d_score:
        return 0

      # Player Win Condition
      elif p_score > d_score or d_score > 21:
        return 1 * mod

    return None

def run_simulations(game, actions, action_history, count = 1000):
  if actions not in action_history:
    action_history[actions] = Metrics()

  for i in tqdm(range(count), mininterval = 0.2):
    path = [actions]
    game_path = [game]
    result = get_score(game, actions)

    while result is None:
      child = select_action(game_path[-1], path[-1], action_history)
      if child not in action_history:
        action_history[child] = Metrics()
      path.append(child)
      #last two letters of action string are the next action to take
      actionCode = child[-2:] 
      
      child_game = copy.deepcopy(game_path[-1])
      child_game = make_move(child_game, actionCode)

      game_path.append(child_game)
      result = get_score(game_path[-1], child)

    for a in path:
      action_history[a].update(result)

def make_move(game, actionCode):
  # player hit
  if actionCode == "Ph":
    game.player_draw()
    if game.score_p_hand() > 21:
      game.turn = 'End'

  # player stay
  elif actionCode == "Ps":
    game.turn = "Dealer"

  # player double down
  elif actionCode == "Pd":
    game.player_draw()
    if game.score_p_hand() > 21:
      game.turn = 'End'
    else:
      game.turn = 'Dealer'

  # dealer hit
  elif actionCode == "Dh":
    game.dealer_draw()

  # dealer stay
  elif actionCode == "Ds":
    game.turn = "End"

  else:
    raise ValueError(actionCode + ' is not a valid action.')

  return game

def update_balance(game, actions, bet):
  dd_modifier = 1
  if game.turn == "End":
    # if player doubled down, double the original bet amount
    if "Pd" in actions:
      dd_modifier = 2

    # Player Loss Condition
    if game.score_p_hand() > 21 or (game.score_p_hand() < game.score_d_hand() and game.score_d_hand() <= 21):
      game.winnings -= bet * dd_modifier

    # Player Win Condition
    elif game.score_p_hand() > game.score_d_hand() or game.score_d_hand() > 21:
      game.winnings += bet * dd_modifier

    # draw does nothing to winnings

def action_to_text(actions):
  message = "The AI reccomends that you "
  if actions[-2:] == 'Ph':
    message = message + "hit"
  elif actions[-2:] == 'Ps':
    message = message + "stay"
  elif actions[-2:] == 'Pd':
    message = message + "double down"
  return message

def reccomend_action(game, actions):
  # create a game that doesn't know the real facedown card
  # the dealer will automatically draw an extra card at the beginning of 
  # its turn to compensate
  temp_game = copy.deepcopy(game)
  dealer_facedown = temp_game.d_hand[-1]   # check facedown card
  temp_game.deck[dealer_facedown] += 1     # add facedown back to deck
  temp_game.d_hand = temp_game.d_hand[:-1] # remove facedown card from hand

  action_history = {}

  if actions not in action_history:
    action_history[actions] = Metrics()

  run_simulations(temp_game, actions, action_history)
  possible_actions = get_possible_actions(temp_game, actions)
  values = [action_history[a].get_win_percentage() for a in possible_actions]

  print(action_to_text(str(possible_actions[np.argmax(values)])) + 
                          " ({:.1f}% confidence)".format(np.max(values)*100))
  
  return str(possible_actions[np.argmax(values)])[-2:]

def play(game, bet = None, reccs = True, auto = False):
  if reccs == False:
    game.play(bet)
  else:
    actions = ""
    action_history = {}
    can_double_down = False
    doubled_down = 1
    game.p_hand = []
    game.d_hand = []
    game.player_draw()
    game.player_draw()
    game.dealer_draw()
    game.dealer_draw()

    # on first move selection, if player hand is worth 9, 10, or 11 they may double down
    if game.score_p_hand() >= 9 and game.score_p_hand() <= 11:
      can_double_down = True

    if bet is None:
      print("Available Funds: ${0:.2f}\nEnter Bet Amount: ".format(game.budget + game.winnings))
      bet = float(input())
      while bet > game.budget + game.winnings:
        print("You can not bet more than the amount of money you have.\nAvailable Funds: ${}\nEnter Bet Amount: ".format(game.budget + game.winnings))
        bet = float(input())

    if bet > game.budget + game.winnings:
      raise ValueError("You can not bet more than the amount of money you have. \nAttempted Bet: {}\nAvailable Funds: {}".format(bet, game.budget + game.winnings))

    #if first two cards are 21, player automatically wins 1.5x bet instead of 2x
    if game.score_p_hand() == 21:
      game.turn = "End"
      game.print_hands()
      if game.score_d_hand() != 21:
        print("Blackjack! You win 1.5x your bet!")
        game.winnings += bet * 1.5
      else:
        print("Stand-off: Your bet has been returned.")
      game.turn = "Player"
      return
    #if dealer has 21 on first hand and player doesn't, dealer wins
    elif game.score_d_hand() == 21:
      game.turn = "End"
      game.print_hands()
      print("Dealer Blackjack. You Lose.")
      game.winnings -= bet
      game.turn = "Player"
      return

    while game.turn is not "End":
      game.print_hands()

      if game.turn == "Player":
        print("Running simulations...")
        sim_result = reccomend_action(game, actions)
        if auto:
          if sim_result == "Ph":
            action = 1
          elif sim_result == "Ps":
            action = 2
          elif sim_result == "Pd":
            action = 3
        else:
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
          actions = actions + "Ph"
          game.player_draw()
          if game.score_p_hand() > 21:
            game.turn = 'End'

        #~~~~~~~~~~~~~ Stay ~~~~~~~~~~~~~
        elif action == 2:
          actions = actions + "Ps"
          game.turn = 'Dealer'

        #~~~~~~~~~~~~~ Double Down ~~~~~~~~~~~~~
        elif action == 3:
          actions = actions + "Pd"
          doubled_down = 2
          game.player_draw()
          if game.score_p_hand() > 21:
            game.turn = 'End'
          else:
            game.turn = 'Dealer'

      elif game.turn == "Dealer":
        # Hit if not bust yet, hand value is less than player's, and dealer stay rule has not been reached
        if game.score_d_hand() < game.d_stay and game.score_d_hand() <= game.score_p_hand() and game.score_d_hand() < 21:
          actions = actions + "Dh"
          print("~~~~~~~~ Dealer Hits ~~~~~~~~")
          game.dealer_draw()
        # else stay
        else:
          actions = actions + "Ds"
          print("~~~~~~~~ Dealer Stays ~~~~~~~~")
          game.turn = 'End'

      # Failsafe for invalid turn state: Just end the game
      else:
        print("Invalid Turn State: Game Ending")
        game.turn = 'End'

    #Hand has ended: Evaluate Result
    print("\nEnd State Reached")
    game.print_hands()
    print("   Dealer Score: {}\n   Player Score: {}".format(game.score_d_hand(), game.score_p_hand()))

    # Player Loss Condition
    if game.score_p_hand() > 21 or (game.score_p_hand() < game.score_d_hand() and game.score_d_hand() <= 21):
      print("You Lose")
      game.winnings -= bet * doubled_down

    # Draw Condition
    elif game.score_p_hand() == game.score_d_hand():
      print("Draw")

    # Player Win Condition
    elif game.score_p_hand() > game.score_d_hand() or game.score_d_hand() > 21:
      print("You Win")
      game.winnings += bet * doubled_down

    game.turn = "Player"

def evaluate_deck(deck, numdecks):
  # higher values favor player, lower values favor house
  value = 0.0
  # subtract 1 for each card with value 2-6
  value -= sum(deck[1:6])
  # add 1 for each card A 10 J Q K
  value += sum(deck[-1:]) + deck[0]
  # divide by number of decks remaining to get a true count that reflects the concentration of high cards
  value = value / float(max(1, numdecks))
  return value

def make_n_decks(n):
  deck1 = [4, 4, 4, 4, 4, 4, 4, 4, 4, 16]
  return list(map(lambda val: val * n, deck1))

# actions tracks all actions that resulted in a given game state
# "Ph" = player hit
# "Ps" = player stay
# "Pd" = player double-down : only can be in the first action, 
#                             and is the last action of the player
# "Dh" = dealer hit
# "Ds" = dealer stay : ends the hand
#
# game states that are reached by the same action histories are considered
# the same for metric purposes, since these are the actions we can affect,
# not the random card draws
actions = ""

mode = 1

if __name__ == '__main__':
  cutoffScore = -1.5
  aggression = 0.3

  # Interactive Demo ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  if(mode == 1):
    print("Set Budget:")
    budget = float(input())
    print("Set Max Bet Amount:")
    maxBet = float(input())
    print("Set Min Bet Amount:")
    minBet = float(input())
    print("Set Number of Decks in Play:")
    numdecks = int(input())

    game = Game(d_stay = 17, deck = make_n_decks(numdecks), budget = budget)

    while(True):
      deck_score = evaluate_deck(game.deck, numdecks)
      if deck_score <= cutoffScore:
        print("\nTrue Count is {}. Reccomend you stop playing".format(deck_score))
      else:
        print("\nTrue Count is {}. Reccomend you keep playing".format(deck_score))
      print("Continue Playing? ([y]/n)")
      cont = input()
      if cont != 'y' and cont != 'Y' and cont != '':
        break;
      
      reccbet = max(min(minBet, game.budget + game.winnings), min(maxBet, minBet + ((deck_score - cutoffScore) / 2.0)))
      print("You have ${0:.2f} in funds.".format(game.budget + game.winnings))
      print("Enter bet amount (reccomend ${0:.2f})".format(reccbet))
      bet = input()
      if str(bet) == '':
        bet = reccbet
      else:
        bet = float(bet)

      play(game, bet = bet, reccs = True, auto = False)

      if sum(game.deck) < 52.0 * numdecks / 4.0:
        print("Shuffling Decks...")
        game.deck = make_n_decks(numdecks)

    print("\nALL GAMES PLAYED!\nEnding Funds: ${0:.2f}".format(game.budget + game.winnings))


  # simulation demo ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  if mode == 2:
    numGames = 5
    numHands = 15
    maxBet = 3.0
    minBet = 1.0
    numdecks = 4

    csvfile = open("results.csv", "w", newline='')
    csvwriter = csv.writer(csvfile, delimiter=',', dialect='excel', quotechar='|', quoting=csv.QUOTE_MINIMAL)
    csvwriter.writerow(['aggression', 'winnings'])

    for j in range(0,numGames):
      game = Game(d_stay = 17, deck = make_n_decks(numdecks), budget = 30.00)
      for i in range(0, numHands):
        deck_score = evaluate_deck(game.deck, numdecks)
        if deck_score <= cutoffScore:
          print("Walking away")
          break
        bet = max(min(minBet, game.budget + game.winnings), min(maxBet, minBet + ((deck_score - cutoffScore) / 2.0)))
        if(game.budget + game.winnings - bet < 0):
          print("Out of cash")
          break
        play(game, bet = bet, reccs = True, auto = True)
        if sum(game.deck) < 52.0 * numdecks / 4.0:
          print("Shuffling...")
          game.deck = make_n_decks(numdecks)

      csvwriter.writerow([aggression, game.winnings])
      print("\nALL GAMES PLAYED!\nEnding Funds: ${0:.2f}".format(game.budget + game.winnings))
