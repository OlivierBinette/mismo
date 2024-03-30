from __future__ import annotations

from pathlib import Path

import ibis
from ibis.expr import types as ir

from mismo import _util

__all__ = [
    "load_febrl1",
    "load_febrl2",
    "load_febrl3",
    "load_patents",
    "load_rldata500",
    "load_rldata10000",
]

_DATASETS_DIR = Path(__file__).parent / "_data/_datasets"


def _wrap_febrl(loader_name: str) -> tuple[ir.Table, ir.Table]:
    with _util.optional_import("recordlinkage"):
        from recordlinkage import datasets as rlds

    loader = getattr(rlds, loader_name)
    pdf, links_multi_index = loader(return_links=True)
    pdf = pdf.reset_index(drop=False)
    schema = {
        "rec_id": "str",
        "given_name": "str",
        "surname": "str",
        "street_number": "str",  # keep as string for leading 0s
        "address_1": "str",
        "address_2": "str",
        "suburb": "str",
        "postcode": "str",  # keep as string for leading 0s
        "state": "str",
        "soc_sec_id": "int32",  # 7 digits long, never null, no leading 0s
        "date_of_birth": "str",  # contains some BS dates like 19371233
    }
    t = ibis.memtable(pdf)
    t = t.cast(schema)
    t = t.rename(record_id="rec_id")
    t = t.order_by("record_id")
    t = t.cache()

    links_df = links_multi_index.to_frame(
        index=False, name=["record_id_l", "record_id_r"]
    )
    links = ibis.memtable(links_df)
    links = links.order_by(["record_id_l", "record_id_r"])
    links = links.cache()
    return (t, links)


def load_febrl1() -> tuple[ir.Table, ir.Table]:
    return _wrap_febrl("load_febrl1")


def load_febrl2() -> tuple[ir.Table, ir.Table]:
    return _wrap_febrl("load_febrl2")


def load_febrl3() -> tuple[ir.Table, ir.Table]:
    return _wrap_febrl("load_febrl3")


# Don't bother wrapping load_febrl4 because it has a different API,
# could add that later if it's needed.


def load_patents(backend: ibis.BaseBackend | None = None) -> ir.Table:
    """Load the PATSTAT dataset

    This represents a dataset of patents, and the task is to determine which
    patents came from the same inventor.

    This comes from
    [the Dedupe Patent Example](https://github.com/dedupeio/dedupe-examples/tree/master/patent_example).

    Returns
    -------
    Table
        An Ibis Table with the following schema:

        - record_id: int64
          A unique ID for each row in the table.
        - label_true: int64
          The manually labeled, true ID of the inventor.
        - name_true: str
          The manually labeled, true name of the inventor.
        - name: str
          The raw name on the patent.
        - latitude: float64
          Geocoded from the inventor's address. 0.0 indicates no address was found
        - longitude: float64
        - coauthor: str
          A list of coauthors on the patent, separated by "**"
        - class_: str
          A list of 4-character IPC technical codes, separated by "**"

    Examples
    --------
    >>> load_patents()
    ┏━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
    ┃ record_id ┃ label_true ┃ name_true            ┃ name                         ┃ latitude ┃ longitude ┃ coauthors                      ┃ classes                        ┃
    ┡━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
    │ int64     │ int64      │ string               │ string                       │ float64  │ float64   │ string                         │ string                         │
    ├───────────┼────────────┼──────────────────────┼──────────────────────────────┼──────────┼───────────┼────────────────────────────────┼────────────────────────────────┤
    │      2909 │     402600 │ AGILENT TECHNOLOGIES │ * AGILENT TECHNOLOGIES, INC. │     0.00 │  0.000000 │ KONINK PHILIPS ELECTRONICS N … │ A61N**A61B                     │
    │      3574 │     569309 │ AKZO NOBEL           │ * AKZO NOBEL N.V.            │     0.00 │  0.000000 │ TSJERK  HOEKSTRA**ANDRESS K  … │ G01N**B01L**C11D**G02F**F16L   │
    │      3575 │     569309 │ AKZO NOBEL           │ * AKZO NOBEL NV              │     0.00 │  0.000000 │ WILLIAM JOHN ERNEST  PARR**HA… │ C09K**F17D**B01F**C23F         │
    │      3779 │     656303 │ ALCATEL              │ * ALCATEL N.V.               │    52.35 │  4.916667 │ GUENTER  KOCHSMEIER**ZBIGNIEW… │ G02B**G04G**H02G**G06F         │
    │      3780 │     656303 │ ALCATEL              │ * ALCATEL N.V.               │    52.35 │  4.916667 │ ZILAN  MANFRED**JOSIANE  RAMO… │ H03G**B05D**H04L**H04B**C03B*… │
    │      3782 │     656303 │ ALCATEL              │ * ALCATEL N.V.               │     0.00 │  0.000000 │ OLIVIER  AUDOUIN**MICHEL  SOT… │ H04B**H01S**H04J               │
    │     15041 │    4333661 │ CANON EUROPA         │ * CANON EUROPA N.V           │     0.00 │  0.000000 │ LEE  RICKLER**SIMON  PARKER**… │ G06F                           │
    │     15042 │    4333661 │ CANON EUROPA         │ * CANON EUROPA N.V.          │     0.00 │  0.000000 │ QI HE  HONG**ADAM MICHAEL  BA… │ G06T**G01B                     │
    │     15043 │    4333661 │ CANON EUROPA         │ * CANON EUROPA NV            │     0.00 │  0.000000 │ NILESH  PATHAK**MASAMICHI  MA… │ H04B**G06T**G06F**H04M**H04N*… │
    │     25387 │    7650783 │ DSM                  │ * DSM N.V.                   │     0.00 │  0.000000 │ GABRIEL MARINUS  MEESTERS**RU… │ C12N**A61K**A23L**A23J**A23K*… │
    │         … │          … │ …                    │ …                            │        … │         … │ …                              │ …                              │
    └───────────┴────────────┴──────────────────────┴──────────────────────────────┴──────────┴───────────┴────────────────────────────────┴────────────────────────────────┘
    """  # noqa E501
    path = _DATASETS_DIR / "patstat/patents.csv"
    if backend is None:
        backend = ibis
    # In order to guarantee row order, could either use
    # parallel=False kwarg, but I'd rather just have them sorted
    # by record_id
    return backend.read_csv(path).order_by("record_id").cache()


def rldata_schema() -> dict:
    return {
        "record_id": "int64",
        "label_true": "int64",
        "fname_c1": "string",
        "fname_c2": "string",
        "lname_c1": "string",
        "lname_c2": "string",
        "by": "int64",
        "bm": "int64",
        "bd": "int64",
    }


def load_rldata500(backend: ibis.BaseBackend | None = None) -> ir.Table:
    """Synthetic personal information dataset with 500 rows

    This is a synthetic dataset with noisy names and dates of birth, with the task being
    to determine which rows represent the same person. 10% of the records are duplicates
    of existing ones, and the level of noise is low. The dataset can be deduplicated with 90%+
    precision and recall using simple linkage rules. It is often used as a
    sanity check for computational efficiency and disambiguation accuracy.

    This comes from the
    [RecordLinkage R package](https://cran.r-project.org/web/packages/RecordLinkage/index.html)
    and was generated using the data generation component of
    [Febrl (Freely Extensible Biomedical Record Linkage)](https://sourceforge.net/projects/febrl/).

    Returns
    -------
    Table
        An Ibis Table with the following schema:

        - record_id: int64
          A unique ID for each row in the table.
        - label_true: int64
          The manually labeled, true ID of the inventor.
        - fname_c1: string
          First component of the first name.
        - fname_c2: string
          Second component of the first name (mostly NULL values)
        - lname_c1: string
          First component of the last name.
        - lname_c2: string
          Second component of the last name (mostly NULL values).
        - by: int64
          Birth year
        - bm: int64
          Birth month
        - bd: int64
          Birth day

    Examples
    --------
    >>> load_rldata500()
    ┏━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━┳━━━━━━━┳━━━━━━━┓
    ┃ record_id ┃ label_true ┃ fname_c1 ┃ fname_c2 ┃ lname_c1 ┃ lname_c2 ┃ by    ┃ bm    ┃ bd    ┃
    ┡━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━╇━━━━━━━╇━━━━━━━┩
    │ int64     │ int64      │ string   │ string   │ string   │ string   │ int64 │ int64 │ int64 │
    ├───────────┼────────────┼──────────┼──────────┼──────────┼──────────┼───────┼───────┼───────┤
    │         0 │         34 │ CARSTEN  │ NULL     │ MEIER    │ NULL     │  1949 │     7 │    22 │
    │         1 │         51 │ GERD     │ NULL     │ BAUER    │ NULL     │  1968 │     7 │    27 │
    │         2 │        115 │ ROBERT   │ NULL     │ HARTMANN │ NULL     │  1930 │     4 │    30 │
    │         3 │        189 │ STEFAN   │ NULL     │ WOLFF    │ NULL     │  1957 │     9 │     2 │
    │         4 │         72 │ RALF     │ NULL     │ KRUEGER  │ NULL     │  1966 │     1 │    13 │
    │         5 │        142 │ JUERGEN  │ NULL     │ FRANKE   │ NULL     │  1929 │     7 │     4 │
    │         6 │        162 │ GERD     │ NULL     │ SCHAEFER │ NULL     │  1967 │     8 │     1 │
    │         7 │         48 │ UWE      │ NULL     │ MEIER    │ NULL     │  1942 │     9 │    20 │
    │         8 │        133 │ DANIEL   │ NULL     │ SCHMIDT  │ NULL     │  1978 │     3 │     4 │
    │         9 │        190 │ MICHAEL  │ NULL     │ HAHN     │ NULL     │  1971 │     2 │    27 │
    │         … │          … │ …        │ …        │ …        │ …        │     … │     … │     … │
    └───────────┴────────────┴──────────┴──────────┴──────────┴──────────┴───────┴───────┴───────┘
    """  # noqa: E501
    path = _DATASETS_DIR / "rldata/RLdata500.csv"
    schema = rldata_schema()
    if backend is None:
        backend = ibis
    return (
        backend.read_csv(path)
        .cast(schema)
        .select(*schema.keys())
        .order_by("record_id")
        .cache()
    )


def load_rldata10000(backend: ibis.BaseBackend | None = None) -> ir.Table:
    """Synthetic personal information dataset with 10000 rows

    This is a synthetic dataset with noisy names and dates of birth, with the task being
    to determine which rows represent the same person. 10% of the records are duplicates
    of existing ones, and the level of noise is low. The dataset can be deduplicated with 90%+
    precision and recall using simple linkage rules. It is often used as a
    sanity check for computational efficiency and disambiguation accuracy.

    This comes from the
    [RecordLinkage R package](https://cran.r-project.org/web/packages/RecordLinkage/index.html)
    and was generated using the data generation component of
    [Febrl (Freely Extensible Biomedical Record Linkage)](https://sourceforge.net/projects/febrl/).

    Returns
    -------
    Table
        An Ibis Table with the following schema:

        - record_id: int64
          A unique ID for each row in the table.
        - label_true: int64
          The manually labeled, true ID of the inventor.
        - fname_c1: string
          First component of the first name.
        - fname_c2: string
          Second component of the first name (mostly NULL values)
        - lname_c1: string
          First component of the last name.
        - lname_c2: string
          Second component of the last name (mostly NULL values).
        - by: int64
          Birth year
        - bm: int64
          Birth month
        - bd: int64
          Birth day

    Examples
    --------
    >>> load_rldata10000()
    ┏━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━┳━━━━━━━┳━━━━━━━┓
    ┃ record_id ┃ label_true ┃ fname_c1 ┃ fname_c2 ┃ lname_c1   ┃ lname_c2 ┃ by    ┃ bm    ┃ bd    ┃
    ┡━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━╇━━━━━━━╇━━━━━━━┩
    │ int64     │ int64      │ string   │ string   │ string     │ string   │ int64 │ int64 │ int64 │
    ├───────────┼────────────┼──────────┼──────────┼────────────┼──────────┼───────┼───────┼───────┤
    │         0 │       3606 │ FRANK    │ NULL     │ MUELLER    │ NULL     │  1967 │     9 │    27 │
    │         1 │       2560 │ MARTIN   │ NULL     │ SCHWARZ    │ NULL     │  1967 │     2 │    17 │
    │         2 │       3892 │ HERBERT  │ NULL     │ ZIMMERMANN │ NULL     │  1961 │    11 │     6 │
    │         3 │        329 │ HANS     │ NULL     │ SCHMITT    │ NULL     │  1945 │     8 │    14 │
    │         4 │       1994 │ UWE      │ NULL     │ KELLER     │ NULL     │  2000 │     7 │     5 │
    │         5 │       2330 │ DANIEL   │ NULL     │ HEINRICH   │ NULL     │  1967 │     5 │     6 │
    │         6 │       4420 │ MARTIN   │ NULL     │ ZIMMERMANN │ NULL     │  1982 │    11 │     2 │
    │         7 │       2534 │ ANDREAS  │ BENJAMIN │ BERGMANN   │ NULL     │  1989 │     9 │    13 │
    │         8 │       3076 │ DIETER   │ NULL     │ SCHUSTER   │ NULL     │  1974 │     4 │    19 │
    │         9 │       4305 │ MANFRED  │ NULL     │ SCHMIDT    │ NULL     │  1979 │     7 │    11 │
    │         … │          … │ …        │ …        │ …          │ …        │     … │     … │     … │
    └───────────┴────────────┴──────────┴──────────┴────────────┴──────────┴───────┴───────┴───────┘
    """  # noqa: E501
    path = _DATASETS_DIR / "rldata/RLdata10000.csv"
    schema = rldata_schema()
    if backend is None:
        backend = ibis
    return (
        backend.read_csv(path)
        .cast(schema)
        .select(*schema.keys())
        .order_by("record_id")
        .cache()
    )
