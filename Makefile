.SILENT:
.PHONY: env up clean

# Default target
env: .env

# Create .env file from template using 1password CLI
.env: tpl.env
	@echo "Generating .env file from template..."
	@op inject -i tpl.env -o .env
	@echo ".env file generated successfully"

# Clean generated files
clean:
	@rm -f .env
	@echo "Cleaned .env file"

# Run weather.py in virtual environment
up: .env
	@.venv/bin/python weather.py