NFX := nfx/nfx.json
LICENSE := LICENSE
README := README.md
VERSION := 1.0.0

LINUX_x86_64_DIR := bin/linux/x86_64
WINDOWS_x86_64_DIR := bin/windows/x86_64
BUILD_DIR := nfx_zip
KEY_DIR := keys
NFX_DIR := nfx

BUILD_DATE := $(shell date +%Y-%m-%d\ %H:%M)

NFX_LINUX_OUT := $(LINUX_x86_64_DIR)/dist/nfx
NFX_WINDOWS_OUT := $(WINDOWS_x86_64_DIR)/dist/nfx.exe

WORK_JSON := $(NFX_DIR)/build.json

ZIP := $(BUILD_DIR)/NFX-v$(VERSION).zip
CANON_NFX := $(NFX_DIR)/nfx.canonical.json
SIG := $(BUILD_DIR)/NFX-v$(VERSION).zip.sig

# Colors
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
CYAN := \033[0;36m
RESET := \033[0m

.PHONY: all clean build-linux

dirs:
	@mkdir -p $(BUILD_DIR) $(KEY_DIR) $(NFX_DIR) bin bin/linux bin/windows bin/linux/x86_64 bin/windows/x86_64 \
		bin/linux/x86_64/dist bin/linux/x86_64/build bin/windows/x86_64/dist bin/windows/x86_64/build

build-linux:
	@printf "$(YELLOW)==> Building %s \n$(RESET)" $(NFX_LINUX_OUT)
	@pyinstaller src/__main__.py \
		--onefile \
		--name nfx \
		--distpath $(LINUX_x86_64_DIR)/dist \
		--workpath $(LINUX_x86_64_DIR)/build \
		--specpath $(LINUX_x86_64_DIR)/build
	@printf "$(GREEN)==> Done building %s \n$(RESET)" $(NFX_LINUX_OUT)

build-windows:
	@printf "$(YELLOW)==> Building %s \n$(RESET)" $(NFX_WINDOWS_OUT)
	@wine python.exe -m PyInstaller src/__main__.py \
		--onefile \
		--name nfx \
		--distpath $(WINDOWS_x86_64_DIR)/dist \
		--workpath $(WINDOWS_x86_64_DIR)/build \
		--specpath $(WINDOWS_x86_64_DIR)/build
	@printf "$(GREEN)==> Done building %s \n$(RESET)" $(NFX_WINDOWS_OUT)

prepare-json:
	@cp $(NFX) $(WORK_JSON)

canonical: sizes date
	@printf "$(YELLOW)==> Creating canonical JSON...\n$(RESET)"
	@jq -S . $(WORK_JSON) > $(CANON_NFX)

sizes: hashes
	@printf "$(YELLOW)==> Getting Sizes...\n$(RESET)"

	@LINUX_SIZE=$$(stat -c %s $(NFX_LINUX_OUT)); \
		printf "$(GREEN)==> Linux size: %s\n$(RESET)" $$LINUX_SIZE; \
		jq '.Binaries[0].Size = '$$LINUX_SIZE'' $(WORK_JSON) > $(WORK_JSON).tmp && mv $(WORK_JSON).tmp $(WORK_JSON)

	@WIN_SIZE=$$(stat -c %s $(NFX_WINDOWS_OUT)); \
		printf "$(GREEN)==> Windows size: %s\n$(RESET)" $$WIN_SIZE; \
		jq '.Binaries[1].Size = '$$WIN_SIZE'' $(WORK_JSON) > $(WORK_JSON).tmp && mv $(WORK_JSON).tmp $(WORK_JSON)

hashes: prepare-json
	@printf "$(YELLOW)==> Getting Hashes...\n$(RESET)"

	@LINUX_HASH=$$(sha256sum $(NFX_LINUX_OUT) | awk '{print $$1}'); \
		printf "$(GREEN)==> Linux hash: %s\n$(RESET)" $$LINUX_HASH; \
		jq '.Binaries[0].Sha256 = "'$$LINUX_HASH'"' $(WORK_JSON) > $(WORK_JSON).tmp && mv $(WORK_JSON).tmp $(WORK_JSON)

	@WIN_HASH=$$(sha256sum $(NFX_WINDOWS_OUT) | awk '{print $$1}'); \
		printf "$(GREEN)==> Windows hash: %s\n$(RESET)" $$WIN_HASH; \
		jq '.Binaries[1].Sha256 = "'$$WIN_HASH'"' $(WORK_JSON) > $(WORK_JSON).tmp && mv $(WORK_JSON).tmp $(WORK_JSON)
	
date:
	@printf "$(YELLOW)==> Injecting build date...\n$(RESET)"
	@jq '.Build.Date = "$(BUILD_DATE)"' $(WORK_JSON) > $(WORK_JSON).tmp && mv $(WORK_JSON).tmp $(WORK_JSON)
	@printf "$(GREEN)==> Build date set to $(BUILD_DATE)\n$(RESET)"

zip: dirs build-linux build-windows canonical
	@printf "$(YELLOW)==> Creating Zip... (%s) \n$(RESET)" $(ZIP)
	@cp $(CANON_NFX) nfx.json
	@zip -r $(ZIP) \
		nfx.json \
		$(NFX_LINUX_OUT) \
		$(NFX_WINDOWS_OUT) \
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

all: dirs build-linux build-windows hashes sizes canonical zip sign verify
	@printf "$(GREEN)==> Packaged at %s (unsigned) and %s (signed) \n$(RESET)" $(ZIP) $(SIG)

clean:
	@printf "$(YELLOW)==> Cleaning... \n$(RESET)"
	@rm -rf $(BUILD_DIR) $(CANON_NFX) bin
	@printf "$(GREEN)==> Cleaned! \n$(RESET)"