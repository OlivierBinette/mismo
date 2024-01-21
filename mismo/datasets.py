from __future__ import annotations

from pathlib import Path

import ibis
from ibis.expr.types import Table

from mismo import _util

__all__ = [
    "load_febrl1",
    "load_febrl2",
    "load_febrl3",
    "load_patents",
    "load_rldata500",
    "load_rldata10000",
    "load_cen_msr",
]

_DATASETS_DIR = Path(__file__).parent / "_data/_datasets"


def _wrap_febrl(loader_name: str) -> tuple[Table, Table]:
    with _util.optional_import():
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


def load_febrl1() -> tuple[Table, Table]:
    return _wrap_febrl("load_febrl1")


def load_febrl2() -> tuple[Table, Table]:
    return _wrap_febrl("load_febrl2")


def load_febrl3() -> tuple[Table, Table]:
    return _wrap_febrl("load_febrl3")


# Don't bother wrapping load_febrl4 because it has a different API,
# could add that later if it's needed.


def load_patents(backend: ibis.BaseBackend | None = None) -> Table:
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
        - name_true: string
          The manually labeled, true name of the inventor.
        - name: string
          The raw name on the patent.
        - latitude: float64
          Geocoded from the inventor's address. 0.0 indicates no address was found
        - longitude: float64
        - coauthor: string
          A list of coauthors on the patent, separated by "**"
        - class_:string
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


def load_rldata500(backend: ibis.BaseBackend | None = None) -> Table:
    """Synthetic personal information dataset with 500 rows

    This is a synthetic dataset with noisy names and dates of birth, with the task being
    to determine which rows represent the same person. The duplication rate is 10% and
    the level of noise is low. The dataset can be deduplicated with 90%+
    precision and recall using very simple linkage rules. It is often used as a
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
    if backend is None:
        backend = ibis
    return backend.read_csv(path).order_by("record_id").cache()


def load_rldata10000(backend: ibis.BaseBackend | None = None) -> Table:
    """Synthetic personal information dataset with 10000 rows

    This is a synthetic dataset with noisy names and dates of birth, with the task being
    to determine which rows represent the same person. The duplication rate is 10% and
    the level of noise is low. The dataset can be deduplicated with 90%+
    precision and recall using very simple linkage rules. It is often used as a
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
    if backend is None:
        backend = ibis
    return backend.read_csv(path).order_by("record_id").cache()


def load_cen_msr(backend: ibis.BaseBackend | None = None) -> tuple[Table, Table]:
    """Bipartite record linkage datasets based on Union Army Data

    This function returns two datasets, `CEN` and `MSR`, with no duplication within, but with
    duplication between. These datasets contain personal information about
    civil war soldiers from the Union Army and their family members.
    The task is to link the civil war soldiers in the
    `MSR` dataset (Military Service Records) to their corresponding records in the
    `CEN` dataset (1900 Census Data), while accounting for noise and avoiding false matches.

    Notes
    -----

    The `CEN` and `MSR` datasets were derived from the
    [Union Army Data Set](https://www.nber.org/research/data/union-army-data-set)
    for use in the paper titled
    ["Optimal F-Score Clustering for Bipartite Record Linkage"](https://arxiv.org/pdf/2311.13923.pdf).

    From the paper:

    > "The Union Army data comprise a longitudinal sample of Civil War veterans collected as part of the
    Early Indicators of Aging project (Fogel et al., 2000). Records of soldiers from 331 Union companies
    were collected and carefully linked to a data file comprising military service records—which we call
    the MSR file—as well as other sources. These records also were linked to the 1850, 1860, 1900,
    and 1910 censuses. The quality of the linkages in this project is considered very high, as the true
    matches were manually made by experts (Fogel et al., 2000). Thus, the Union Army data file can
    be used to test automated record linkage algorithms."

    > "We consider re-linking soldiers from the MSR data to records from the 1900 census, which we
    call the CEN data file. This linkage problem is difficult for automated record linkage algorithms due
    to the presence of soldiers' family members in the CEN data. Furthermore, not all soldiers from
    the MSR data have a match in the CEN data. However, we can consider the linkages identified by
    the Early Indicators of Aging project as truth. For the linking fields, we use first name, last name,
    middle initial, and approximate birth year."

    Note that the `CEN` file only contains:
    1. The 1900 census records of soldiers who match `MSR` records in the Union Army dataset.
    2. The 1900 census records of family members of these soldiers.

    A unique identifier recorded in the `label_true` attribute can be used to identify matches.
    Some records have an NULL value for this unique identifier, since they were out of the scope
    of the linkage performed for the Union Army Dataset.

    Returns
    -------
    tuple[Table, Table]
        Tuple containing the `CEN` and `MSR` tables, with the following schemas.
        Note that the `birth_year` and `birth_month` columns are strings
        in the `CEN` dataset (because they can be poorly formatted),
        but integers in the `MSR` dataset.

        **CEN dataset:**
        - record_id: int64
            Sequential identification of rows in the table.
        - label_true: int64
            Unique identifier for recruits in the Union Army dataset. This identifier
            can be used to identify matches between the `CEN` and `MSR` datasets.
            Note that some records have a NULL value for this unique identifier,
            since they were out of the scope of the linkage performed for the
            Union Army Dataset.
        - first_name: string
        - middle_name: string
        - last_name: string
        - birth_year: string
            Often the real year as in "1842", but can be noisy, eg "?R" or "UN".
        - birth_month: string
            Often the month as in "03", but can be noisy, eg "UNK".
        - gender: string
            Gender of the recruit. Usually "M" or "F", but can contain junk.
        - birth_place: string
            Two letter code representing a state, country, continent, etc.
            eg "NY" (New York), "AG" (Afghanistan), "AS" (Aboard Ship).
            See the paper for more details.

        **MSR dataset:**
        - record_id: int64
            Sequential identification of rows in the table.
        - label_true: int64
            Unique identifier for recruits in the Union Army dataset, as above.
        - first_name: string
        - middle_name: string
        - last_name: string
        - birth_date: string
            In YYYYMMDD format. Dashes are used for missing values, eg "186-12--".
        - birth_place: string
            Two letter code representing a state, country, continent, etc.
            eg "NY" (New York), "AG" (Afghanistan), "AS" (Aboard Ship).
            See the paper for more details.
        - enlist_date: string
            In YYYYMMDD format. Dashes are used for missing values, eg "186-12--".
        - enlist_age: int64
            Can be NULL. May be untrustworthy, as the age of 2 appears, which
            seems unlikely to be true.

    Examples
    --------
    >>> CEN, MSR = load_cen_msr()
    >>> CEN
    ┏━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━┓
    ┃ record_id ┃ label_true ┃ first_name ┃ middle_name ┃ last_name ┃ birth_year ┃ birth_month ┃ birth_place ┃ gender ┃
    ┡━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━┩
    │ int64     │ string     │ string     │ string      │ string    │ string     │ string      │ string      │ string │
    ├───────────┼────────────┼────────────┼─────────────┼───────────┼────────────┼─────────────┼─────────────┼────────┤
    │         0 │ 0100501002 │ THEODORE   │ F           │ ALKESKEY  │ 1840       │ 03          │ NY          │ M      │
    │         1 │ 0100501004 │ GEORGE     │ A           │ BRADLEY   │ 1847       │ 06          │ CT          │ M      │
    │         2 │ 0100501005 │ WM         │ NULL        │ BURRITT   │ 1847       │ 11          │ CT          │ M      │
    │         3 │ 0100501007 │ FREDRICK   │ J           │ BOOTH     │ 1842       │ 06          │ CT          │ M      │
    │         4 │ 0100501009 │ WILLIAM    │ E           │ BEERS     │ 1839       │ 02          │ CT          │ M      │
    │         5 │ 0100501010 │ THOMAS     │ NULL        │ BENEDICT  │ 1841       │ 02          │ CT          │ M      │
    │         6 │ 0100501018 │ HIRAM      │ M           │ COLE      │ 1843       │ 01          │ CT          │ M      │
    │         7 │ 0100501019 │ HENRY      │ B           │ CURTISS   │ 1840       │ 09          │ CT          │ M      │
    │         8 │ 0100501020 │ JOHN       │ NULL        │ CARNEY    │ 1844       │ 03          │ IR          │ M      │
    │         9 │ 0100501021 │ DAVID      │ O           │ COMSTOCK  │ 1841       │ 02          │ CT          │ M      │
    │         … │ …          │ …          │ …           │ …         │ …          │ …           │ …           │ …      │
    └───────────┴────────────┴────────────┴─────────────┴───────────┴────────────┴─────────────┴─────────────┴────────┘
    >>> MSR
    ┏━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━┓
    ┃ record_id ┃ label_true ┃ first_name ┃ middle_name ┃ last_name ┃ birth_date ┃ birth_place ┃ enlist_date ┃ enlist_age ┃
    ┡━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━┩
    │ int64     │ int64      │ string     │ string      │ string    │ string     │ string      │ string      │ int64      │
    ├───────────┼────────────┼────────────┼─────────────┼───────────┼────────────┼─────────────┼─────────────┼────────────┤
    │     19479 │ 2202202138 │ WILLIAM    │ NULL        │ DAHLBY    │ NULL       │ NULL        │ 08051862    │         20 │
    │     19626 │ 2202309133 │ JAMES      │ NULL        │ RIDD      │ NULL       │ NULL        │ 12141863    │         27 │
    │     19861 │ 2202403214 │ DANIEL     │ O           │ LOUGHELIN │ NULL       │ NULL        │ 09201864    │         21 │
    │     19868 │ 2202607002 │ CLARK      │ NULL        │ ETHER     │ NULL       │ NULL        │ 07271861    │         30 │
    │     19906 │ 2202607040 │ WILLIAM    │ H           │ FINKLE    │ NULL       │ NULL        │ 07271861    │         18 │
    │     19907 │ 2202607041 │ JONATHAN   │ NULL        │ FISH      │ NULL       │ NULL        │ 07271861    │         21 │
    │     19982 │ 2202607116 │ JOHN       │ W           │ NISLY     │ NULL       │ NULL        │ 03031864    │         21 │
    │     19997 │ 2202607131 │ WILLIAM    │ H           │ JONES     │ NULL       │ NULL        │ 11261864    │         22 │
    │     20515 │ 2203703167 │ ROBERT     │ S           │ WARD      │ NULL       │ NULL        │ 10131864    │         19 │
    │     20702 │ 2204205164 │ N          │ NULL        │ VA        │ NULL       │ NULL        │ 11221864    │         27 │
    │         … │          … │ …          │ …           │ …         │ …          │ …           │ …           │          … │
    └───────────┴────────────┴────────────┴─────────────┴───────────┴────────────┴─────────────┴─────────────┴────────────┘
    """  # noqa: E501
    if backend is None:
        backend = ibis

    CEN_path = _DATASETS_DIR / "union_army/CEN.csv"
    CEN_SCHEMA = {
        "record_id": "int64",
        "label_true": "int64",
        "first_name": "string",
        "middle_name": "string",
        "last_name": "string",
        "birth_year": "string",
        "birth_month": "string",
        "birth_place": "string",
        "gender": "string",
    }
    CEN = (
        backend.read_csv(CEN_path)
        .cast(CEN_SCHEMA)
        .select(*CEN_SCHEMA.keys())
        .order_by("record_id")
        .cache()
    )

    MSR_path = _DATASETS_DIR / "union_army/MSR.csv"
    MSR_SCHEMA = {
        "record_id": "int64",
        "label_true": "int64",
        "first_name": "string",
        "middle_name": "string",
        "last_name": "string",
        "birth_date": "string",
        "birth_place": "string",
        "enlist_date": "string",
        "enlist_age": "int64",
    }
    MSR = (
        backend.read_csv(MSR_path)
        .cast(MSR_SCHEMA)
        .select(*MSR_SCHEMA.keys())
        .order_by("record_id")
        .cache()
    )

    return CEN, MSR
