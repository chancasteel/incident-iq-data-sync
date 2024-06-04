# Incident IQ Data Import

This script is designed to retrieve data from the Incident IQ API and convert it into CSV format. The script handles data for assets, tickets, and users, and has the capability to include device activities for specific asset categories.

## Prerequisites

- Python 3.x
- Required Python libraries:
  - argparse
  - config
  - datetime
  - json
  - logging
  - pandas
  - random
  - requests
  - time
  - types (SimpleNamespace)
  - tqdm

## Configuration

Ensure that the `config.py` file is correctly set up with the following variables:

- `LOG_PATH`: Path where logs will be stored
- `IIQ_TOKEN`: Incident IQ API token
- `IIQ_SITE`: Incident IQ site ID
- `IIQ_INSTANCE`: Incident IQ instance URL
- `DATA_PATH`: Path where CSV files will be saved

## Usage

Run the script from the command line. Optionally, include the `--activity` flag to retrieve device activities for certain asset categories.

```bash
python script_name.py [--activity]
```

### Arguments

- `--activity`: Retrieve device activities for specific asset categories (Tablets, Chromebooks, Laptops / Notebooks).

## Logging

Logs are stored in a file named `iiqdata_download_<YYYYMMDD>.log` within the path specified in the `config.LOG_PATH` variable.

## Script Workflow

1. **Setup Logging**: Initializes logging configuration.
2. **API Credentials and URL**: Sets up API credentials and the base URL for Incident IQ.
3. **Function Definitions**:
   - `parse_fields(response)`: Parses custom fields from the API response.
   - `get_custom_fields(item, custom_fields)`: Retrieves custom fields for a given item.
   - `pull_data(endpoint, method='GET', data=None)`: Generic function to pull data from the API.
   - `get_device_activity(item, category)`: Retrieves device activity for a given item and category.
   - `asset_sync()`: Retrieves assets data and converts it to a CSV file.
   - `ticket_sync()`: Retrieves tickets data and converts it to a CSV file.
   - `user_sync()`: Retrieves users data and converts it to a CSV file.

4. **Main Execution**:
   - Parses command line arguments.
   - Executes data sync for tickets, assets, and users.
   - Logs the execution time for each sync process and the total execution time.

## Data Fields

### Assets

- AssetId, CreatedDate, DeployedDate, AssetTypeName, IsDeleted, Status, AssetTag, SerialNumber, Name, Category, Location, LocationRoom, Notes, HasOpenTickets, OpenTickets, FundingSource, LastVerificationSuccessful, ExternalId, PurchasePrice, PurchasePoNumber, LastInventoryDate, Vendor, DeviceActivity, MicrosoftIntuneData, ComplianceState, LastContactDateTime, MDMOSVersion, GoogleDeviceData, LastLoginDate, LastSyncDate, RecentUserEmail, GoogleDeviceStatus, ChromebookOSVersion, PaymentsStripe, Balance, LastActivityDate, PastDueAmount, OldestPastDueBalance, FileWaveData, LastCheck-InDate, LastLoggedInUser, SparePool, GroupName, PoolName

### Tickets

- TicketId, TicketNumber, CreatedDate, StartedDate, ClosedDate, OwnerId, OwnerName, ForId, ForName, IssueId, IsIssueConfirmed, IsDeleted, AssignedToUserId, AssignedToUsername, IsClosed, WorkflowStepId, Status, LocationId, LocationName, ModifiedDate, Priority, IssueName, Subject, Assets, IssueDescription, TeamId, TeamName, PaymentsStripe, Balance, LastActivityDate, PastDueAmount, OldestPastDueBalance

### Users

- UserId, IsDeleted, CreatedDate, ModifiedDate, LocationId, LocationName, IsActive, IsOnline, IsOnlineLastUpdated, FirstName, LastName, Email, Username, Phone, SchoolIdNumber, Grade, ExternalId, InternalComments, RoleId, RoleName, AuthenticatedBy, AccountSetupProgress, IsEmailVerified, IsWelcomeEmailSent, PreventProviderUpdates, IsOutOfOffice, Portal, Balance, LastActivityDate, PastDueAmount, OldestPastDueBalance, ClassLinkSsoData

## License

This project is licensed under the MIT License.

---

Ensure that you handle the API credentials securely and do not expose them in your source code or logs.
