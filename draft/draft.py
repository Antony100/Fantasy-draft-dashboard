from itertools import chain, combinations
import os
import requests


from matplotlib import pyplot as plt
import numpy as np

CURRENT_DIR = os.getcwd()
RESULTS_DIR_PATH = os.path.join(CURRENT_DIR, 'results')
BASE_URL = "https://draft.premierleague.com/api/"


class DraftData():
    """
    Retrieves the draft data from the draft league API and filters data
    to return player names and their gameweek points.
    """

    def __init__(self, league_id):
        self.league_id = league_id

    @property
    def player_ids(self):
        try:
            return self._player_ids
        except AttributeError:
            self._player_ids = self.get_player_ids()
            return self._player_ids

    def get_api_data(self, BASE_URL=BASE_URL, url=''):
        """Makes a call to the API and returns the result as json."""
        response = requests.get(BASE_URL + url)

        response.raise_for_status()

        if response.status_code == 200:
            return response.json()

    def get_league_details(self):
        """ Retrieves and returns the the league's details. """
        return self.get_api_data(
            url=f"league/{self.league_id}/details"
        )

    def get_player_ids(self, player_id='entry_id'):
        """
        retrieves league details and returns a dictionary of all players
        and their league entry IDs. Change id arg to "id" for player IDs
        used for match events.
        """
        league_details = self.get_league_details()
        result = dict()

        for player in league_details['league_entries']:
            result[player['player_first_name']] = player[player_id]

        return result

    def create_id_dict(self):
        """
        creates a dict that has player IDs as keys with an empty list
        as the value.
        """
        return {ids: [] for ids
                in self.get_player_ids(player_id='id').values()
                }

    def get_league_name(self):
        """Retrieves the league name."""
        return self.get_league_details()['league']['name']

    def get_player_history(self, player_name):
        """ Retrieves and returns the player's history. """
        return self.get_api_data(
            url=f"entry/{self.player_ids[player_name]}/history"
        )

    def get_points_per_gameweek(self, src):
        """
        Returns a list of points from every gameweek filtered from the
        player's history.
        """
        return [points['points'] for points in src['history']]

    def get_players_points(self, *players, format_type="dict"):
        """
        returns a dictionary of players and their gameweek score points.
        specify format_type (by default a dictionary) of either
        a list or dictionary to change the gameweek points as either a
        dictionary of gameweek number and points or a list of just the
        points.
        """
        result = dict()
        for player_name in players:
            data = self.get_player_history(player_name)
            points = self.get_points_per_gameweek(data)
            if format_type == "dict":
                result[player_name] = dict(enumerate(points, start=1))
            elif format_type == "list":
                result[player_name] = list(points)
        return result


class LeagueStats(DraftData):
    """
    Returns the highest, lowest and average gameweek score of each
    player in barcharts and also as a boxplot.
    """

    def __init__(self, league_id):
        super().__init__(league_id)
        self.all_player_scores = self.get_players_points(
            *self.player_ids, format_type='list'
        )

    def calc_average(self, lst):
        try:
            return sum(lst) // len(lst)
        except ZeroDivisionError as e:
            print(e, "No values to divide")

    def get_gameweek_statistic(self, func):
        """
        Returns a gameweek statistic from the player scores based on the
        function given to the func argument.
        """
        return {
            player: func(self.all_player_scores[player])
            for player in self.all_player_scores
        }

    def barchart(self, scores, title):
        """
        Plots a barchart of single bars that are annotated with values.
        """

        labels = list(scores.keys())

        plt.style.use('bmh')

        x = np.arange(len(labels))  # the label locations
        width = 0.4  # the width of the bars

        fig, ax = plt.subplots()
        rects1 = ax.bar(x, scores.values(), width)

        ax.set_ylabel('Points')
        ax.set_xlabel('players')
        ax.set_title(title)
        ax.set_xticks(x)
        ax.set_xticklabels(labels)

        def autolabel(rects):
            """
            Attach a text label above each bar in *rects*, displaying
            its height.
            """
            for rect in rects:
                height = rect.get_height()
                ax.annotate('{}'.format(height),
                            xy=(rect.get_x() + rect.get_width() / 2, height),
                            xytext=(0, 3),  # 3 points vertical offset
                            textcoords="offset points",
                            ha='center', va='bottom')

        autolabel(rects1)

        fig.tight_layout()
        fig.set_size_inches(18.5, 10.5, forward=True)

        plt.savefig(
            f'{os.getcwd()}/static/images/{self.league_id}/stats/{title}.jpg',
            orientation='landscape'
        )
        plt.close()

    def plot_highest_scores(self):
        """
        Saves a barchart of all the players and their highest gameweek
        score.
        """
        return self.barchart(
            self.get_gameweek_statistic(max),
            'Highest Gameweek Scores Per Player'
        )

    def plot_lowest_scores(self):
        """
        Saves a barchart of all the players and their lowest gameweek
        score.
        """
        return self.barchart(
            self.get_gameweek_statistic(min),
            'Lowest Gameweek Scores Per Player'
        )

    def plot_average_scores(self):
        """
        Saves a barchart of all the players and their average gameweek
        score.
        """
        return self.barchart(
            self.get_gameweek_statistic(self.calc_average),
            'Average Gameweek Scores Per Player'
        )

    def merge_score_lists(self, scores):
        """
        combines multiple lists of scores into a single list.
        """
        return list(chain.from_iterable(scores))

    def merge_all_scores(self):
        """
        creates a single list of all players' gameweek scores.
        """
        return self.merge_score_lists(self.all_player_scores.values())

    def get_average_score(self):
        """
        returns the average of all gameweek scores.
        """
        return self.calc_average(self.merge_all_scores())

    def get_lowest_score(self):
        return min(self.merge_all_scores())

    def get_highest_score(self):
        return max(self.merge_all_scores())

    def get_winning_player_scores(self):
        league_details = self.get_league_details()
        player_winning_scores = self.create_id_dict()

        for event in league_details['matches']:
            if (event['league_entry_1_points'] >
                    event['league_entry_2_points']):
                player_winning_scores[event['league_entry_1']].append(
                        event['league_entry_1_points']
                    )
            elif (event['league_entry_2_points'] >
                  event['league_entry_1_points']
                  ):
                player_winning_scores[event['league_entry_2']].append(
                    event['league_entry_2_points']
                )
        return player_winning_scores

    def merge_all_winning_scores(self):
        return self.merge_score_lists(
            self.get_winning_player_scores().values()
        )

    def get_average_winning_score(self):
        return self.calc_average(self.merge_all_winning_scores())

    def headtohead_score(self, score_dict, player1, player2):
        """
        Compares the scores of each gameweek if players went
        head to head and returns a dict of how many wins each and draws.
        """
        p1_win = 0
        p2_win = 0
        draw = 0
        for score in list(
            zip(
                score_dict[player1],
                score_dict[player2]
            )
        ):
            if score[0] > score[1]:
                p1_win += 1
            elif score[1] > score[0]:
                p2_win += 1
            elif score[0] == score[1]:
                draw += 1
        return {'player1': player1, 'player2': player2, 'p1_score': p1_win,
                'p2_score': p2_win, "draw": draw
                }

    def get_head_to_head_results(self):
        """
        Returns a dict of all combinations of players going head to head
        """

        player_combos = tuple(combinations(self.player_ids, 2))

        res = []

        for name1, name2 in player_combos:
            res.append(
                self.headtohead_score(self.all_player_scores, name1, name2)
                )

        return res

    def generate_stat_graphs(self):

        return (self.plot_average_scores(),
                self.plot_highest_scores(),
                self.plot_lowest_scores(),
                )
