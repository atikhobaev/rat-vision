from ratvision.domain.models import VisualParameters


def test_visual_parameters_normalize_to_supported_ranges():
    value = VisualParameters(-1, 2, 9, 140).normalized()
    assert value == VisualParameters(0.0, 1.0, 2.8, 100)


def test_visual_parameters_keep_supported_values():
    value = VisualParameters(0.4, 0.6, 1.2, 65).normalized()
    assert value == VisualParameters(0.4, 0.6, 1.2, 65)
