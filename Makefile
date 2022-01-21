.PHONY: setup
setup: packages

.PHONY: packages
packages:
	pipenv install --system --deploy

.PHONY: dev-packages
dev-packages:
	pipenv install --dev --system

.PHONY:
test:
	pytest -v . $(PYTEST_OPTIONS) -vv

.PHONY: snapshot-update
snapshot-update: PYTEST_OPTIONS := --snapshot-update
snapshot-update: test

.PHONY: autoflake
autoflake:
	autoflake -r $(AUTOFLAKE_OPTIONS) --remove-unused-variables --remove-all-unused-imports  ./api ./tests | tee autoflake.log
	echo "$(AUTOFLAKE_OPTIONS)" | grep -q -- '--in-place' || ! [ -s autoflake.log ]

.PHONY: lint
lint: ISORT_OPTIONS := --check-only
lint: BLACK_OPTIONS := --check
lint: autoflake format

.PHONY: format
format: AUTOFLAKE_OPTIONS := --in-place
format: autoflake
	isort ./api ./tests $(ISORT_OPTIONS)
	black ./api ./tests --exclude '.*/(snapshots|snapshottest)/.*|.git' $(BLACK_OPTIONS)

.PHONY:
run:
	FLASK_DEBUG=1 FLASK_ENV=development FLASK_APP=api.app:flask_app flask run  --host=127.0.0.1 --port=8001

