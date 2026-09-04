import tkinter as tk

from ratvision.domain.models import ThemeMode
from ratvision.ui.theme import ThemeManager
from ratvision.ui.tour import TourStep, TutorialTour
from ratvision.domain.models import ThemeMode
from ratvision.ui.theme import ThemeManager


def test_tutorial_tour_moves_forward_backward_and_finishes():
    root = tk.Tk(); root.geometry("600x400")
    target = tk.Button(root, text="Target")
    target.pack(padx=40, pady=40)
    root.update()
    theme = ThemeManager().tokens(ThemeMode.NIGHT)
    steps = [
        TourStep(lambda: target, "STEP ONE", "First explanation"),
        TourStep(lambda: target, "STEP TWO", "Second explanation"),
    ]
    tour = TutorialTour(root, theme, steps)

    tour.start()
    assert tour.active is True
    if tour.dim is not None:
        assert float(tour.dim.attributes("-alpha")) < 0.95
    assert tour.index == 0
    assert "01 / 02" in tour.counter_label.cget("text")
    tour.next()
    assert tour.index == 1
    tour.previous()
    assert tour.index == 0
    tour.finish()
    assert tour.active is False
    assert tour.card is None
    root.destroy()


def test_tutorial_tour_has_dedicated_close_button():
    root = tk.Tk(); root.geometry("600x400+40+40")
    theme = ThemeManager().tokens(ThemeMode.NIGHT)
    target = tk.Button(root, text="Target"); target.pack(pady=30)
    root.update()
    tour = TutorialTour(root, theme, [TourStep(lambda: target, "ONE", "Help")])
    tour.start()
    assert tour.close_button is not None
    tour.close_button.invoke()
    assert tour.active is False
    root.destroy()


def test_tutorial_card_can_move_independently_from_highlight():
    from types import SimpleNamespace
    root = tk.Tk(); root.geometry("600x400+40+40")
    theme = ThemeManager().tokens(ThemeMode.NIGHT)
    target = tk.Button(root, text="Target"); target.pack(pady=30)
    root.update()
    tour = TutorialTour(root, theme, [TourStep(lambda: target, "ONE", "Help")])
    tour.start(); root.update()
    before_card = (tour.card.winfo_x(), tour.card.winfo_y())
    before_border = tuple(window.geometry() for window in tour._borders)
    tour._drag_start(SimpleNamespace(x_root=100, y_root=100))
    tour._drag_move(SimpleNamespace(x_root=145, y_root=125))
    root.update()
    assert (tour.card.winfo_x(), tour.card.winfo_y()) == (before_card[0] + 45, before_card[1] + 25)
    assert tuple(window.geometry() for window in tour._borders) == before_border
    tour.finish(); root.destroy()


def test_tutorial_overlay_tracks_main_window_movement():
    root = tk.Tk(); root.geometry("600x400+40+40")
    theme = ThemeManager().tokens(ThemeMode.NIGHT)
    target = tk.Button(root, text="Target"); target.pack(pady=30)
    root.update()
    tour = TutorialTour(root, theme, [TourStep(lambda: target, "ONE", "Help")])
    tour.start(); root.update()
    dim_before = (tour.dim.winfo_x(), tour.dim.winfo_y()) if tour.dim is not None else None
    border_before = (tour._borders[0].winfo_x(), tour._borders[0].winfo_y())
    card_before = (tour.card.winfo_x(), tour.card.winfo_y())
    root.geometry("600x400+120+100")
    root.update()
    root.after(40, lambda: None); root.update()
    if dim_before is not None:
        assert (tour.dim.winfo_x(), tour.dim.winfo_y()) != dim_before
    assert (tour._borders[0].winfo_x(), tour._borders[0].winfo_y()) != border_before
    assert (tour.card.winfo_x(), tour.card.winfo_y()) != card_before
    tour.finish(); root.destroy()


def test_tutorial_overlay_has_its_own_close_button():
    root = tk.Tk(); root.geometry("600x400+40+40")
    theme = ThemeManager().tokens(ThemeMode.NIGHT)
    target = tk.Button(root, text="Target"); target.pack(pady=30)
    root.update()
    tour = TutorialTour(root, theme, [TourStep(lambda: target, "ONE", "Help")])
    tour.start(); root.update()
    assert tour.overlay_close_button is not None
    tour.overlay_close_button.invoke()
    assert tour.active is False
    root.destroy()


def test_clicking_dim_background_finishes_tour():
    from types import SimpleNamespace
    root = tk.Tk(); root.geometry("600x400+40+40")
    theme = ThemeManager().tokens(ThemeMode.NIGHT)
    target = tk.Button(root, text="Target"); target.pack(pady=30)
    root.update()
    tour = TutorialTour(root, theme, [TourStep(lambda: target, "ONE", "Help")])
    tour.start(); root.update()
    tour._on_dim_click(SimpleNamespace())
    assert tour.active is False
    root.destroy()


def test_tutorial_raise_order_keeps_card_above_dim_and_highlight():
    class Layer:
        def __init__(self, name, calls):
            self.name = name
            self.calls = calls
        def lift(self, above=None):
            self.calls.append((self.name, None if above is None else above.name))

    calls = []
    root = tk.Tk(); root.withdraw()
    theme = ThemeManager().tokens(ThemeMode.NIGHT)
    tour = TutorialTour(root, theme, [])
    tour.active = True
    tour.dim = Layer("dim", calls)
    tour._borders = [Layer(f"border{i}", calls) for i in range(4)]
    tour.card = Layer("card", calls)
    tour.overlay_close = Layer("overlay_close", calls)

    tour._raise_overlay_layers()

    assert calls[0] == ("dim", None)
    assert calls[-2] == ("card", "border3")
    assert calls[-1] == ("overlay_close", "card")
    root.destroy()


def test_tutorial_windows_are_positioned_before_first_native_show():
    root = tk.Tk(); root.geometry("600x400+140+110")
    theme = ThemeManager().tokens(ThemeMode.NIGHT)
    target = tk.Button(root, text="Target"); target.pack(pady=30)
    root.update()
    tour = TutorialTour(root, theme, [TourStep(lambda: target, "ONE", "Help")])
    observed_states = []
    original_reposition = tour._reposition

    def observed_reposition():
        if tour.card is not None:
            observed_states.append(tour.card.state())
        original_reposition()

    tour._reposition = observed_reposition
    tour.start(); root.update()

    assert observed_states and observed_states[0] == "withdrawn"
    if tour.dim is not None:
        assert (tour.dim.winfo_x(), tour.dim.winfo_y()) == (root.winfo_rootx(), root.winfo_rooty())
    tour.finish(); root.destroy()
