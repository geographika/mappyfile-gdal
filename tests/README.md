Mapfiles generated from the sample JSON in `tests/json` are compared against the
expected copies in `tests/mapfiles`. A new sample only needs its JSON adding; the
expected Mapfile is written on the first run for review. After an intentional change
to the output, update them all with:

```console
pytest tests/test_expected.py --update-expected
```