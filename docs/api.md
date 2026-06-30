# API reference

Auto-generated from the in-code docstrings.


## Top-level names

These are re-exported from `pystoch` for convenience and can be imported
directly, e.g. `from pystoch import PystochParam, calculate_maps, gwdetectors`:

`PystochParam`, `FramesetParam`, `FramesetIntermediates`, `PystochResults`,
`calculate_maps`, `calculate_maps_wrapper`, `calculate_fisher_diag`,
`load_frame_data`, `seed_matrices`, `make_notch_array`, `spectral_index`,
`complex_getlm`, `complex_map2alm`, `part_alm`, `fisher_zeros`,
`gwdetectors`, `gmst_calculate`, `combined_antenna_response_t_delay`,
`arrival_time`, `ehat`, `display_time`.

They are documented in full under their defining modules below.

## Detectors and antenna response

```{eval-rst}
.. automodule:: pystoch.detectors
   :members:
```

## Map-making functions

```{eval-rst}
.. automodule:: pystoch.pystoch_functions
   :members:
```

## Parameter classes and mapping

```{eval-rst}
.. automodule:: pystoch.pystoch_class_and_mapping
   :members:
```

## Command-line entry points

```{eval-rst}
.. automodule:: pystoch.cli.read_frames
   :members:

.. automodule:: pystoch.cli.convert_frames
   :members:

.. automodule:: pystoch.cli.make_maps
   :members:
```
