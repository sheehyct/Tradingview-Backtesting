"""Smoke test so the Stop test gate has something to collect on a fresh workspace."""


def test_analysis_package_imports():
    import analysis

    assert analysis.__doc__ is not None
