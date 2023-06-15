from __future__ import annotations

from ibis.expr.types import Table


def format_table(template: str, name: str, table: Table) -> str:
    t = repr(table.head(5))
    nindent = 0
    search = "{" + name + "}"
    for line in template.splitlines():
        try:
            nindent = line.index(search)
        except ValueError:
            continue
    indent = " " * nindent
    sep = "\n" + indent
    t = sep.join(line for line in t.splitlines())
    return template.format(table=t)