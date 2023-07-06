# Schedule Schematics refreshes using Code Engine

The `rollingIaaS.py` Python file is used to automate refreshing schematics workspaces. It is designed to be run as a Code Engine job.

## Prerequisites

The following environment variables will be needed when configuring the Code Engine Job:

- `IBMCLOUD_API_KEY`: IBM Cloud API key used to initiate the IAM authenticator.
- `WORKSPACE_ID`: The ID of the Schematics workspace where the server is deployed.
- `LOGDNA_INGESTION_KEY`: The LogDNA ingestion key for logging.

> **Optional**: If you would like to deploy resources via the CLI, please ensure you have the code engine plugin installed. `ibmcloud plugin install code-engine`

## Steps

### Step 1: Create a new Code Engine project

#### Create project from the portal

1. Navigate to the [Code Engine UI](https://cloud.ibm.com/codeengine/overview).
2. Click the `Create project` button, give the project a name, select your resource group, and click `Create`.

![Create Code Engine UI](https://dsc.cloud/quickshare/Shared-Image-2023-07-06-07-30-53.png)

#### Create project from the CLI

Before you can create a Code Engine project, you must first target a resource group.

```sh
ibmcloud target -g <resource-group>
```

Then, create the project. I highly recommend adding tags to your resources whenever possible for easier management, searching, and billing.

```sh
ibmcloud ce project create --name <project-name> --tag <project-tag>
```

**Example Output**

```sh
ibmcloud ce project create --name rolling-schematics-ce --tag "owner:ryantiffany"
Creating project 'rolling-schematics-ce'...
ID for project 'rolling-schematics-ce' is 'xxxxxx-c92e-xxxx-936b-xxxxx'.
Waiting for project 'rolling-schematics-ce' to be active...
```

The process will take a few moments to complete. Once it is finished, the CLI will automatically target the project, so it will be ready for the next step.

### Step 2: Create a Code Engine build using this repository as the source

The next steo is to set up a Code Engine build to pull this repository and build the container image. The container image will then be stored in the IBM Cloud Container Registry.

#### Create container build from the Portal

From the left hand Code Engine menu, click on `Image builds` and then click the `Create build` button.

![Click on Image Build](https://dsc.cloud/quickshare/Shared-Image-2023-07-06-07-45-03.png)


#### Create container build from the CLI

```sh
```

### Step 3: Create a Code Engine job using the build created in the previous step.

### Step 4: Configure the job with the environment variables listed above.

### Step 5: Create schedules for the job to run at the desired intervals.

