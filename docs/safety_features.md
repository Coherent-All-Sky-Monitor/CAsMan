# Safety Features

CAsMan includes comprehensive safety features to prevent accidental data loss and ensure reliable operation.

## Database Safety Features

### Visual Warning System

CAsMan provides prominent visual warnings for destructive operations:

**Stop Sign Warning:**

- Red text on white background stop sign

- Displayed before any destructive database operation

- Cannot be bypassed or disabled

### Double Confirmation System

All destructive database operations require double confirmation:

1. **First Confirmation**: User must type "yes" to proceed
2. **Second Confirmation**: User must type "yes" again to confirm the irreversible action
3. **Immediate Abort**: Any other input immediately cancels the operation

**Example Workflow:**

```bash

$ casman database clear --parts

🛑 STOP SIGN WARNING DISPLAYED

WARNING: This will DELETE ALL records from the parts database at: /path/to/parts.db
Are you sure you want to clear the parts database? (yes/no): yes
This action is IRREVERSIBLE. Type 'yes' again to confirm: yes
All records deleted from parts database.

```python

### Database Integrity Checks

Before performing operations, CAsMan verifies:

- **Database Existence**: Checks if database files exist before operations

- **Database Connectivity**: Verifies connection can be established

- **Schema Validation**: Ensures database schema is correct

- **Backup Creation**: Creates backups before destructive operations (when possible)

### Error Handling

Comprehensive error handling provides:

- **Graceful Degradation**: Operations fail safely without corruption

- **Informative Messages**: Clear error descriptions for troubleshooting

- **Recovery Guidance**: Suggestions for resolving issues

- **Exit Code Management**: Proper exit codes for scripting

## Assembly Chain Validation

### Connection Rules Enforcement

CAsMan enforces strict assembly chain rules:

**Sequence Validation:**

- Parts must connect in order: `ANT → LNA → COAXSHORT → COAXLONG → BACBOARD → SNAP`

- Invalid sequences are immediately rejected

- Real-time validation during scanning

**Directionality Enforcement:**

- ANTENNA parts can only be sources (no incoming connections)

- SNAP parts can only be targets (no outgoing connections)

- Intermediate parts can have one incoming and one outgoing connection

**Duplicate Prevention:**

- Each part can have only one outgoing connection

- Each part can have only one incoming connection

- Branching and loops are prevented

### Real-time Validation

During interactive scanning:

- **Part Database Validation**: All parts validated against parts database

- **SNAP Format Validation**: SNAP parts validated against format pattern SNAP<chassis><slot><port>

- **Connection Validation**: Each connection validated against chain rules

- **Immediate Feedback**: Invalid operations rejected with clear explanations

## User Interface Safety

### Confirmation Prompts

All potentially destructive actions require explicit confirmation:

- Database clearing operations

- Bulk part deletion (if implemented)

- Configuration changes affecting data

- Irreversible migrations

### Help and Documentation

Safety through information:

- **Comprehensive Help**: Every command has detailed help (`--help`)

- **Example Usage**: Examples provided for all operations

- **Warning Messages**: Clear warnings for destructive operations

- **Error Messages**: Informative error messages with resolution guidance

### Terminal Adaptation

Safe display across environments:

- **Terminal Width Detection**: Adapts output to prevent truncation

- **Color Support Detection**: Gracefully handles terminals without color

- **Unicode Fallback**: ASCII alternatives for unicode characters

- **Screen Reader Compatibility**: Text-based warnings work with accessibility tools

## Data Protection

### Backup Strategies

When possible, CAsMan creates backups:

- **Database Backups**: Automatic backups before migrations

- **Configuration Backups**: Backup config files before changes

- **Timestamp Preservation**: Original timestamps maintained in backups

### Transaction Safety

Database operations use transactions:

- **Atomic Operations**: All-or-nothing operation completion

- **Rollback Capability**: Failed operations don't leave partial changes

- **Consistency Checks**: Post-operation validation ensures data integrity

### Input Validation

All user input is validated:

- **Part Number Format**: Validates part number patterns

- **Type Checking**: Ensures proper data types

- **Range Checking**: Validates numeric ranges

- **Sanitization**: Prevents injection attacks

## Recovery Features

### Error Recovery

When errors occur:

- **Clear Error Messages**: Detailed description of what went wrong

- **Recovery Suggestions**: Specific steps to resolve issues

- **State Preservation**: System state preserved when possible

- **Safe Exit**: Clean shutdown even after errors

### Database Recovery

For database issues:

- **Integrity Checking**: Built-in database integrity verification

- **Backup Restoration**: Guidance for restoring from backups

- **Schema Repair**: Tools for fixing schema issues

- **Migration Recovery**: Rollback capabilities for failed migrations

## Best Practices

### Recommended Workflows

Safe operation practices:

1. **Regular Backups**: Use provided backup tools regularly
2. **Test Operations**: Use `--dry-run` flags when available
3. **Read Help**: Always check `--help` for unfamiliar commands
4. **Verify Inputs**: Double-check part numbers and parameters
5. **Monitor Output**: Pay attention to warnings and confirmations

### Development Safety

For developers:

- **Test Coverage**: Comprehensive test suite for safety features

- **Code Review**: All safety-critical code requires review

- **Error Simulation**: Tests include error condition simulation

- **Documentation**: All safety features documented and tested

## Emergency Procedures

### Data Recovery

If data loss occurs:

1. **Stop Operations**: Immediately stop any ongoing operations
2. **Check Backups**: Look for automatic backups in database directory
3. **Database Restoration**: Use backup files to restore databases
4. **Validation**: Verify restored data integrity
5. **Resume Operations**: Carefully resume normal operations

### System Issues

For system-level problems:

1. **Check Logs**: Review any available log files
2. **Verify Environment**: Ensure Python environment is correct
3. **Reinstall Package**: Clean reinstall of CAsMan if needed
4. **Contact Support**: Use GitHub issues for persistent problems

## Configuration

### Safety Settings

Available safety configurations:

- **Confirmation Timeouts**: Set timeouts for confirmation prompts

- **Backup Retention**: Configure how long backups are kept

- **Validation Levels**: Adjust strictness of validation checks

- **Error Reporting**: Configure error reporting and logging

### Environment Variables

Safety-related environment variables:

- `CASMAN_SKIP_CONFIRMATIONS`: **NOT RECOMMENDED** - Skips confirmations

- `CASMAN_BACKUP_DIR`: Custom backup directory location

- `CASMAN_VALIDATION_STRICT`: Enable strict validation mode

- `CASMAN_SAFE_MODE`: Enable maximum safety checks
