"""
Blocking is the process of selecting which pairs of records should be further compared.

Because pairwise comparisons is an O(n^2) operation, it is infeasible to compare all
pairs of records. Therefore, we use blocking to reduce the number of pairs that need
to be compared, hopefully to a manageable level.
"""
from __future__ import annotations

from mismo.block._array import ArrayBlocker as ArrayBlocker
from mismo.block._blocking import BlockingRule as BlockingRule
from mismo.block._blocking import block as block
from mismo.block._sql_analyze import JOIN_TYPES as JOIN_TYPES
from mismo.block._sql_analyze import SLOW_JOIN_TYPES as SLOW_JOIN_TYPES
from mismo.block._sql_analyze import SlowJoinError as SlowJoinError
from mismo.block._sql_analyze import SlowJoinWarning as SlowJoinWarning
from mismo.block._sql_analyze import check_join_type as check_join_type
from mismo.block._sql_analyze import get_join_type as get_join_type
from mismo.block._upset_block import upset_chart as upset_chart
from mismo.block._util import join as join
