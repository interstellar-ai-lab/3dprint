# -*- coding: utf-8 -*-

import os
import json
import types
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.ai3d.v20250513 import ai3d_client, models

# Import configuration
try:
    from tencent_config import (
        TENCENTCLOUD_SECRET_ID, 
        TENCENTCLOUD_SECRET_KEY, 
        TENCENTCLOUD_REGION, 
        TENCENTCLOUD_ENDPOINT,
        TEST_IMAGE_URL,
        TEST_PROMPT
    )
except ImportError:
    print("Warning: tencent_config.py not found, using environment variables only")
    TENCENTCLOUD_SECRET_ID = None
    TENCENTCLOUD_SECRET_KEY = None
    TENCENTCLOUD_REGION = "ap-guangzhou"
    TENCENTCLOUD_ENDPOINT = "ai3d.tencentcloudapi.com"
    TEST_IMAGE_URL = "https://i.postimg.cc/hj8HRmFk/1.jpg"
    TEST_PROMPT = "一只可爱的小猫"

def test_tencent_ai3d_api():
    """
    Test function for Tencent Cloud AI3D API
    """
    try:
        # Get credentials from environment variables or config file
        secret_id = os.getenv("TENCENTCLOUD_SECRET_ID")
        secret_key = os.getenv("TENCENTCLOUD_SECRET_KEY")
        
        if not secret_id or not secret_key:
            print("Error: TENCENTCLOUD_SECRET_ID and TENCENTCLOUD_SECRET_KEY must be set as environment variables or in tencent_config.py")
            return None
        
        # 实例化一个认证对象，入参需要传入腾讯云账户 SecretId 和 SecretKey，此处还需注意密钥对的保密
        # 代码泄露可能会导致 SecretId 和 SecretKey 泄露，并威胁账号下所有资源的安全性
        # 以下代码示例仅供参考，建议采用更安全的方式来使用密钥
        # 请参见：https://cloud.tencent.com/document/product/1278/85305
        # 密钥可前往官网控制台 https://console.cloud.tencent.com/cam/capi 进行获取
        cred = credential.Credential(secret_id, secret_key)
        
        # 使用临时密钥示例
        # cred = credential.Credential("SecretId", "SecretKey", "Token")
        
        # 实例化一个http选项，可选的，没有特殊需求可以跳过
        httpProfile = HttpProfile()
        httpProfile.endpoint = TENCENTCLOUD_ENDPOINT

        # 实例化一个client选项，可选的，没有特殊需求可以跳过
        clientProfile = ClientProfile()
        clientProfile.httpProfile = httpProfile
        
        # 实例化要请求产品的client对象,clientProfile是可选的
        client = ai3d_client.Ai3dClient(cred, TENCENTCLOUD_REGION, clientProfile)

        # 实例化一个请求对象,每个接口都会对应一个request对象
        req = models.SubmitHunyuanTo3DJobRequest()
        params = {
            "ImageUrl": TEST_IMAGE_URL
        }
        req.from_json_string(json.dumps(params))

        # 返回的resp是一个SubmitHunyuanTo3DJobResponse的实例，与请求对象对应
        resp = client.SubmitHunyuanTo3DJob(req)
        
        # 输出json格式的字符串回包
        print("API Response:")
        print(resp.to_json_string())
        
        return resp

    except TencentCloudSDKException as err:
        print(f"Tencent Cloud SDK Exception: {err}")
        return None
    except Exception as e:
        print(f"General Exception: {e}")
        return None

def test_with_prompt():
    """
    Test function using text prompt instead of image URL
    """
    try:
        # Get credentials from environment variables or config file
        secret_id = os.getenv("TENCENTCLOUD_SECRET_ID") or TENCENTCLOUD_SECRET_ID
        secret_key = os.getenv("TENCENTCLOUD_SECRET_KEY") or TENCENTCLOUD_SECRET_KEY
        
        if not secret_id or not secret_key:
            print("Error: TENCENTCLOUD_SECRET_ID and TENCENTCLOUD_SECRET_KEY must be set as environment variables or in tencent_config.py")
            return None
        
        cred = credential.Credential(secret_id, secret_key)
        
        httpProfile = HttpProfile()
        httpProfile.endpoint = TENCENTCLOUD_ENDPOINT

        clientProfile = ClientProfile()
        clientProfile.httpProfile = httpProfile
        
        client = ai3d_client.Ai3dClient(cred, TENCENTCLOUD_REGION, clientProfile)

        req = models.SubmitHunyuanTo3DJobRequest()
        params = {
            "Prompt": TEST_PROMPT,
            "ResultFormat": "OBJ"
        }
        req.from_json_string(json.dumps(params))

        resp = client.SubmitHunyuanTo3DJob(req)
        
        print("API Response (Text Prompt):")
        print(resp.to_json_string())
        
        return resp

    except TencentCloudSDKException as err:
        print(f"Tencent Cloud SDK Exception: {err}")
        return None
    except Exception as e:
        print(f"General Exception: {e}")
        return None

def check_job_status(job_id):
    """
    Check the status of a submitted job
    """
    try:
        # Get credentials from environment variables or config file
        secret_id = os.getenv("TENCENTCLOUD_SECRET_ID") or TENCENTCLOUD_SECRET_ID
        secret_key = os.getenv("TENCENTCLOUD_SECRET_KEY") or TENCENTCLOUD_SECRET_KEY
        
        if not secret_id or not secret_key:
            print("Error: TENCENTCLOUD_SECRET_ID and TENCENTCLOUD_SECRET_KEY must be set as environment variables or in tencent_config.py")
            return None
        
        cred = credential.Credential(secret_id, secret_key)
        
        httpProfile = HttpProfile()
        httpProfile.endpoint = TENCENTCLOUD_ENDPOINT

        clientProfile = ClientProfile()
        clientProfile.httpProfile = httpProfile
        
        client = ai3d_client.Ai3dClient(cred, TENCENTCLOUD_REGION, clientProfile)

        # Import the query job model
        from tencentcloud.ai3d.v20250513 import models as ai3d_models
        
        req = ai3d_models.QueryHunyuanTo3DJobRequest()
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

if __name__ == "__main__":
    print("Testing Tencent Cloud AI3D API...")
    print("=" * 50)
    
    print("\n1. Testing with Image URL:")
    result1 = test_tencent_ai3d_api()
    
    # If we got a job ID, check its status
    if result1 and hasattr(result1, 'JobId'):
        print(f"\nChecking status for job: {result1.JobId}")
        check_job_status(result1.JobId)
    
    print("\n" + "=" * 50)
    print("\n2. Testing with Text Prompt:")
    result2 = test_with_prompt()
    
    # If we got a job ID, check its status
    if result2 and hasattr(result2, 'JobId'):
        print(f"\nChecking status for job: {result2.JobId}")
        check_job_status(result2.JobId)
    
    print("\n" + "=" * 50)
    print("Test completed!")
