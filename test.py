from heuristic import get_lines_from_pos
from punto import Game, Player, Card
from random import choice

players = ["StockMind", "DeepFish", "LeelaPunto0", "AlphaMinus1"]


def test_init():
    game = Game(players)
    board = game.board

    print(game.players[0])

    for y, row in enumerate(board._spots):
        for x, card in enumerate(row):
            if y == board.y_mid and x == board.x_mid:
                assert card.player is game.players[-1]
                assert card.value != 0
            else:
                assert card.player.get_player_id() == 0
                assert card.value == 0
    assert len(board.played_cards) == 1


def test_play_first_card():
    game = Game(players)
    p = Player("P", 1)
    card = Card(p, 1)

    game.board.play_card(card, 5, 5, check_if_valid=False)
    assert game.board.get_card(5, 5) == card
    return True


def test_overlay():
    game = Game(players)
    p1 = Player("P1", 1)
    p2 = Player("P2", 1)
    card1 = Card(p1, 1)
    card2 = Card(p1, 2)
    card3 = Card(p2, 3)
    x = y = 5

    game.board.play_card(card1, x, y, False)
    assert game.board.get_card(x, y) == card1

    game.board.play_card(card3, x, y)
    assert game.board.get_card(x, y) == card3

    assert not game.board.play_card(card2, x, y)  # illegal move


def test_check_winner():
    pass  # TODO


def test_random_round():
    game = Game(players[:2])  # ensure all cards can be played -> only 2 players
    played_cards = 1  # first card is already played

    while not game.is_done():
        card = game.players[0].get_next_card()
        actions = game.board.get_valid_plays(card)
        x, y = choice(actions)

        game.board.play_card(card, x, y, check_if_valid=False)
        game.next_player()
        played_cards += 1

    print(game)

    # check if all cards could be played
    assert played_cards == len(game.board.played_cards)
    # check if all 9's are visible (cannot overlay 9)
    assert len([c for c in game.board.played_cards if c.value == Card.max_val]) == len(game.players) * 2


# TODO: correct test
def test_get_lines():
    def extract_cards(lines_all_data):
        return [[card for _, card in line] for line in lines_all_data]

    game = Game([players[0]])
    p1 = Player("P1", 1)
    card1 = Card(p1, 1)
    card2 = Card(p1, 2)
    card3 = Card(p1, 3)
    card4 = Card(p1, 4)
    card5 = Card(p1, 9)

    empty = game.board.null_card
    first_card = game.board.get_card(5, 5)

    # 5,5; 6,5; 7,5
    game.board.play_card(card1, 6, 5)
    game.board.play_card(card2, 7, 5)
    line1 = [first_card, card1, card2, empty]

    # so far, state of board:
    #    3 4 5 6 7
    # 5  . . x x x   -> first_card, 1, 2

    lines = extract_cards(get_lines_from_pos(game.board, 5, 5))
    assert line1 in lines

    # 5,5; 6,4; 7;3 (and 6,4; 6,5 as a side effect)
    game.board.play_card(card3, 6, 4)
    game.board.play_card(card4, 7, 3)
    line2 = [card4, card3, first_card, empty]

    # new state of board
    #    3 4 5 6 7
    # 3  . . . . x
    # 4  . . . x .
    # 5  . . x x x

    lines = extract_cards(get_lines_from_pos(game.board, 5, 5))
    assert line1 in lines
    assert line2 in lines

    # 4,4; 5,5
    game.board.play_card(card5, 4, 4)
    line3 = [card5, first_card, empty, empty]

    # new state of board
    #    3 4 5 6 7
    # 3  . . . . x
    # 4  . x . x .
    # 5  . . x x x

    lines = extract_cards(get_lines_from_pos(game.board, 5, 5))
    assert line1 in lines
    assert line2 in lines
    assert line3 in lines

    line4 = [card5, empty, card3, empty]
    line5 = [card5, first_card, empty, empty]
    lines = extract_cards(get_lines_from_pos(game.board, 4, 4))
    assert line4 in lines
    assert line5 in lines


if __name__ == "__main__":
    for f in locals().copy():
        if f.startswith("test_"):
            eval(f)()  # call function
