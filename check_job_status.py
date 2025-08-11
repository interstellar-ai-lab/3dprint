#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to check the status of a Tencent Cloud AI3D job
"""

import os
import json
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.ai3d.v20250513 import ai3d_client, models

from dotenv import load_dotenv
load_dotenv('.env')

def check_job_status(job_id):
    """
    Check the status of a specific job
    """
    try:
        TENCENTCLOUD_SECRET_ID = os.getenv("TENCENTCLOUD_SECRET_ID")
        TENCENTCLOUD_SECRET_KEY = os.getenv("TENCENTCLOUD_SECRET_KEY")
        TENCENTCLOUD_REGION = "ap-guangzhou"
        TENCENTCLOUD_ENDPOINT = "ai3d.tencentcloudapi.com"
        
        if not TENCENTCLOUD_SECRET_ID or not TENCENTCLOUD_SECRET_KEY:
            print("Error: TENCENTCLOUD_SECRET_ID and TENCENTCLOUD_SECRET_KEY must be set as environment variables")
            return None
        cred = credential.Credential(TENCENTCLOUD_SECRET_ID, TENCENTCLOUD_SECRET_KEY)
        
        httpProfile = HttpProfile()
        httpProfile.endpoint = TENCENTCLOUD_ENDPOINT

        clientProfile = ClientProfile()
        clientProfile.httpProfile = httpProfile
        
        client = ai3d_client.Ai3dClient(cred, TENCENTCLOUD_REGION, clientProfile)

        # Create request to query job status
        req = models.QueryHunyuanTo3DJobRequest()
        params = {
            "JobId": job_id
        }
        req.from_json_string(json.dumps(params))

        resp = client.QueryHunyuanTo3DJob(req)
        
        print(f"Job Status for {job_id}:")
        print(resp.to_json_string())
        
        return resp

    except TencentCloudSDKException as err:
        print(f"Tencent Cloud SDK Exception: {err}")
        return None
    except Exception as e:
        print(f"General Exception: {e}")
        return None

def main():
    # Load environment variables from env.local and .env
    
    print("Checking Tencent Cloud AI3D Job Status...")
    print("=" * 50)
    
    # Job IDs from our previous tests
    job_ids = [
        "1346037372240101376",
        "1345964238652669952", # dog
        "1345307282845777920",  # From first test
        "1345308348844916736",  # From second test
    ]
    
    for job_id in job_ids:
        print(f"\nChecking job: {job_id}")
        print("-" * 30)
        result = check_job_status(job_id)
        
        if result:
            # Parse the response to show key information
            try:
                response_data = json.loads(result.to_json_string())
                if 'Response' in response_data:
                    job_info = response_data['Response']
                    print(f"Status: {job_info.get('Status', 'Unknown')}")
                    print(f"Progress: {job_info.get('Progress', 'Unknown')}")
                    if 'ResultUrl' in job_info:
                        print(f"Result URL: {job_info['ResultUrl']}")
                    if 'ErrorMsg' in job_info:
                        print(f"Error: {job_info['ErrorMsg']}")
            except json.JSONDecodeError:
                print("Could not parse response JSON")
        
        print()

if __name__ == "__main__":
    main()
