NFX_ERROR_UNKNOWN = 1000
NFX_ERROR_INTERNAL = 1001
NFX_ERROR_NOT_IMPLEMENTED = 1002
NFX_ERROR_TIMEOUT = 1003
NFX_ERROR_INTERRUPTED = 1004
NFX_ERROR_INVALID_ARGUMENT = 1005
NFX_ERROR_INVALID_STATE = 1006
NFX_ERROR_NULL_REFERENCE = 1007
NFX_ERROR_BUFFER_OVERFLOW = 1008
NFX_ERROR_UNSUPPORTED_PLATFORM = 1009

NFX_ERROR_FILE_NOT_FOUND = 1100
NFX_ERROR_FILE_READ_FAILED = 1101
NFX_ERROR_FILE_WRITE_FAILED = 1102
NFX_ERROR_DIRECTORY_NOT_FOUND = 1103
NFX_ERROR_PERMISSION_DENIED = 1104
NFX_ERROR_DISK_FULL = 1105
NFX_ERROR_PATH_TOO_LONG = 1106
NFX_ERROR_TEMPFILE_CREATION_FAILED = 1107
NFX_ERROR_CACHE_CORRUPTED = 1108
NFX_ERROR_LOCKFILE_BROKEN = 1109

NFX_ERROR_PACKAGE_NOT_FOUND = 1200
NFX_ERROR_PACKAGE_ALREADY_INSTALLED = 1201
NFX_ERROR_PACKAGE_CONFLICT = 1202
NFX_ERROR_DEPENDENCY_NOT_FOUND = 1203
NFX_ERROR_DEPENDENCY_CYCLE = 1204
NFX_ERROR_VERSION_CONFLICT = 1205
NFX_ERROR_INVALID_PACKAGE_NAME = 1206
NFX_ERROR_INVALID_PACKAGE_VERSION = 1207
NFX_ERROR_REPOSITORY_UNAVAILABLE = 1208
NFX_ERROR_MIRROR_UNREACHABLE = 1209

NFX_ERROR_HTTP_BAD_REQUEST = 1300
NFX_ERROR_HTTP_UNAUTHORIZED = 1301
NFX_ERROR_HTTP_FORBIDDEN = 1302
NFX_ERROR_HTTP_NOT_FOUND = 1303
NFX_ERROR_HTTP_METHOD_NOT_ALLOWED = 1304
NFX_ERROR_HTTP_CONFLICT = 1305
NFX_ERROR_HTTP_TOO_MANY_REQUESTS = 1306
NFX_ERROR_HTTP_INTERNAL_SERVER_ERROR = 1307
NFX_ERROR_HTTP_BAD_GATEWAY = 1308
NFX_ERROR_HTTP_SERVICE_UNAVAILABLE = 1309

NFX_ERROR_TLS_HANDSHAKE_FAILED = 1400
NFX_ERROR_TLS_CERTIFICATE_INVALID = 1401
NFX_ERROR_TLS_CERTIFICATE_EXPIRED = 1402
NFX_ERROR_TLS_CERTIFICATE_REVOKED = 1403
NFX_ERROR_TLS_HOSTNAME_MISMATCH = 1404
NFX_ERROR_SECURITY_POLICY_VIOLATION = 1405
NFX_ERROR_UNTRUSTED_SOURCE = 1406
NFX_ERROR_SIGNATURE_VERIFICATION_FAILED = 1407
NFX_ERROR_PUBLIC_KEY_MISSING = 1408
NFX_ERROR_PRIVATE_KEY_UNAVAILABLE = 1409

NFX_ERROR_SHA256_MISMATCH = 1500
NFX_ERROR_SHA512_MISMATCH = 1501
NFX_ERROR_CHECKSUM_MISSING = 1502
NFX_ERROR_CHECKSUM_CORRUPTED = 1503
NFX_ERROR_INTEGRITY_CHECK_FAILED = 1504
NFX_ERROR_MANIFEST_TAMPERED = 1505
NFX_ERROR_PACKAGE_TAMPERED = 1506
NFX_ERROR_INVALID_SIGNATURE_FORMAT = 1507
NFX_ERROR_HASH_ALGORITHM_UNSUPPORTED = 1508
NFX_ERROR_TRUST_CHAIN_INVALID = 1509

NFX_ERROR_KEY_NOT_FOUND = 1600
NFX_ERROR_KEY_EXPIRED = 1601
NFX_ERROR_KEY_REVOKED = 1602
NFX_ERROR_KEY_IMPORT_FAILED = 1603
NFX_ERROR_KEY_EXPORT_FAILED = 1604
NFX_ERROR_KEY_GENERATION_FAILED = 1605
NFX_ERROR_GPG_VERIFICATION_FAILED = 1606
NFX_ERROR_PGP_SIGNATURE_INVALID = 1607
NFX_ERROR_KEYSERVER_UNREACHABLE = 1608
NFX_ERROR_TRUST_DATABASE_CORRUPTED = 1609

NFX_ERROR_ARCHIVE_INVALID = 1700
NFX_ERROR_ARCHIVE_CORRUPTED = 1701
NFX_ERROR_ARCHIVE_EXTRACTION_FAILED = 1702
NFX_ERROR_UNSUPPORTED_ARCHIVE_FORMAT = 1703
NFX_ERROR_COMPRESSION_FAILED = 1704
NFX_ERROR_DECOMPRESSION_FAILED = 1705
NFX_ERROR_ARCHIVE_ENTRY_MISSING = 1706
NFX_ERROR_ARCHIVE_OVERFLOW = 1707
NFX_ERROR_ARCHIVE_PERMISSION_DENIED = 1708
NFX_ERROR_ARCHIVE_SIGNATURE_INVALID = 1709

NFX_ERROR_CONFIG_NOT_FOUND = 1800
NFX_ERROR_CONFIG_INVALID = 1801
NFX_ERROR_CONFIG_PARSE_FAILED = 1802
NFX_ERROR_ENVIRONMENT_INVALID = 1803
NFX_ERROR_MANIFEST_INVALID = 1804
NFX_ERROR_METADATA_MISSING = 1805
NFX_ERROR_METADATA_CORRUPTED = 1806
NFX_ERROR_SCHEMA_VALIDATION_FAILED = 1807
NFX_ERROR_REPOSITORY_METADATA_INVALID = 1808
NFX_ERROR_FEATURE_FLAG_DISABLED = 1809

NFX_ERROR_PROCESS_SPAWN_FAILED = 1900
NFX_ERROR_PROCESS_EXIT_FAILURE = 1901
NFX_ERROR_SANDBOX_VIOLATION = 1902
NFX_ERROR_EXECUTION_DENIED = 1903
NFX_ERROR_SCRIPT_RUNTIME_ERROR = 1904
NFX_ERROR_HOOK_FAILED = 1905
NFX_ERROR_PLUGIN_LOAD_FAILED = 1906
NFX_ERROR_PLUGIN_CRASHED = 1907
NFX_ERROR_PLUGIN_INCOMPATIBLE = 1908
NFX_ERROR_RESOURCE_LIMIT_EXCEEDED = 1909

NFX_ERROR_DATABASE_CONNECTION_FAILED = 2000
NFX_ERROR_DATABASE_QUERY_FAILED = 2001
NFX_ERROR_DATABASE_CORRUPTED = 2002
NFX_ERROR_CACHE_MISS = 2003
NFX_ERROR_CACHE_WRITE_FAILED = 2004
NFX_ERROR_CACHE_READ_FAILED = 2005
NFX_ERROR_INDEX_CORRUPTED = 2006
NFX_ERROR_STATE_DESERIALIZATION_FAILED = 2007
NFX_ERROR_STATE_SERIALIZATION_FAILED = 2008
NFX_ERROR_TRANSACTION_ABORTED = 2009

NFX_ERROR_AUTH_REQUIRED = 2100
NFX_ERROR_AUTH_FAILED = 2101
NFX_ERROR_TOKEN_EXPIRED = 2102
NFX_ERROR_TOKEN_INVALID = 2103
NFX_ERROR_SESSION_INVALID = 2104
NFX_ERROR_ACCESS_DENIED = 2105
NFX_ERROR_SCOPE_INSUFFICIENT = 2106
NFX_ERROR_LOCKED = 2107
NFX_ERROR_MULTI_FACTOR_REQUIRED = 2108
NFX_ERROR_CREDENTIAL_STORE_UNAVAILABLE = 2109

NFX_ERROR_MESSAGES = {
    1000: "Unknown error occurred",
    1001: "Internal system error",
    1002: "Not implemented",
    1003: "Operation timed out",
    1004: "Operation interrupted",
    1005: "Invalid argument provided",
    1006: "Invalid state encountered",
    1007: "Null reference error",
    1008: "Buffer overflow detected",
    1009: "Unsupported platform",

    1100: "File not found",
    1101: "Failed to read file",
    1102: "Failed to write file",
    1103: "Directory not found",
    1104: "Permission denied",
    1105: "Disk is full",
    1106: "File path too long",
    1107: "Temporary file creation failed",
    1108: "Cache is corrupted",
    1109: "Lockfile is broken",

    1200: "Package not found",
    1201: "Package already installed",
    1202: "Package conflict detected",
    1203: "Dependency not found",
    1204: "Dependency cycle detected",
    1205: "Version conflict detected",
    1206: "Invalid package name",
    1207: "Invalid package version",
    1208: "Repository unavailable",
    1209: "Mirror unreachable",

    1300: "HTTP bad request",
    1301: "HTTP unauthorized",
    1302: "HTTP forbidden",
    1303: "HTTP not found",
    1304: "HTTP method not allowed",
    1305: "HTTP conflict",
    1306: "HTTP too many requests",
    1307: "HTTP internal server error",
    1308: "HTTP bad gateway",
    1309: "HTTP service unavailable",

    1400: "TLS handshake failed",
    1401: "Invalid TLS certificate",
    1402: "Expired TLS certificate",
    1403: "Revoked TLS certificate",
    1404: "TLS hostname mismatch",
    1405: "Security policy violation",
    1406: "Untrusted source",
    1407: "Signature verification failed",
    1408: "Public key missing",
    1409: "Private key unavailable",

    1500: "SHA256 mismatch",
    1501: "SHA512 mismatch",
    1502: "Checksum missing",
    1503: "Checksum corrupted",
    1504: "Integrity check failed",
    1505: "Manifest tampered",
    1506: "Package tampered",
    1507: "Invalid signature format",
    1508: "Unsupported hash algorithm",
    1509: "Trust chain invalid",

    1600: "Key not found",
    1601: "Key expired",
    1602: "Key revoked",
    1603: "Key import failed",
    1604: "Key export failed",
    1605: "Key generation failed",
    1606: "GPG verification failed",
    1607: "PGP signature invalid",
    1608: "Keyserver unreachable",
    1609: "Trust database corrupted",

    1700: "Archive invalid",
    1701: "Archive corrupted",
    1702: "Archive extraction failed",
    1703: "Unsupported archive format",
    1704: "Compression failed",
    1705: "Decompression failed",
    1706: "Archive entry missing",
    1707: "Archive overflow",
    1708: "Archive permission denied",
    1709: "Archive signature invalid",

    1800: "Configuration not found",
    1801: "Invalid configuration",
    1802: "Configuration parse failed",
    1803: "Invalid environment",
    1804: "Manifest invalid",
    1805: "Metadata missing",
    1806: "Metadata corrupted",
    1807: "Schema validation failed",
    1808: "Repository metadata invalid",
    1809: "Feature flag disabled",

    1900: "Process spawn failed",
    1901: "Process exit failure",
    1902: "Sandbox violation",
    1903: "Execution denied",
    1904: "Script runtime error",
    1905: "Hook failed",
    1906: "Plugin load failed",
    1907: "Plugin crashed",
    1908: "Plugin incompatible",
    1909: "Resource limit exceeded",

    2000: "Database connection failed",
    2001: "Database query failed",
    2002: "Database corrupted",
    2003: "Cache miss",
    2004: "Cache write failed",
    2005: "Cache read failed",
    2006: "Index corrupted",
    2007: "State deserialization failed",
    2008: "State serialization failed",
    2009: "Transaction aborted",

    2100: "Authentication required",
    2101: "Authentication failed",
    2102: "Token expired",
    2103: "Token invalid",
    2104: "Session invalid",
    2105: "Access denied",
    2106: "Insufficient scope",
    2107: "Nfx locked (Probably another NFX instance running)",
    2108: "Multi-factor authentication required",
    2109: "Credential store unavailable",
}