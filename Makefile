# Makefile for TechSpecsTVI
# Build + Glossary/Index + Bibliography + Audit (CI)
# ------------------------------------------------------------------
# Usage examples:
#   make                (default: full build: PDF + glossaries + index)
#   make fast           (single engine pass; no biber/glossaries)
#   make audit          (run glossary/index audit with fail conditions)
#   make ci             (full build + audit; fails on audit violations)
#   make clean          (remove intermediate build artifacts)
#   make distclean      (clean + remove final PDF)
#
# Variables you can override (e.g., `make ENGINE=xelatex`):
#   ENGINE       (lualatex|xelatex) default lualatex
#   TEX          main (basename of .tex master file)
#   FAIL_ON      audit fail conditions (unused-terms unindexed-first-use orphan-index alias-target-missing)
#
# CI Suggestion:
#   make ci FAIL_ON="all"
#
# ------------------------------------------------------------------

SHELL          := /bin/bash
ENGINE         ?= lualatex
TEX            ?= main
BIB            ?= biber
GLOSSCMD       ?= makeglossaries
PYTHON         ?= python3

# Audit script configuration
AUDIT_SCRIPT   := scripts/glossary_index_audit.py
AUDIT_CHAPTERS := Chapters
AUDIT_GLOSS    := IndexingGlossary/glossary_definitions.tex glossary_preamble.tex
AUDIT_IDX      := $(TEX).idx
FAIL_ON        ?=
AUDIT_BASE_CMD := $(PYTHON) $(AUDIT_SCRIPT) --chapters-dir $(AUDIT_CHAPTERS) --glossary-files $(AUDIT_GLOSS) --idx-file $(AUDIT_IDX)

# Colors (optional)
C_RESET  := \033[0m
C_INFO   := \033[1;34m
C_WARN   := \033[1;33m
C_ERR    := \033[1;31m
C_OK     := \033[1;32m

PDF      := $(TEX).pdf

.PHONY: all build fast biber pass1 pass2 gloss index audit audit-markdown audit-json ci clean distclean help

# Default target
all: build

help:
	@echo -e "$(C_INFO)Targets:$(C_RESET)"
	@grep -E '^[a-zA-Z_-]+:.*?##' $(MAKEFILE_LIST) | sed -E 's/:.*?##/: /' | sort
	@echo -e "$(C_INFO)Variables: ENGINE (lualatex|xelatex), FAIL_ON, TEX$(C_RESET)"

# ------------------------------------------------------------------
# Build pipeline
# ------------------------------------------------------------------

build: pass1 biber pass2 gloss pass3 ## Full document build (PDF + bibliography + glossaries/index)
	@echo -e "$(C_OK)[OK] Build complete: $(PDF)$(C_RESET)"

fast: ## Quick single compile (no biber, no glossaries) for rapid iteration
	@echo -e "$(C_INFO)[FAST] $(ENGINE) $(TEX).tex$(C_RESET)"
	@$(ENGINE) -interaction=nonstopmode -halt-on-error $(TEX).tex || (echo -e "$(C_ERR)LaTeX FAST build failed$(C_RESET)"; exit 1)

pass1:
	@echo -e "$(C_INFO)[1/5] LaTeX pass (structure)$(C_RESET)"
	@$(ENGINE) -interaction=nonstopmode -halt-on-error $(TEX).tex || (echo -e "$(C_ERR)LaTeX pass1 failed$(C_RESET)"; exit 1)

biber:
	@echo -e "$(C_INFO)[2/5] Bibliography (biber)$(C_RESET)"
	@$(BIB) $(TEX) || (echo -e "$(C_ERR)Biber failed$(C_RESET)"; exit 1)

pass2:
	@echo -e "$(C_INFO)[3/5] LaTeX pass (resolve refs)$(C_RESET)"
	@$(ENGINE) -interaction=nonstopmode -halt-on-error $(TEX).tex || (echo -e "$(C_ERR)LaTeX pass2 failed$(C_RESET)"; exit 1)

gloss:
	@echo -e "$(C_INFO)[4/5] Glossaries / Index$(C_RESET)"
	@$(GLOSSCMD) $(TEX) || (echo -e "$(C_ERR)Glossary generation failed$(C_RESET)"; exit 1)

pass3:
	@echo -e "$(C_INFO)[5/5] Final LaTeX pass$(C_RESET)"
	@$(ENGINE) -interaction=nonstopmode -halt-on-error $(TEX).tex || (echo -e "$(C_ERR)LaTeX pass3 failed$(C_RESET)"; exit 1)

# ------------------------------------------------------------------
# Audit targets
# ------------------------------------------------------------------

audit: ## Run glossary/index audit (human-readable)
	@echo -e "$(C_INFO)[AUDIT] glossary/index audit$(C_RESET)"
	@$(AUDIT_BASE_CMD) $(if $(FAIL_ON),--fail-on $(FAIL_ON),)

audit-markdown: ## Audit with Markdown output
	@echo -e "$(C_INFO)[AUDIT] (Markdown)$(C_RESET)"
	@$(AUDIT_BASE_CMD) --markdown $(if $(FAIL_ON),--fail-on $(FAIL_ON),)

audit-json: ## Audit with JSON output
	@echo -e "$(C_INFO)[AUDIT] (JSON)$(C_RESET)"
	@$(AUDIT_BASE_CMD) --json $(if $(FAIL_ON),--fail-on $(FAIL_ON),)

ci: build audit ## CI pipeline: full build + audit (set FAIL_ON=all for strict mode)
	@echo -e "$(C_OK)[CI] Build + audit succeeded$(C_RESET)"

# ------------------------------------------------------------------
# Cleaning
# ------------------------------------------------------------------

CLEAN_EXT = aux bbl bcf blg glg glo gls ist idx ilg ind lof log lot out run.xml toc pytxcode acn acr alg xdy fdb_latexmk fls nav snm vrb

clean: ## Remove intermediate build artifacts
	@echo -e "$(C_WARN)[CLEAN] Removing intermediate files$(C_RESET)"
	@for e in $(CLEAN_EXT); do rm -f $(TEX).$$e; done
	@rm -f $(TEX).gls* $(TEX).glo* $(TEX).glg* $(TEX).synctex.gz

distclean: clean ## Remove final PDF as well
	@echo -e "$(C_WARN)[DISTCLEAN] Removing final PDF$(C_RESET)"
	@rm -f $(PDF)

# ------------------------------------------------------------------
# Sanity checks
# ------------------------------------------------------------------

check-script:
	@[ -f $(AUDIT_SCRIPT) ] || (echo -e "$(C_ERR)Missing audit script: $(AUDIT_SCRIPT)$(C_RESET)"; exit 1)

check-glossary:
	@for gf in $(AUDIT_GLOSS); do \
		if [ ! -f $$gf ]; then echo -e "$(C_ERR)Missing glossary file $$gf$(C_RESET)"; exit 1; fi; \
	done

preflight: check-script check-glossary ## Validate presence of audit + glossary files
	@echo -e "$(C_OK)[OK] Preflight checks passed$(C_RESET)"

# ------------------------------------------------------------------
# Convenience target to print summary variables
# ------------------------------------------------------------------
vars:
	@echo "ENGINE=$(ENGINE)"
	@echo "TEX=$(TEX)"
	@echo "FAIL_ON=$(FAIL_ON)"
	@echo "AUDIT_CHAPTERS=$(AUDIT_CHAPTERS)"
	@echo "AUDIT_GLOSS=$(AUDIT_GLOSS)"
	@echo "AUDIT_SCRIPT=$(AUDIT_SCRIPT)"
	@echo "AUDIT_IDX=$(AUDIT_IDX)"

# End of Makefile
