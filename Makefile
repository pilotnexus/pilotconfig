run: guard-PILOT_DEVENV_PI_HOST
	python3 -m pilot.pilot setup --host $(PILOT_DEVENV_PI_HOST)
upload:
	rm -f dist/*
	python3 setup.py sdist bdist_wheel
	twine upload dist/*

deploy: guard-PILOT_DEVENV_PI_HOST
	sshpass -p raspberry rsync -av --exclude 'node_modules*' ./pilot pi@$(PILOT_DEVENV_PI_HOST):~/pilot-config

guard-%:
	@if [ "${${*}}" = "" ]; then \
		echo "Environment variable $* not set"; \
		exit 1; \
	fi
