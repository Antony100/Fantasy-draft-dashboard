import json
import os

from flask import Flask, request, render_template
from flask.views import View
from .dirs_creator import directories
from .draft import draft

app = Flask(__name__)
app.debug = True

class DashView(View):

    def __init__(self, league_id, list_template='home.html'):
        self.list_template = list_template
        self.league_id = league_id
        self.league_dir = self.create_league_dir(self.league_id)
        self.graph_dirs = self.create_graph_dirs(self.league_id)
        self.league_stats = draft.LeagueStats(self.league_id)
        self.stat_graphs = self.create_stat_graphs(self.league_id)

        super(DashView, self).__init__()

    methods = ['GET']

    def create_league_dir(self, league_id):
        return directories.create_league_dir(league_id)

    def create_graph_dirs(self, league_id):
        return directories.create_graph_dirs(league_id)

    def create_stat_graphs(self, league_id):
        return self.league_stats.generate_stat_graphs()

    def add_dir_prefix(self, lst, folder, league_id):
        return [f'static/images/{league_id}/{folder}/' + i for i in lst]

    def render_template(self, context):
        return render_template(self.list_template, **context)

    def dispatch_request(self):
        context = {
            'average_score': self.league_stats.get_average_score(),
            'lowest_score': self.league_stats.get_lowest_score(),
            'highest_score': self.league_stats.get_highest_score(),
            'league_name': self.league_stats.get_league_name(),
            'average_winning_score':
                self.league_stats.get_average_winning_score(),
            'stat_graphs': self.add_dir_prefix(
                os.listdir(
                    f"static/images/{self.league_id}/stats"
                ),
                'stats',
                self.league_id
                ),
            'h2h_scores': self.league_stats.get_head_to_head_results()
                   }
        if request.method == 'GET':
            return self.render_template(context)


def read_json(file_path):
    with open(file_path, "r") as f:
        return json.load(f)

def get_league_id(config_file, league_number):
    read_config = (read_json(config_file))
    return read_config['league_ids'][f'LEAGUE{league_number}_ID']

LEAGUE1_ID = get_league_id(("config.json"), "1")

LEAGUE2_ID = get_league_id(("config.json"), "2")
app.add_url_rule(
    f'/{LEAGUE1_ID}', view_func=DashView.as_view('league_1', LEAGUE1_ID)
)

app.add_url_rule(
    f'/{LEAGUE2_ID}', view_func=DashView.as_view('league_2', LEAGUE2_ID)
)
