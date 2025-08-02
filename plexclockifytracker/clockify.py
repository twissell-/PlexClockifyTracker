from datetime import datetime, timezone

import requests

from plexclockifytracker.config import Config


class Clockify:
    """
    Clockify API client for PlexClockifyTracker
    Handles interactions with the Clockify API for time tracking
    """

    BASE_URL = "https://api.clockify.me/api/v1"

    def __init__(self):
        self._app_name = "PlexClockifyTracker_webhook"
        self._workspace = None
        self._headers = {"content-type": "application/json", "X-Api-Key": ""}

        if not Config.get("clockify_api_key"):
            raise ValueError("clockify_api_key is not configured.")

        self._api_key = Config.get("clockify_api_key")
        self._headers["X-Api-Key"] = self._api_key

    def _request(self, endpoint, params=None, method="GET", body=None):
        """
        Make a request to the Clockify API

        Args:
            endpoint: API endpoint to call
            params: URL parameters
            method: HTTP method (GET, POST, PATCH, PUT, DELETE)
            body: Request body for POST/PUT/PATCH requests

        Returns:
            Response from the API
        """
        url = Clockify.BASE_URL + endpoint
        params = params or {}
        body = body or {}

        if method == "POST":
            rtn = requests.post(
                url,
                headers=self._headers,
                json=body,
                params=params,
            )
        elif method == "GET":
            rtn = requests.get(url, headers=self._headers, params=params)
        elif method == "PATCH":
            rtn = requests.patch(url, headers=self._headers, json=body, params=params)
        elif method == "PUT":
            rtn = requests.put(url, headers=self._headers, json=body, params=params)
        elif method == "DELETE":
            rtn = requests.delete(url, headers=self._headers, params=params)

        if rtn.status_code < 200 or rtn.status_code >= 300:
            raise Exception(
                "Clockify response was: [{status}] {text}".format(
                    status=rtn.status_code, text=rtn.text
                )
            )

        return rtn

    def get_workspace(self):
        """
        Get the user's workspace

        Returns:
            The first workspace found for the user
        """
        if not self._workspace:
            self._workspace = self._request("/workspaces").json()[0]

        return self._workspace

    def get_projects(self, name: str = ""):
        """
        Get projects from the workspace

        Args:
            name: Filter by project name

        Returns:
            List of projects or a single project if name is provided
        """
        workspace_id = self.get_workspace()["id"]
        endpoint = "/workspaces/{workspace_id}/projects".format(
            workspace_id=workspace_id
        )

        projects = self._request(endpoint).json()

        if name:
            project = list(filter(lambda x: x["name"] == name, projects))
            return project[0] if project else []
        else:
            return projects

    def get_running_timer(self):
        """
        Get the currently running time entry

        Returns:
            The running time entry or None if no timer is running
        """
        workspace_id = self.get_workspace()["id"]
        user_id = self._request("/user").json()["id"]

        endpoint = "/workspaces/{workspace_id}/user/{user_id}/time-entries".format(
            workspace_id=workspace_id, user_id=user_id
        )

        # Get the most recent time entry
        params = {"hydrated": "true", "page-size": 1}

        time_entries = self._request(endpoint, params=params).json()

        # Check if there's a running time entry (timeInterval.end is null)
        if (
            time_entries
            and "timeInterval" in time_entries[0]
            and time_entries[0]["timeInterval"].get("end") is None
        ):
            return time_entries[0]

        return None

    def stop_timer(self):
        """
        Stop the currently running timer

        Returns:
            The stopped time entry
        """
        timer = self.get_running_timer()

        if not timer:
            return None

        workspace_id = self.get_workspace()["id"]
        user_id = self._request("/user").json()["id"]

        endpoint = "/workspaces/{workspace_id}/user/{user_id}/time-entries".format(
            workspace_id=workspace_id, user_id=user_id
        )

        # Clockify requires a PATCH request with the current datetime to stop a timer
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        return self._request(endpoint, method="PATCH", body={"end": now}).json()

    def start_timer(self, description: str, project_id: str):
        """
        Start a new timer

        Args:
            description: Description for the time entry
            project_id: ID of the project to associate with the time entry

        Returns:
            The created time entry
        """
        # First, ensure any running timer is stopped
        running_timer = self.get_running_timer()
        if running_timer:
            self.stop_timer()

        workspace_id = self.get_workspace()["id"]
        user_id = self._request("/user").json()["id"]

        endpoint = "/workspaces/{workspace_id}/time-entries".format(
            workspace_id=workspace_id
        )

        # Get the start time in the correct format
        start = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        body = {
            "start": start,
            "description": description,
            "projectId": project_id,
            "billable": "false",
        }

        return self._request(endpoint, method="POST", body=body).json()
