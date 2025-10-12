.PHONY: bootstrap login whoami

bootstrap:
	@echo "Installing core CLIs…"
	# optional: npm i -g pnpm serverless
	@echo "Done."

login:
	aws sso login --profile meded-dev

whoami:
	aws sts get-caller-identity --profile meded-dev

