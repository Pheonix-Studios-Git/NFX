# NFX Changelog

## Version 1.0.2
### Upgrades
- Security Flaw fixes
- Bug fixes
- Removal of Self-Signing packages

### Additions
- Addition of singular validity/signing key

### Known Flaws
- Introduced a bug in 'installs' command preventing it from working properly
- Introduced 'upgrade_package' function bug, causing it to not upgrade same version but different revision packages

## Version 1.0.3
### Upgrades
- Fixed 'installs' command bug, allowing it to function properly again
- Fixed 'upgrade_package' function bug, causing it to misidentify downloaded packages
- Fixed 'upgrade_package' function bug, causing it to not upgrade same version but different revision packages

### Additions
- Changelog addition
- Re-implemented 'all' flag for 'info' command
- Added *Rich* Markdown support

### Known Flaws
- None
