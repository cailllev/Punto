from typing import Union

import gym
from stable_baselines3.common.policies import ActorCriticPolicy
from stable_baselines3 import A2C, PPO
from punto import Game, Card
from random import choice

players = ["StockMind", "DeepFish", "LeelaPunto0", "AlphaMinus1"]


class PuntoEnv(gym.Env):
    def __init__(self):
        self.game = Game(players)
        self._check_valid = False  # TODO implement correctly with ai

        # TODO: maybe limit action_space dynamically
        # action_space = where to place the card = the board
        self.action_space = gym.spaces.MultiDiscrete([self.game.board.max_x, self.game.board.max_y])

        # TODO: check if it works
        # [values * players] * fields -> combinations / information
        # observation_space = what is visible = the whole board + own top card
        combinations_per_field = len(self.game.players) * (Card.max_val + 1)
        fields = self.game.board.max_x * self.game.board.max_y
        board_encoded = [combinations_per_field] * fields
        board_encoded.append(Card.max_val)  # add own top card to obs space
        self.observation_space = gym.spaces.MultiDiscrete(board_encoded)

    def get_check_valid(self) -> bool:
        return self._check_valid

    def set_check_valid(self, val: bool) -> None:
        self._check_valid = val

    def reset(self) -> int:
        return self.game.reset()

    def step(self, action: [int, int]) -> (int, int, bool, dict):
        """
        takes an action and places the topmost card of the current player on the board
        actively takes the card out of their deck, use peek_top_card before calling step()
        :param action: x, y (pos of the card)
        :return: obs, reward, done, info
        """
        player = self.game.players[0]
        card = player.get_next_card()
        x, y = action

        if self._check_valid:
            if action in self.game.board.get_valid_plays(card):
                self.game.board.play_card(card, x, y, False)
                done = self.game.board.check_winner(player, x, y) or self.game.is_done()
                reward = 1  # valid play TODO: better reward on good play, or use this for learning the rules?
            else:
                done = False
                reward = -1  # invalid play
        else:
            self.game.board.play_card(card, x, y, False)
            done = self.game.board.check_winner(player, x, y) or self.game.is_done()
            reward = 0

        return self.game.board.get_observation(), reward, done, {}

    def render(self, mode="human"):
        return str(self.game)


def main():
    env = PuntoEnv()
    a2c = A2C(ActorCriticPolicy, env, n_steps=64, verbose=0)
    ppo = PPO(ActorCriticPolicy, env, n_steps=64, verbose=0)

    def random_sim():
        _ = env.reset()
        done = False

        while not done:
            card = env.game.players[0].peek_next_card()

            actions = env.game.board.get_valid_plays(card)
            if not actions:
                print(f"[*] {env.game.players[0]} has no moves left.")
                env.game.players.pop(0)  # kick them from the current round
                continue
            action = choice(actions)

            env.step(action)
            done = env.game.board.check_winner(env.game.players[0], *action) or env.game.is_done()
            print(env.game)
            env.game.next_player()

        print("[*] Done.")

    def agent_sim(agent: Union[A2C, PPO]):
        _ = env.reset()
        env.set_check_valid(True)
        done = False
        while not done:
            board_obs = env.game.board.get_observation()
            card = env.game.players[0].peek_next_card()
            obs = board_obs.append(card)

            # actions = env.game.board.get_valid_plays(card)
            action, _ = agent.predict(obs)  # , mask=actions)
            obs, _, done, _ = env.step(action)

    random_sim()
    exit()
    for ai in [a2c, ppo]:
        agent_sim(ai)


if __name__ == "__main__":
    main()
