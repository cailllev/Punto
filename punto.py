from console import black, white, red, blue, green, yellow, clear
from random import choice, shuffle
from typing import List, Tuple


class Player:
    def __init__(self, name: str, player_id: int):
        self._name = name
        self._player_id = player_id
        self._cards = [Card(self, i) for i in range(Card.min_val, Card.max_val + 1)]
        self._cards.extend(self._cards)  # 1, 1, 2, 2, ...
        shuffle(self._cards)

    def get_name(self) -> str:
        return self._name

    def get_next_card(self) -> "Card":
        return self._cards.pop()

    def peek_next_card(self) -> "Card":
        return self._cards[0].copy()

    """
    def get_chance_of_drawing(self, other_val: int) -> float:
        return len([c for c in self._cards if c.value > other_val]) / len(self._cards)

    def get_drawing_chances(self) -> List[float]:
        counts = [0] * (Card.max_val + 1)
        for c in self._cards:
            counts[c.value] += 1
        return [c / len(self._cards) for c in counts]
    """

    # TODO: maybe return 60% / 70% median to be more cautious with plays, or 30% / 40% median to be more risky
    def get_avg_draw(self) -> "Card":
        return self._cards[len(self._cards) // 2]

    def get_remaining_cards(self) -> ["Card"]:
        # only to be used by heuristics!
        return self._cards

    def get_player_id(self):
        return self._player_id

    def cards_count(self) -> int:
        return len(self._cards)

    def __str__(self) -> str:
        return f"{self._name}: {len(self._cards)} cards"

    def __eq__(self, other: "Player"):
        return self._player_id == other.get_player_id()


class Card:
    min_val = 1
    max_val = 9

    def __init__(self, player: Player, value: int = 0):
        self.player = player
        self.value = value

    def copy(self):
        return Card(self.player, self.value)

    def __str__(self) -> str:
        f = Board.id_to_col[self.player.get_player_id()]
        return f(str(self.value))
        # return str(self.player.player_id) + str(self.value)


class Board:
    null_player = Player("", 0)
    null_card = Card(null_player, 0)

    max_x = max_y = 11
    max_size = 6
    x_mid = (max_x - 1) // 2
    y_mid = (max_y - 1) // 2

    id_to_col = {0: black, 1: red, 2: green, 3: blue, 4: yellow}

    def __init__(self, card: Card):
        self._spots = [[self.null_card for _ in range(self.max_x)] for _ in range(self.max_y)]

        # both borders are inclusive, i.e. it's valid to play a card "on" the border
        # ensures that the playing field is not wider than 6x6
        self.ob_x_min = 0
        self.ob_y_min = 0
        self.ob_x_max = self.max_x - 1
        self.ob_y_max = self.max_y - 1

        # quick check if cards could be in playable area (could have a neighbour)
        self.ib_x_min = self.x_mid - 1
        self.ib_y_min = self.y_mid - 1
        self.ib_x_max = self.x_mid + 1
        self.ib_y_max = self.y_mid + 1

        self.played_cards = [card]
        self._spots[self.y_mid][self.x_mid] = card

    def get_card(self, x: int, y: int) -> Card:
        return self._spots[y][x]

    def get_valid_plays(self, card: Card) -> List[Tuple[int, int]]:
        return [(x, y) for y in range(self.max_y) for x in range(self.max_x) if self.is_valid_play(card, x, y)]

    def is_valid_play(self, card: Card, x: int, y: int) -> bool:
        # check if new card is bigger
        if card.value <= self._spots[y][x].value:
            return False

        # check if card is in inner border (automatically in outer border too if in inner)
        if not self.ib_x_min <= x <= self.ib_x_max or not self.ib_y_min <= y <= self.ib_y_max:
            return False

        # check adjacent, at least one direct or diagonally
        x_minus = 0 if x == 0 else 1
        x_plus = 0 if x == self.max_x - 1 else 1
        y_minus = 0 if y == 0 else 1
        y_plus = 0 if y == self.max_y - 1 else 1
        adjacent_cards = [
            self._spots[j][i] for j in range(y - y_minus, y + y_plus + 1) for i in range(x - x_minus, x + x_plus + 1)
        ]
        if not any(c.value for c in adjacent_cards):
            return False

        return True

    def update_borders(self, x: int, y: int) -> None:
        # shrink outer borders (on oppisite side of played card), +1 / -1 bc of index magic
        if (v := x + 1 - self.max_size) > self.ob_x_min: self.ob_x_min = v
        if (v := y + 1 - self.max_size) > self.ob_y_min: self.ob_y_min = v
        if (v := x - 1 + self.max_size) < self.ob_x_max: self.ob_x_max = v
        if (v := y - 1 + self.max_size) < self.ob_y_max: self.ob_y_max = v

        # enlarge inner border (if card placed on border), but also check that inner is not "bigger" than outer
        if x == self.ib_x_min and self.ib_x_min > self.ob_x_min: self.ib_x_min = x - 1
        if y == self.ib_y_min and self.ib_y_min > self.ob_y_min: self.ib_y_min = y - 1
        if x == self.ib_x_max and self.ib_x_max < self.ob_x_max: self.ib_x_max = x + 1
        if y == self.ib_y_max and self.ib_y_max < self.ob_y_max: self.ib_y_max = y + 1

    def play_card(self, card: Card, x: int, y: int, check_if_valid: bool = True) -> bool:
        if check_if_valid:
            if self.is_valid_play(card, x, y):
                self.played_cards.append(card)
                self._spots[y][x] = card
                self.update_borders(x, y)
                return True
            return False
        else:
            self.played_cards.append(card)
            self._spots[y][x] = card
            self.update_borders(x, y)
            return True

    def set_card(self, card: Card, x: int, y: int) -> None:
        # only change spot, no checks, no new card in "cards played", has to be reverted, used by heuristics
        self._spots[y][x] = card

    def check_winner(self, last_player: Player, x: int, y: int) -> bool:
        x_minus = min(x, 3)
        y_minus = min(y, 3)
        x_plus = min(self.max_x - 1 - x, 3)
        y_plus = min(self.max_y - 1 - y, 3)
        rows = [  # [top to bottom, top left to bottom right, left to right, bottom left to top right]
            [self._spots[y + j][x] for j in range(-y_minus, y_plus + 1)],
            [self._spots[y + j][x + i] for j, i in zip(range(-y_minus, y_plus + 1), range(-x_minus, x_plus + 1))],
            [self._spots[y][x + i] for i in range(-x_minus, x_plus + 1)],
            [self._spots[y + j][x + i] for j, i in zip(range(y_plus, -y_minus - 1, -1), range(-x_minus, x_plus + 1))]
        ]
        for row in rows:
            streak = 0
            for c in row:
                if c.player and c.player == last_player:
                    streak += 1
                    if streak == 4:
                        return True
                else:
                    streak = 0
        return False

    def get_observation(self) -> List[int]:
        # the position of a card in the list is info enough about its location
        # the value of the card is transformed, so that player1 card6 != player2 card3
        # -> each value is unique -> let the AI figure it out
        obs = []
        for row in self._spots:
            for card in row:
                obs.append(card.player.get_player_id() * card.value)
        return obs

    def update_observation(self, obs: List[int], card: Card, x: int, y: int) -> None:
        # updates the current observation after a played card
        # 2d positions to index in flat list
        ind = self.max_y * y + x
        obs[ind] = card.player.get_player_id() * card.value

    def reset(self, first_card: Card):
        for y in range(self.max_y):
            for x in range(self.max_x):
                self._spots[y][x] = self.null_card

        # set up for next game
        self._spots[self.y_mid][self.x_mid] = first_card
        self.played_cards = [first_card]

    def __str__(self) -> str:
        s = " " * 4
        # indices above board, mark indices outside border as black
        ind = []
        for i in range(self.max_x):
            ind.append(white(str(i)) if self.ob_x_min <= i <= self.ob_x_max else black(str(i)))
        s += " ".join(ind) + "\n\n"
        for j, row in enumerate(self._spots):
            # indices next to board
            s += white(str(j)) if self.ob_y_min <= j <= self.ob_y_max else black(str(j))
            s += " " * (4 - len(str(j)))  # pad
            for card in row:
                s += str(card) + " "
            s += "\n"
        return s


class Game:

    def __init__(self, player_names: List[str]):
        if not player_names:
            raise ValueError("[!] Cannot create game for 0 players!")
        self.players = [Player(name, i + 1) for i, name in enumerate(player_names)]
        self.me = self.players[0]
        shuffle(self.players)

        # place first card
        first_card = self.players[0].get_next_card()
        self.board = Board(first_card)
        self.next_player()

    def next_player(self) -> None:
        """
        rotates the players
        """
        self.players.append(self.players.pop(0))

    def do_turn(self) -> Tuple[Player, Tuple[int, int]]:
        from heuristic import get_best_spots, maximax

        player = self.players[0]
        card = player.get_next_card()
        self.next_player()

        print(self)
        print(f"[*] Your topmost card is {card}.")

        # do not use maximax on other players
        if player is not self.me:
            if len(self.board.played_cards) < len(self.players):  # do random plays in first round
                (x, y) = choice(self.board.get_valid_plays(card))
            else:
                (x, y), _ = get_best_spots(self.board, card)[0]
            self.board.play_card(card, x, y, False)
            return player, (x, y)

        xm, ym = maximax(self, card)
        while True:
            while True:
                try:
                    print(f"[*] Maximax recommends to play {xm} {ym}")
                    pos = input("[*] Select the position to play the card: ").split(" ")
                    x = int(pos[0])
                    y = int(pos[1])
                    break
                except (ValueError, IndexError):
                    print("[!] Please enter the position like this: 1 3 (for x=1 and y=3)")
                except KeyboardInterrupt:
                    print("\n[*] Exiting...")
                    exit()

            if self.board.play_card(card, x, y):
                break
            else:
                print(f"[!] Card must be adjacent to existing cards or bigger then the card underneath.")

        return player, (x, y)

    def play_round(self) -> bool:
        while True:
            last_player, (x, y) = self.do_turn()
            if self.board.check_winner(last_player, x, y):
                print(self)
                print(f"[*] Congrats {last_player.get_name()}, you won!")
                return True
            if self.is_done():
                print(f"[*] Game ended, no winner...")
                return True

    def is_done(self) -> bool:
        return not any(p.cards_count() for p in self.players)

    def reset(self) -> int:
        self.__init__([p.get_name() for p in self.players])
        return 0

    def __str__(self) -> str:
        return clear() + str(self.board)


if __name__ == "__main__":
    game = Game(["Me", "Myself", "I"])
    game.play_round()
