from punto import Board, Card, Game
from typing import List, Tuple

# TODO: refine
H_WIN = 1000
H_IN_ROW = 10

H_OVERLAY_OPPONENT = 3
H_OVERLAY_OWN = -1

H_TOTAL_SUM = 2
H_OWN_SUM = 1
H_CROSS_ROW_SUM = 1
H_OPPONENT_SUM = 2

H_OUT_OF_SOFT_BOUNDS = -1
H_INVALID_PLAY = -1000

dirs = [
    (+1, 0),   # top to bottom
    (+1, +1),  # top left to bottom right
    (0, +1),   # left to right
    (+1, -1),  # top right to bottom left
]


def get_lines_from_pos(b: Board, x: int, y: int) -> List[List[Tuple[Tuple[int, int], Card]]]:
    lines = []
    for dy, dx in dirs:

        # for each line of 4 in given direction, i.e.:
        #  x x x x . . .; . x x x x . .; . . x x x x .; . . . x x x x
        # -3-2-1 0         -2-1 0 1         -1 0 1 2          0 1 2 3
        for s in range(-3, 1):
            cards_pos = [(x + (s + i) * dx, y + (s + i) * dy) for i in range(4)]

            if all(b.ob_x_min <= xi <= b.ob_x_max and b.ob_y_min <= yi <= b.ob_y_max for xi, yi in cards_pos):
                lines.append([((xi, yi), b.get_card(xi, yi)) for xi, yi in cards_pos])

    return lines


def get_best_spots(board: Board, card: Card) -> List[Tuple[Tuple[int, int], int]]:
    """
    finds possible winning spots (see below) / or just good spots to place the card
    . x . . .
    . . x . .
    . . . X .
    . . . . x
    :param card: the card to find lines for
    :param board: the board to find lines on
    :return: all line segments
    """
    x_min = board.ib_x_min
    y_min = board.ib_y_min
    x_max = board.ib_x_max
    y_max = board.ib_y_max

    player = card.player

    # init heuristic board with heatmap (the further away from dynamic middle, the worse) and invalid plays
    h_spots = [[(
        0, 0                                            # normal init (0 cards in row, 0 score)
        if y_min <= y <= y_max and x_min <= x <= x_max  # if valid
        else H_INVALID_PLAY                             # else apply invalid play
    ) for x in range(board.max_x)] for y in range(board.max_x)]

    # iterate playable board from top left to bottom right
    for y in range(y_min, y_max + 1):
        for x in range(x_min, x_max + 1):

            # mark invalid plays and continue
            if not board.is_valid_play(card, x, y):
                h_spots[y][x] = 0, H_INVALID_PLAY
                continue

            # temporary change of board to calc heuristics
            original_card = board.get_card(x, y)
            board.set_card(card, x, y)

            # test for overlay bonus, the higher the other card, the better
            if original_card.player is not player:
                overlay_bonus = original_card.value * H_OVERLAY_OPPONENT
            else:
                overlay_bonus = original_card.value * H_OVERLAY_OWN

            lines = get_lines_from_pos(board, x, y)
            for line in lines:

                # heuristics of spot when placing card in current row
                cards_in_row = sum(1 for _, c in line if c.player is player)            # count of own cards in line
                own_sum = sum(c.value for _, c in line if c.player is player)           # sum of own cards in line
                opponent_sum = sum(c.value for _, c in line if c.player is not player)  # sum of other cards in line
                score = H_OWN_SUM * own_sum + H_OPPONENT_SUM * opponent_sum

                # add out of soft bounds penalty
                if not all(x_min <= xi <= x_max or y_min <= yi <= y_max for (xi, yi), _ in line):
                    score += H_OUT_OF_SOFT_BOUNDS

                # find crossing rows (and add score to them)
                cards_existing, score_existing = h_spots[y][x]
                in_row = cards_in_row if cards_in_row >= cards_existing else cards_existing
                if in_row == 4:
                    added_score = H_WIN
                else:
                    added_score = score + H_CROSS_ROW_SUM * score_existing + overlay_bonus

                # save score for current line in x, y
                h_spots[y][x] = in_row, added_score

            # revert board
            board.set_card(original_card, x, y)

    # flatten list and add index to find positions of spots easily
    flat_h_spots = [((x, y), data) for y, row in enumerate(h_spots) for x, data in enumerate(row)]

    # convert data (in_row, score) to complete score
    scores = [((x, y), H_IN_ROW * in_row ** 2 + H_TOTAL_SUM * score) for (x, y), (in_row, score) in flat_h_spots]

    # sort spots, from best score to worst score
    sorted_h_spots = sorted(scores, key=lambda elem: (elem[1]), reverse=True)
    return sorted_h_spots


# TODO: implement shallow pruning, correct and sanitycheck algo
# minimax devolves to 1 v all in multiplayer settings
#   -> use maximax (maximize for all players individually)
def maximax(game: Game, card: Card) -> Tuple[int, int]:
    """
    :param card: the card to find best play for
    :param game: the current state of game to find best play for
    :return: best current play
    """

    nr_of_plays = 8
    max_scores = [0] * nr_of_plays
    top_n_plays_per_round = [3, 3, 1]  # last 1 for lookahead strategy
    score_coef_per_round = [0.8, 0.6, 0.5]
    rounds_forward = len(top_n_plays_per_round)

    def algo(play_nr: int, current_round: int, added_score: float):

        # when in leaf check accumulated score and add to results if new max
        if current_round == rounds_forward:
            max_scores[play_nr] = added_score if added_score > max_scores[play_nr] else max_scores[play_nr]
            return

        # get best play per other players, and finally for own player
        for player in game.players[1:] + [me]:
            avg_card = player.get_avg_draw()
            top_n_plays = top_n_plays_per_round[current_round]
            top_plays = get_best_spots(board, avg_card)[:top_n_plays]

            for (x, y), score in top_plays:
                # only change score on own player
                if player is me:
                    added_score += score_coef_per_round[current_round] * score

                # store old card, set new card and evaluate new board
                tmp_card = board.get_card(x, y)
                board.set_card(avg_card, x, y)
                algo(play_nr, current_round + 1, added_score)

                # revert play
                board.set_card(tmp_card, x, y)

    # helper vars
    me = game.players[0]
    board = game.board

    # get top 8 valid plays
    original_plays = get_best_spots(board, card)[:nr_of_plays]

    # calculate score of each play
    for i, ((x0, y0), score0) in enumerate(original_plays):
        old_card = board.get_card(x0, y0)
        board.set_card(card, x0, y0)
        algo(i, 0, score0)
        board.set_card(old_card, x0, y0)

    # find index of highest score
    idx = max_scores.index(max(max_scores))

    # return x,y of highest score
    return original_plays[idx][0]
