# Copied from https://github.com/ibis-project/ibis/blob/master/justfile

# list justfile recipes
default:
    just --list

# initialize development environment
init:
    pdm install -d -G :all
    . .venv/bin/activate

# format code
fmt:
    black .
    ruff --fix .
    nbqa ruff --fix .

# lint code
lint:
    ruff .
    nbqa ruff .
    black -q . --check
    mypy mismo

# run tests
test:
    pytest

# publish docs
docs-publish:
    mkdocs gh-deploy --force

# lock dependencies
lock:
    pdm lock -dG :all

# update dependencies
update-deps:
    pdm update -dG :all
