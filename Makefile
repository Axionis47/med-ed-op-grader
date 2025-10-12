.PHONY: bootstrap login whoami api-run api-deps infra-deploy

bootstrap:
	@echo "Installing core CLIs…"
	# optional: npm i -g pnpm serverless
	@echo "Done."

login:
	aws sso login --profile meded-dev

whoami:
	aws sts get-caller-identity --profile meded-dev

api-run:
	uvicorn api.app:app --reload --port 8000

api-deps:
	python3 -m pip install -r api/requirements.txt

infra-deploy:
	npx serverless deploy --config infra/serverless.yml

