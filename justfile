# Copied from https://github.com/ibis-project/ibis/blob/master/justfile

# list justfile recipes
default:
    just --list

# initialize development environment (but don't activate it)
install:
    pdm install -d -G :all

# format code
fmt:
    black mismo docs
    ruff --fix mismo docs
    nbqa ruff --fix mismo docs

# lint code
lint:
    black --check mismo docs
    ruff mismo docs
    nbqa ruff mismo docs

# run tests
test:
    pytest

# build docs to the site/ directory
docs-build:
    PYDEVD_DISABLE_FILE_VALIDATION=1 mkdocs build

# serve docs for live editing
docs-serve:
    PYDEVD_DISABLE_FILE_VALIDATION=1 mkdocs serve

# publish docs
docs-publish:
    mkdocs gh-deploy --force

# lock dependencies
deps-lock:
    pdm lock -dG :all

# update dependencies
deps-update:
    pdm update -dG :all --update-all  --update-eager
