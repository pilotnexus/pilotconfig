run: guard-PILOT_DEVENV_PI_node
	python3 -m pilot.pilot setup --host $(PILOT_DEVENV_PI_node)
upload:
	rm -f dist/*
	rm -r build/*
	python3 setup.py sdist bdist_wheel
	twine upload dist/*

deploy: guard-PILOT_DEVENV_PI_node
	sshpass -p raspberry rsync -av --exclude 'node_modules*' ./pilot pi@$(PILOT_DEVENV_PI_node):~/pilot-config

guard-%:
	@if [ "${${*}}" = "" ]; then \
		echo "Environment variable $* not set"; \
		exit 1; \
	fi
