import os

CURRENT_DIR = os.getcwd()
RESULTS_DIR_PATH = os.path.join(CURRENT_DIR, f'static/images/')


def create_league_dir(league_id):
    try:
        os.mkdir(RESULTS_DIR_PATH + f"{league_id}")
    except FileExistsError:
        print(f"{league_id} folder already exists")


def create_graph_dirs(league_id):
    league_dir = RESULTS_DIR_PATH + f"{league_id}/"
    graph_dirs = ["head2head", "stats"]

    for _dir in graph_dirs:
        try:
            os.mkdir(league_dir + f"{_dir}")
        except FileExistsError:
            print(f"{_dir} folder already exists")
