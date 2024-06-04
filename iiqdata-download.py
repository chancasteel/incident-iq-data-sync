import argparse
import config
from datetime import timedelta
import json
import logging
import pandas as pd
import random
import requests
import time
from types import SimpleNamespace as Namespace
from tqdm import tqdm

# Setup logging
timestr = time.strftime("%Y%m%d")
log_filename = f"{config.LOG_PATH}/iiqdata_download_{timestr}.log"
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filename=log_filename, filemode='a')
logger = logging.getLogger(__name__)

# API credentials and URL
url = "https://duncanvilleisd.incidentiq.com"
authkey = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJjNzdhNjg2My1jMTNkLTRmMzktYTk5NS01ZmUzN2FjM2Y5MTAiLCJzY29wZSI6Imh0dHBzOi8vZHVuY2FudmlsbGVpc2QuaW5jaWRlbnRpcS5jb20iLCJzdWIiOiJhYmUzMWQ3Ny1lMDVhLTQyYjctYmNlNC02NGUwY2M3ODAxOTMiLCJqdGkiOiIxNjQ3ZmE0NS1kZWQ2LWVjMTEtYjY1Ni0wMDE1NWQ5ODAzZjEiLCJpYXQiOjE2NTI5MDEwNzQuMjMzLCJleHAiOjE3NDc1OTU0NzQuMjR9.AUpuzI82trLWMDVUbg4PlGn3gyDwYNPevdzYSlh3iWE"
site_id = "c77a6863-c13d-4f39-a995-5fe37ac3f910"

headers = {
    "Authorization": f"Bearer {config.IIQ_TOKEN}",
    "SiteId": config.IIQ_SITE,
    "Client": "ApiClient"
}

def parse_fields(response : requests.Response):
    """
    Parse custom fields from the API response.

    :param response: API response object
    :return: Dictionary of custom field IDs and names
    """
    logger.info("Parsing custom fields")
    all_fields = {}
    for item in response.json()['Items']:
        name = item['CustomFieldType']['Name'].replace(" ","")
        all_fields[item['CustomFieldTypeId']] = name
    return all_fields

def get_custom_fields(item, custom_fields):
    """
    Retrieve custom fields for a given item.

    :param item: Item with custom field values
    :param custom_fields: Dictionary of custom field IDs and names
    :return: Dictionary of custom field names and values
    """
    attributes = {}
    if hasattr(item, 'CustomFieldValues'):
        for field in item.CustomFieldValues:
            if field.CustomFieldTypeId in custom_fields:
                attributes[custom_fields[field.CustomFieldTypeId]] = field.Value
    return attributes

def pull_data(endpoint, method='GET', data=None):
    """
    Generic function to pull data from the API.
    
    * param endpoint: API endpoint to hit.
    * param method: HTTP method to use ('GET' or 'POST').
    * param data: Data to send in a POST request.
    * return: JSON response or None if the request failed.
    """
    logger.info(f"Pulling data from {endpoint} with method {method}")
    if method == 'GET':
        response = requests.get(url=f"{config.IIQ_INSTANCE}{endpoint}", headers=headers)
    else:
        response = requests.post(url=f"{config.IIQ_INSTANCE}{endpoint}", headers=headers, json=data)
    if not response.ok:
        logger.error(f"Request to {endpoint} failed with status code {response.status_code}")
        return None
    return response

device_activity_type = {0 : "Other", 1 : "Created", 2 : "Viewed", 3 : "Updated", 4 : "Deleted", 5 : "TicketCreated", 6 : "Comment", 7 : "RuleExecuted", 8 : "ResolutionAction",
                        9 : "TicketCanceled", 10 : "TicketResolved", 20 : "Email", 30 : "AssetAudited", 31 : "AttachmentAdded", 40 : "SpareIssued", 41 : "SpareReturned", 
                        50 : "OutsideRepairRequested", 51 : "OutsideRepairCompleted", 52 : "OutsideRepairApproved", 53 : "OutsideRepairDeclined", 54 : "OutsideRepairReturned",
                        55 : "OutsideRepairStatusChanged", 56 : "OutsideRepairCanceled", 57 : "Part", 58 : "DuplicateTicket", 59 : "AwaitingApproval", 60 : "Deferred", 
                        61 : "Approved", 62 : "Denied", 63 : "StatusChange", 70 : "FollowerAdded", 71 : "FollowerRemoved", 72 : "TagAdded", 73 : "TagRemoved", 
                        74 : "WebHookCalled", 75 : "AssetAuditPolicyEvent", 76 : "AssetVerified", 77 : "TicketSlaMetricUpdated"
}

def get_device_activity(item, category):
    """
    Retrieve device activity for a given item and category.

    :param item: Item to retrieve activity for
    :param category: Category of the item
    :return: String representation of the activity or an empty string if not applicable
    """
    if category in {'Tablets', 'Chromebooks', 'Laptops / Notebooks'}:
        try:
            response = pull_data(f'/api/v1.0/assets/{item.AssetId}/activities/')
            time.sleep(random.uniform(0,1))
            if response.ok and response.content:
                data = response.json()
                activities = [
                    {**activity, 'ActivityType': device_activity_type[activity['ActivityType']]}
                    for activity in data.get('Items', [])
                    if activity['ActivityType'] != 2
                ]
                return ' '.join([str(x).replace(r"\r\n", "") for x in activities])
        except requests.RequestException as e:
            logger.error(f"API Request failed: {e}")
        except KeyError as e:
            logger.error(f"Key Error failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
    return None

asset_fields = [
    'AssetId', 'CreatedDate', 'DeployedDate', 'AssetTypeName',
    'IsDeleted', 'Status', 'AssetTag', 'SerialNumber', 'Name', 'Category', 'Location',
    'LocationRoom', 'Notes', 'HasOpenTickets', 'OpenTickets',
    'FundingSource', 'LastVerificationSuccessful', 'ExternalId',
    'PurchasePrice', 'PurchasePoNumber', 'LastInventoryDate', 'Vendor', 'DeviceActivity', 
    'MicrosoftIntuneData', 'ComplianceState', 'LastContactDateTime', 'MDMOSVersion',
    'GoogleDeviceData', 'LastLoginDate', 'LastSyncDate', 'RecentUserEmail', 'GoogleDeviceStatus', 'ChromebookOSVersion',
    'PaymentsStripe', 'Balance', 'LastActivityDate', 'PastDueAmount', 'OldestPastDueBalance',
    'FileWaveData', 'LastCheck-InDate', 'LastLoggedInUser',
    'SparePool', 'GroupName', 'PoolName'
]

def asset_sync():
    """
    Main function to retrieve assets and covert to CSV.
    """
    logger.info("Starting asset sync")
    asset_response = pull_data('/api/v1.0/assets/?$s=999999&$o=AssetTag&$d=Ascending','POST', json.dumps({
                    "SiteScope": "Aggregate",
                    "Strategy": "AggregateAsset",
                    "Filters": [{
                        "Facet": "Status",
                        "Value": "Available" 
                    }]
                }))
    cf_response = pull_data('/api/v1.0/custom-fields?$p=0/&$s=999999&$o=AssetTag&$d=Ascending', 'POST', json.dumps({
                    "SiteScope": "Aggregate",
                    "Strategy": "AggregateAsset"
                }))
    custom_fields = parse_fields(cf_response)
    
    asset_types = asset_response.json(object_hook=lambda d:Namespace(**d)).Items
    iiq_classes = []

    for item in tqdm(asset_types):
        customs = get_custom_fields(item, custom_fields)
        asset_info = {
            'AssetId': getattr(item, 'AssetId', None),
            'CreatedDate': getattr(item, 'CreatedDate', None),
            'DeployedDate': getattr(item, 'DeployedDate', None),
            'AssetTypeName': getattr(item, 'AssetTypeName', None),
            'IsDeleted': getattr(item, 'IsDeleted', None),
            'Status': getattr(item.Status, 'Name', None),
            'AssetTag': getattr(item, 'AssetTag', None),
            'SerialNumber': getattr(item, 'SerialNumber', None),
            'Name': getattr(item, 'Name', None),
            'Category': getattr(item.Model.Category, 'Name', None) if hasattr(item, 'Model') else None,
            'Location': getattr(item.Location, 'Name', None) if hasattr(item, 'Location') else None,
            'LocationRoom': getattr(item.LocationRoom, 'Name', None) if hasattr(item, 'LocationRoom') else None,
            'Notes': getattr(item, 'Notes', None),
            'HasOpenTickets': getattr(item, 'HasOpenTickets', None),
            'OpenTickets': getattr(item, 'OpenTickets', None),
            'FundingSource': getattr(item.FundingSource, 'Name', None) if hasattr(item, 'FundingSource') else None,
            'LastVerificationSuccessful': getattr(item, 'LastVerificationSuccessful', None),
            'ExternalId': getattr(item, 'ExternalId', None),
            'DataMappings': getattr(item, 'DataMappings', None),
            'PurchasePrice': getattr(item, 'PurchasePrice', None),
            'PurchasePoNumber': getattr(item, 'PurchasePoNumber', None),
            'LastInventoryDate': getattr(item, 'LastInventoryDate', None),
            'Vendor': getattr(item, 'Vendor', None),
            'DeviceActivity': get_device_activity(item, getattr(item.Model.Category, 'Name', None)) if main_args.device_activity else None,
        }
        
        custom_data_mappings = {
            'MicrosoftIntuneData': ['ComplianceState', 'LastContactDateTime', 'MDMOSVersion'],
            'GoogleDeviceData': ['LastLoginDate', 'LastSyncDate', 'RecentUserEmail', 'GoogleDeviceStatus', 'ChromebookOSVersion'],
            'PaymentsStripe': ['Balance', 'LastActivityDate', 'PastDueAmount', 'OldestPastDueBalance'],
            'FileWaveData': ['LastCheck-InDate', 'LastLoggedInUser'],
            'SparePool': ['GroupName', 'PoolName']
        }

        for key, fields in custom_data_mappings.items():
            if key in customs:
                data = json.loads(customs[key])[0]
                for field in fields:
                    customs[field] = data.get(field, None)
        
        asset_info.update(customs)
        iiq_classes.append(asset_info)

    asset_df = pd.DataFrame(iiq_classes, columns= asset_fields)
    logger.info("Asset data frame info")
    asset_df.info()
    asset_df.to_csv(f'{config.DATA_PATH}/assets.csv', index=False)
    logger.info("Asset sync completed")

ticket_fields = [
    'TicketId', 'TicketNumber', 'CreatedDate', 'StartedDate', 'ClosedDate',
    'OwnerId', 'OwnerName', 'ForId', 'ForName','IssueId', 'IsIssueConfirmed',
    'IsDeleted', 'AssignedToUserId', 'AssignedToUsername', 'IsClosed', 'WorkflowStepId', 'Status',
    'LocationId', 'LocationName', 'ModifiedDate', 'Priority', 'IssueName',
    'Subject', 'Assets', 'IssueDescription', 'TeamId', 'TeamName', 'PaymentsStripe',
    'Balance', 'LastActivityDate', 'PastDueAmount', 'OldestPastDueBalance'
]

def ticket_sync():
    """
    Main function to retrieve tickets and convert them to CSV.
    """
    logger.info("Starting ticket sync")
    ticket_response = pull_data('/api/v1.0/tickets/?$s=999999&$d=Descending&$o=TicketCreatedDate','POST',data={
        "OnlyShowDeleted": False,
        "FilterByViewPermission": True
    })
    cf_response = pull_data('/api/v1.0/custom-fields?$p=0/&$s=999999', 'POST', json.dumps({
                    "SiteScope": "Aggregate",
                    "Strategy": "AggregateTicket"
            }))
    custom_fields = parse_fields(cf_response)
    
    ticket_types = ticket_response.json(object_hook=lambda d:Namespace(**d)).Items
    iiq_classes = []

    for item in tqdm(ticket_types):
        customs = get_custom_fields(item, custom_fields)
        ticket_info = {
            'TicketId': getattr(item, 'TicketId', None),
            'TicketNumber': getattr(item, 'TicketNumber', None),
            'CreatedDate': getattr(item, 'CreatedDate', None),
            'StartedDate': getattr(item, 'StartedDate', None),
            'ClosedDate': getattr(item, 'ClosedDate', None),
            'OwnerId': getattr(item, 'OwnerId', None),
            'OwnerName': getattr(item.Owner, 'Name', None) if hasattr(item, 'Owner') else None, 
            'ForId': getattr(item, 'ForId', None),
            'ForName': getattr(item.For, 'Name', None) if hasattr(item, 'For') else None, 
            'IssueId': getattr(item, 'IssueId', None),
            'IsIssueConfirmed': getattr(item, 'IsIssueConfirmed', None),
            'IsDeleted': getattr(item, 'IsDeleted', None),
            'AssignedToUserId': getattr(item, 'AssignedToUserId', None),
            'IsClosed': getattr(item, 'IsClosed', None),
            'WorkflowStepId': getattr(item, 'WorkflowStepId', None),
            'LocationId': getattr(item, 'LocationId', None),
            'LocationName': getattr(item.Location, 'Name', None),
            'ModifiedDate': getattr(item, 'ModifiedDate', None),
            'Priority': getattr(item, 'Priority', None),
            'Subject': getattr(item, 'Subject', None),
            'IssueName': getattr(item.Issue, 'Name', None) if hasattr(item, 'Issue') else None,
            'IssueDescription': getattr(item, 'IssueDescription', None),
            'Status': getattr(item.WorkflowStep, 'StatusName', None),
            'Assets': getattr(item.Assets[0], 'AssetId', None) if hasattr(item, 'Assets') else None,
            'AssignedToUsername': getattr(item.AssignedToUser, 'Name') if hasattr(item, 'AssignedToUser') else None,
            'TeamId': getattr(item.AssignedToTeam, 'TeamId', None) if hasattr(item, 'AssignedToTeam') else None,
            'TeamName': getattr(item.AssignedToTeam, 'TeamName', None) if hasattr(item, 'AssignedToTeam') else None
        }

        custom_data_mappings = {
            'PaymentsStripe': ['Balance', 'LastActivityDate', 'PastDueAmount', 'OldestPastDueBalance']
        }
                
        for key, fields in custom_data_mappings.items():
            if key in customs:
                data = json.loads(customs[key])[0]
                for field in fields:
                    customs[field] = data.get(field, None)

        ticket_info.update(customs)
        iiq_classes.append(ticket_info)

    ticket_df = pd.DataFrame(iiq_classes, columns= ticket_fields)
    logger.info("Ticket data frame info")
    ticket_df.info()
    ticket_df.to_csv(f'{config.DATA_PATH}/tickets.csv', index=False)
    logger.info("Ticket sync completed")

user_fields = [
    'UserId','IsDeleted',  'CreatedDate',  'ModifiedDate',
    'LocationId', 'LocationName', 'IsActive', 'IsOnline', 'IsOnlineLastUpdated',
    'FirstName', 'LastName', 'Email', 'Username',  'Phone', 'SchoolIdNumber',
    'Grade', 'ExternalId', 'InternalComments',  'RoleId', 'RoleName', 
    'AuthenticatedBy', 'AccountSetupProgress', 'IsEmailVerified',
    'IsWelcomeEmailSent', 'PreventProviderUpdates', 'IsOutOfOffice', 'Portal',
    'Balance', 'LastActivityDate', 'PastDueAmount', 'OldestPastDueBalance', 'ClassLinkSsoData'
]


def user_sync():
    """
    Main function to retrieve tickets and convert them to CSV.
    """
    logger.info("Starting user sync")
    ticket_response = pull_data('/api/v1.0/users/?$o=UserId&$s=999999&$d=Ascending','POST',data={
        "OnlyShowDeleted": False,
        "FilterByViewPermission": True
    })
    cf_response = pull_data('/api/v1.0/custom-fields?$p=0/&$s=999999', 'POST', json.dumps({
                    "SiteScope": "Aggregate",
                    "Strategy": "AggregateUser"
            }))
    custom_fields = parse_fields(cf_response)
    
    user_types = ticket_response.json(object_hook=lambda d:Namespace(**d)).Items
    iiq_classes = []

    for item in tqdm(user_types):
        customs = get_custom_fields(item, custom_fields)
        user_info = {
            'UserId': getattr(item, 'UserId', None),
            'IsDeleted': getattr(item, 'IsDeleted', None),
            'CreatedDate': getattr(item, 'CreatedDate', None),
            'ModifiedDate': getattr(item, 'ModifiedDate', None),
            'LocationId': getattr(item, 'LocationId', None),
            'LocationName': getattr(item.Location, 'Name', None),
            'IsActive': getattr(item, 'IsActive', None),
            'IsOnline': getattr(item, 'IsOnline', None),
            'IsOnlineLastUpdated': getattr(item, 'IsOnlineLastUpdated', None),
            'FirstName': getattr(item, 'FirstName', None),
            'LastName': getattr(item, 'LastName', None),
            'Email': getattr(item, 'Email', None),
            'Username': getattr(item, 'Username', None),
            'Phone': getattr(item, 'Phone', None),
            'SchoolIdNumber': getattr(item, 'SchoolIdNumber', None),
            'Grade': getattr(item, 'Grade', None),
            'Homeroom': getattr(item, 'Homeroom', None),
            'ExternalId': getattr(item, 'ExternalId', None),
            'InternalComments': getattr(item, 'InternalComments', None),
            'RoleId': getattr(item, 'RoleId', None),
            'RoleName': getattr(item.Role, 'Name', None),
            'AuthenticatedBy': getattr(item, 'AuthenticatedBy', None),
            'AccountSetupProgress': getattr(item, 'AccountSetupProgress', None),
            'TrainingPercentComplete': getattr(item, 'TrainingPercentComplete', None),
            'IsEmailVerified': getattr(item, 'IsEmailVerified', None),
            'IsWelcomeEmailSent': getattr(item, 'IsWelcomeEmailSent', None),
            'PreventProviderUpdates': getattr(item, 'PreventProviderUpdates', None),
            'IsOutOfOffice': getattr(item, 'IsOutOfOffice', None),
            'Portal': getattr(item, 'Portal', None)
        }

        custom_data_mappings = {
            'PaymentsStripe': ['Balance', 'LastActivityDate', 'PastDueAmount', 'OldestPastDueBalance']
        }

        for key, fields in custom_data_mappings.items():
            if key in customs:
                data = json.loads(customs[key])[0]
                for field in fields:
                    customs[field] = data.get(field, None)

        user_info.update(customs)
        iiq_classes.append(user_info)

    user_df = pd.DataFrame(iiq_classes, columns= user_fields)
    logger.info("User data frame info")
    user_df.info()
    user_df.to_csv(f'{config.DATA_PATH}/users.csv', index=False)
    logger.info("User sync completed")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="Incident IQ Data Import")
    parser.add_argument('--activity', action='store_true', help="Retrieve Device Activities", dest='device_activity')
    main_args = parser.parse_args()

    start_time = time.time()

    ticket_sync()
    ticket_stop_time = time.time()
    logger.info(f"Ticket Execution took --- {timedelta(seconds=(ticket_stop_time-start_time))} ---", )

    asset_sync()
    asset_stop_time = time.time()
    logger.info(f"Asset Execution took --- {timedelta(seconds=(asset_stop_time-ticket_stop_time))} ---", )

    user_sync()
    stop_time = time.time()
    logger.info(f"User Execution took --- {timedelta(seconds=(stop_time-asset_stop_time))} ---", )

    logger.info(f"Total Execution took --- {timedelta(seconds=(stop_time-start_time))} ---", )