"""Self-contained experiments for the DISP-S1 evaluation framework.

Each subpackage is one experiment. The ``run.py`` module exposes a
``main()`` entry point that writes artifacts under ``results/`` and a
``manifest.json`` describing inputs, software versions, random seeds,
and output checksums.

Experiments are importable so they can be invoked as modules
(``python -m experiments.E01_central_valley_disp_s1_vs_gnss.run``) or
unit-tested.
"""
