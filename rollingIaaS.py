import os
import sys
import time
from logdna import LogDNAHandler
import logging
from ibm_cloud_sdk_core import ApiException
from ibm_schematics.schematics_v1 import SchematicsV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

ibmApiKey = os.environ.get('IBMCLOUD_API_KEY')
if not ibmApiKey:
    raise ValueError("IBMCLOUD_API_KEY environment variable not found")


workspaceId = os.environ.get('WORKSPACE_ID')
if not workspaceId:
    raise ValueError("WORKSPACE_ID environment variable not found")


authenticator = IAMAuthenticator(
    apikey=ibmApiKey,
    client_id='bx',
    client_secret='bx'  # pragma: allowlist secret
)

refreshToken = authenticator.token_manager.request_token()['refresh_token']


def logDnaLogger():
    key = os.environ.get('LOGDNA_INGESTION_KEY')
    log = logging.getLogger('logdna')
    log.setLevel(logging.INFO)

    options = {
        'index_meta': True,
        'url': 'https://logs.private.us-south.logging.cloud.ibm.com/logs/ingest',
        'log_error_response': True,
        'app': 'schematics-refresh'
    }

    logger = LogDNAHandler(key, options)
    log.addHandler(logger)
    return log


def schematicsClient():
    client = SchematicsV1(authenticator=authenticator)
    schematicsURL = 'https://private-us-south.schematics.cloud.ibm.com'
    client.set_service_url(schematicsURL)
    return client

def getWorkspaceStatus():
    log = logDnaLogger()
    schematics = schematicsClient()
    try:
        workspace = schematics.get_workspace(w_id=workspaceId).get_result()
        status = workspace['status']
        return str(status)
    except ApiException as e:
        log.error(f"Error getting workspace status: {e}")
        sys.exit(1)


def destroyWorkspaceResources():
    log = logDnaLogger()
    schematics = schematicsClient()
    try:
        wsDestroy = schematics.destroy_workspace_command(
            w_id=workspaceId,
            refresh_token=refreshToken
        ).get_result()

        destroyActivityId = wsDestroy.get('activityid')
        log.info("Destroying workspace resources")
        while True:
            time.sleep(5)
            status = getWorkspaceStatus()
            if status == "INACTIVE":
                log.info("Resources destroyed successfully.")
                time.sleep(60)
                break
            elif status in ["FAILED", "CANCELLED"]:
                log.error(f"Destroy operation {status}")
                log.error(f"Destroy activity ID: {destroyActivityId}")
                break
            else:
                log.info("Waiting for workspace resources to be destroyed") 
                log.info("Next status check in 1 minute ..")
                log.info(f"Current workspace status: {status}")
                time.sleep(60)
    except ApiException as e:
        log.error(f"Error destroying resources: {e}")
        sys.exit(1)


def applyWorkspaceResources():
    log = logDnaLogger()
    schematics = schematicsClient()
    try:
        wsApply = schematics.apply_workspace_command(
            w_id=workspaceId,
            refresh_token=refreshToken
        ).get_result()

        applyActivityId = wsApply.get('activityid')
        log.info("Provisioning workspace resources")
        while True:
            time.sleep(5)
            status = getWorkspaceStatus()
            if status == "ACTIVE":
                log.info("Resources provisioned successfully.")
                break
            elif status in ["FAILED", "CANCELLED"]:
                log.error(f"Apply operation {status}")
                log.error(f"Apply activity ID: {applyActivityId}")
                break
            else:
                log.info("Waiting for resources to be provisioned. Next status check in 10 minutes...")
                log.info(f"Current workspace status: {status}")
                time.sleep(600)
    except ApiException as e:
        log.error(f"Error applying resources: {e}")
        sys.exit(1)


def main():
    log = logDnaLogger()
    status = getWorkspaceStatus()
    log.info(f"Starting hardware refresh. Current workspace status: {status}")
    if status == "INACTIVE":
        applyWorkspaceResources()
    elif status == "ACTIVE":
        destroyWorkspaceResources()
        applyWorkspaceResources()
    elif status == "FAILED":
        attempts = 0
        while attempts < 3 and status == "FAILED":
            log.info("Workspace is marked as Failed.")
            log.info("Automated recorvery attempt: " + str(attempts + 1) + "/3")
            destroyWorkspaceResources()
            applyWorkspaceResources()
            status = getWorkspaceStatus()
            attempts += 1     
        if status == "FAILED":
            log.error(f"Workspace is marked as: {status} for the 3rd time. Exiting.")
            exit(1)  
    else:
        log.info("Workspace is currently not in a valid state to run destroy/apply actions")
        log.info(f"Current workspace status: {status}")
        log.info("Polling again in 60 seconds.")
        time.sleep(60)


if __name__ == "__main__":
    main()
