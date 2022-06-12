from typing import Iterable, Protocol

import modin.pandas as pd

from mismo._typing import Data, Links
from mismo.block.fingerprint import PFingerprinter, check_fingerprints


class PBlocker(Protocol):
    def block(self, data1: Data, data2: Data) -> Links:
        ...


FingerprinterPair = tuple[PFingerprinter, PFingerprinter]
FingerprinterPairsLike = Iterable[FingerprinterPair]


class FingerprintBlocker(PBlocker):
    fingerprinters: list[FingerprinterPair]

    def __init__(self, fingerprinters: FingerprinterPairsLike) -> None:
        self.fingerprinters = self._convert_fingerprinters(fingerprinters)

    def block(self, data1: Data, data2: Data) -> Links:
        link_chunks = []
        for fp1, fp2 in self.fingerprinters:
            prints1 = fp1.fingerprint(data1)
            prints2 = fp2.fingerprint(data2)
            link_chunk = merge_fingerprints(prints1, prints2)
            link_chunks.append(link_chunk)
        links: pd.DataFrame = pd.concat(link_chunks)
        links.drop_duplicates(inplace=True)
        links.sort_values(by=["index_1", "index_2"], inplace=True)
        return links

    @staticmethod
    def _is_fingerprinter(fp):
        return hasattr(fp, "fingerprint")

    @classmethod
    def _convert_fingerprinters(
        cls, fps: FingerprinterPairsLike
    ) -> list[FingerprinterPair]:
        fps_list = list(fps)
        if not fps_list:
            raise ValueError("Fingerprinters must not be empty")
        result = []
        for fp in fps_list:
            pair = tuple(fp)
            if not len(pair) == 2:
                raise ValueError(
                    "Fingerprinters must be a sequence of length 2. ",
                    f"Got {pair}",
                )
            if not cls._is_fingerprinter(pair[0]) or not cls._is_fingerprinter(pair[1]):
                raise ValueError(
                    "Fingerprinters must be instances of Fingerprinter. ",
                    f"Got {pair}",
                )
            result.append(pair)
        # mypy doesn't understand that pair is length 2.
        return result  # type: ignore


def merge_fingerprints(fp1: pd.DataFrame, fp2: pd.DataFrame) -> Links:
    check_fingerprints(fp1)
    check_fingerprints(fp2)
    non_index1 = [c for c in fp1.columns if c != "index"]
    non_index2 = [c for c in fp2.columns if c != "index"]
    links: pd.DataFrame = pd.merge(
        fp1,
        fp2,
        left_on=non_index1,
        right_on=non_index2,
        suffixes=("_1", "_2"),
    )
    links = links[["index_1", "index_2"]]
    links = links.drop_duplicates()
    return links