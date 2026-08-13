"""Headless smoke test for the visualizer - forces the Agg backend so this
never tries to pop a window during an automated test run.
"""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from cube.scramble import random_scramble
from cube.state import Cube
from cube.viz.render import draw_net, refresh_net


def test_draw_net_runs_for_solved_and_scrambled(solvable_n):
    cube = Cube(solvable_n)
    fig, ax, images = draw_net(cube, title="solved")
    assert set(images) == set(cube.colors)
    plt.close(fig)

    cube.apply_algorithm(random_scramble(solvable_n, length=20))
    fig2, ax2, images2 = draw_net(cube, title="scrambled")
    plt.close(fig2)


def test_refresh_net_updates_image_data(solvable_n):
    cube = Cube(solvable_n)
    fig, ax, images = draw_net(cube)
    cube.apply_algorithm(random_scramble(solvable_n, length=10))
    refresh_net(cube, images)
    for face, image in images.items():
        assert (image.get_array() == cube.colors[face]).all()
    plt.close(fig)
