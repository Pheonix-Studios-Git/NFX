NFX := nfx/nfx.json
LICENSE := LICENSE
README := README.md

NFX_LINUX_OUT := dist/nfx

BUILD_DIR := nfx_zip
KEY_DIR := keys
NFX_DIR := nfx

ZIP := $(BUILD_DIR)/NFX.zip
CANON_NFX := $(NFX_DIR)/nfx.canonical.json
SIG := $(BUILD_DIR)/NFX.zip.sig

# Colors
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
CYAN := \033[0;36m
RESET := \033[0m

.PHONY: all clean

dirs:
	@mkdir -p $(BUILD_DIR) $(KEY_DIR) $(NFX_DIR)

build-linux:
	@printf "$(YELLOW)==> Building %s \n$(RESET)" $(NFX_LINUX_OUT)
	@pyinstaller src/__main__.py \
		--onefile \
		--name nfx \
		--distpath dist \
		--workpath build \
		--specpath build
	@printf "$(GREEN)==> Done building %s \n$(RESET)" $(NFX_LINUX_OUT)

canonical: $(NFX_DIR)/tmp2.json
	@printf "$(YELLOW)==> Creating canonical JSON... (%s) \n$(RESET)" $(CANON_NFX)
	@jq -S . $(NFX_DIR)/tmp2.json > $(CANON_NFX) && rm $(NFX_DIR)/tmp2.json
	@printf "$(GREEN)==> Created canonical JSON! (%s) \n$(RESET)" $(CANON_NFX)

sizes:
	@printf "$(YELLOW)==> Getting Sizes... \n$(RESET)"
	@SIZE=$$(stat -c %s $(NFX_LINUX_OUT) | awk '{print $$1}'); \
		printf "$(GREEN)==> Got size for %s -> %s \n$(RESET)" $(NFX_LINUX_OUT) $$SIZE; \
		jq '.Binaries[0].Size = '$$SIZE'' $(NFX_DIR)/tmp1.json > $(NFX_DIR)/tmp2.json && rm $(NFX_DIR)/tmp1.json

hashes:
	@printf "$(YELLOW)==> Getting Hashes... \n$(RESET)"
	@HASH=$$(sha256sum $(NFX_LINUX_OUT) | awk '{print $$1}'); \
		printf "$(GREEN)==> Got hash for %s -> %s \n$(RESET)" $(NFX_LINUX_OUT) $$HASH; \
		jq '.Binaries[0].Sha256 = "'$$HASH'"' $(NFX) > $(NFX_DIR)/tmp1.json
	
zip: dirs build-linux canonical
	@printf "$(YELLOW)==> Creating Zip... (%s) \n$(RESET)" $(ZIP)
	@cp $(CANON_NFX) nfx.json
	@zip -r $(ZIP) \
		nfx.json \
		$(NFX_LINUX_OUT) \
		$(LICENSE) \
		$(README) \
		$(KEY_DIR)/allowed_signers
	@rm nfx.json
	@printf "$(GREEN)==> Created Zip! (%s) \n$(RESET)" $(ZIP)
sign: zip
	@printf "$(YELLOW)==> Signing... \n$(RESET)"

	@if [ -z "$(PRIV_KEY)" ]; then \
		printf "$(RED)==> PRIV_KEY is not set. Usage: make sign PRIV_KEY=<key> \n$(RESET)"; \
		exit 1; \
	fi

	@ssh-keygen -Y sign \
		-f $(PRIV_KEY) \
		-n file \
		$(ZIP)

	@printf "$(GREEN)==> Signed! \n$(RESET)"

verify:
	@printf "$(YELLOW)==> Verifying... \n$(RESET)" $(CANON_NFX)

	@ssh-keygen -Y verify \
		-f $(KEY_DIR)/allowed_signers \
		-I pheonix-nfx \
		-n file \
		-s $(SIG) \
		< $(ZIP)
	@printf "$(GREEN)==> Verification complete! \n$(RESET)"

all: dirs build-linux hashes sizes canonical zip sign verify
	@printf "$(GREEN)==> Packaged at %s (unsigned) and %s (signed) \n$(RESET)" $(ZIP) $(SIG)

clean:
	@printf "$(YELLOW)==> Cleaning... \n$(RESET)"
	@rm -rf $(BUILD_DIR) $(CANON_NFX)
	@printf "$(GREEN)==> Cleaned! \n$(RESET)"